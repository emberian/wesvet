#!/usr/bin/env python3
"""seat_report: the evaluation plan's daily measurement of a swarm's seat lines.

Usage:
  seat_report.py --root ROOT [--root ROOT ...] [--since 2026-10-14] [--seat-re REGEX]
                 [--common FILE ...] [--cache DIR] [--json OUT]

For the sub-agents of the given coordinator roots (`cv lanes <root> --json`, de-duplicated by agent
id across forked roots) whose description matches --seat-re (default: fn's "fn Builder X<n>"), it
reports per seat line and in total:
  - successions (consecutive seats in a line) and, for each, the successor's orientation
    (tools/orientation_cost.py) and carry recall of brief + what the successor read in its first 40
    calls from the continuation or pack (tools/carry_recall.py, --common files removed);
  - messages addressed to a seat after its final park notice, and those sent while its successor
    was already running (misroutes), from every seat's and root's SendMessage calls;
  - seat lifetimes, peak contexts, tokens.
Read-only: it calls `cv lanes` and `cv show`, and caches IR JSON under --cache (default
./seat-report-cache), never under ~/.claude/projects.
"""
import argparse
import collections
import datetime as dt
import glob
import json
import os
import re
import statistics as st
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import irlib  # noqa: E402
import orientation_cost as oc  # noqa: E402
import carry_recall as cr  # noqa: E402

PARK = re.compile(r"(\bI\b|seat|\b[A-Z]\d+\b)\W{0,3}(am |is |has |have )?(now )?park", re.I)


def lanes(root):
    out = subprocess.run(["cv", "lanes", root, "--json"], capture_output=True, text=True)
    return json.loads(out.stdout or "[]")


def ir_for(root, agent, cache):
    p = os.path.join(cache, agent + ".json")
    if not os.path.exists(p):
        r = subprocess.run(["cv", "show", root, "--agent", agent, "--json"], capture_output=True, text=True)
        if r.returncode != 0:
            return None
        open(p, "w").write(r.stdout)
    return json.load(open(p))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", action="append", required=True)
    ap.add_argument("--since", default="")
    ap.add_argument("--seat-re", default=r"fn (?:Builder )?([A-Z])(\d*)\b[ :(]")
    ap.add_argument("--common", action="append", default=[])
    ap.add_argument("--cache", default="seat-report-cache")
    ap.add_argument("--json")
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    seen = {}
    for root in a.root:
        for l in lanes(root):
            if l["agent_id"] in seen:
                continue
            m = re.match(a.seat_re, l.get("description") or "")
            if m and (l.get("started_at") or "") >= a.since:
                l["root"], l["line"], l["n"] = root, m.group(1), int(m.group(2) or 1)
                seen[l["agent_id"]] = l
    seats = sorted(seen.values(), key=lambda l: (l["line"], l["started_at"]))
    info = {}
    for s in seats:
        ir = ir_for(s["root"], s["agent_id"], a.cache)
        if not ir:
            continue
        msgs = ir["messages"]
        calls = irlib.tool_calls(msgs)
        parks = [c for c in calls if c["name"] == "SendMessage" and str(c["input"].get("to")) == "main"
                 and PARK.search(str(c["input"].get("message", ""))[:300])]
        info[s["agent_id"]] = dict(seat=s, ir=ir, calls=calls,
                                   start=irlib.ts(msgs[0]["timestamp"]), end=irlib.ts(msgs[-1]["timestamp"]),
                                   park=irlib.ts(parks[-1]["ts"]) if parks else irlib.ts(msgs[-1]["timestamp"]))
    by_line = collections.defaultdict(list)
    for aid, i in info.items():
        by_line[i["seat"]["line"]].append(i)
    rows = []
    for line, v in sorted(by_line.items()):
        v.sort(key=lambda i: i["start"])
        for k in range(1, len(v)):
            pred, succ = v[k - 1], v[k]
            o = oc.measure(succ["ir"], 0)
            reads = [c for c in succ["calls"][:40] if c["name"] in ("Bash", "Read") and
                     re.search(r"continuation|distill|lanedumps|tool-results/", json.dumps(c["input"]))]
            given = irlib.text_of(succ["ir"]["messages"][0]) + "\n" + "\n".join(c["result"] for c in reads)
            gp = os.path.join(a.cache, succ["seat"]["agent_id"] + ".given.txt")
            open(gp, "w").write(given)
            rec = cr.run(pred["ir"]["messages"], succ["ir"]["messages"], [("given", gp)], a.common)
            fw = o["first_work"]
            rows.append(dict(line=line, pred=pred["seat"]["agent_id"], succ=succ["seat"]["agent_id"],
                             succ_desc=succ["seat"]["description"], start=succ["seat"]["started_at"],
                             first_work_min=round(fw["seconds"] / 60, 2) if fw else None,
                             first_work_tokens=fw["tokens"] if fw else None,
                             first_work_context=fw["context"] if fw else None,
                             needed=rec["needed"], carry_recall=rec["packs"][0]["recall"],
                             carry_recall_weighted=rec["packs"][0]["recall_weighted"]))
    # misroutes
    sends, seen_ids = [], set()
    for i in info.values():
        for c in i["calls"]:
            if c["name"] == "SendMessage":
                sends.append(c)
    for root in a.root:
        for f in glob.glob(os.path.expanduser(f"~/.claude/projects/*/{root}*.jsonl")):
            if ".flat." in f:
                continue
            for ln in open(f):
                try:
                    r = json.loads(ln)
                except Exception:
                    continue
                if r.get("type") != "assistant":
                    continue
                for b in r.get("message", {}).get("content", []) or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "SendMessage":
                        sends.append(dict(ts=r["timestamp"], input=b.get("input", {}), id=b.get("id")))
    to_seat = after_park = misroute = 0
    for c in sends:
        if c.get("id") in seen_ids:
            continue
        seen_ids.add(c.get("id"))
        to = str(c["input"].get("to", ""))
        tgt = next((i for aid, i in info.items() if len(to) >= 8 and aid.startswith(to[:17])), None)
        if not tgt:
            continue
        to_seat += 1
        t = irlib.ts(c["ts"])
        if t > tgt["park"] + dt.timedelta(seconds=60):
            after_park += 1
            line = tgt["seat"]["line"]
            if any(j["seat"]["line"] == line and tgt["start"] < j["start"] <= t for j in info.values()):
                misroute += 1

    def med(key):
        v = [r[key] for r in rows if r[key] is not None]
        return round(st.median(v), 3) if v else None
    life = [(i["end"] - i["start"]).total_seconds() / 3600 for i in info.values()]
    summary = dict(seats=len(info), successions=len(rows),
                   successions_by_line=dict(collections.Counter(r["line"] for r in rows)),
                   median_first_work_min=med("first_work_min"), median_first_work_tokens=med("first_work_tokens"),
                   median_first_work_context=med("first_work_context"),
                   median_carry_recall=med("carry_recall"), median_carry_recall_weighted=med("carry_recall_weighted"),
                   seat_addressed_messages=to_seat, after_park=after_park, misroutes=misroute,
                   misroutes_per_100=round(100 * misroute / to_seat, 2) if to_seat else None,
                   median_seat_hours=round(st.median(life), 2) if life else None)
    print(json.dumps(summary, indent=1))
    if a.json:
        json.dump(dict(summary=summary, successions=rows), open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
