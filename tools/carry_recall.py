#!/usr/bin/env python3
"""carry_recall: how much of what an agent needed next does a handoff pack carry?

Two modes.

Succession (predecessor -> successor):
  carry_recall.py --pred <ir.json> --succ <ir.json> [--pack NAME=FILE ...] [--json]
  "needed" = the distinctive tokens (shas, absolute paths, fn- identifiers, run ids, UPPER-CASE-IDS,
  5+ digit numbers) that the SUCCESSOR wrote in its own words or tool inputs AND that occur anywhere in
  the PREDECESSOR's transcript: facts that existed in the veteran's context and were used next.

Self-cut (a veteran against its own future):
  carry_recall.py --self <ir.json> --cut N [--pack NAME=FILE ...] [--json]
  "needed" = tokens the agent wrote after message N that occur in messages before N.

For each pack (a text file: a continuation file, a `cv distill` pack, a sharpened .jsonl, a brief) it
reports recall = |needed found in pack| / |needed| and the pack's size, and lists the needed tokens
the pack misses, most-used first. The full predecessor transcript is the upper bound (recall 1.0).

--common FILE removes tokens that a standing document already gives every seat (the worktree root, the
coordination file's paths), so "needed" is what only the predecessor's context held.

Limits: a token-level proxy. It credits a pack for carrying a sha or a path, not for carrying the
reason the sha matters; it cannot see knowledge the agent used without writing a distinctive token;
and it counts a token the successor re-read from disk as needed even if re-reading it was cheap.
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import irlib  # noqa: E402
import anatomy  # noqa: E402

TOKEN = anatomy.TOKEN
NOISE = ("/Users/ember/.claude", "/private/tmp/claude-501", "/dev/null", "/usr/", "/bin/", "/tmp/")


def toks(text):
    return {t for t in TOKEN.findall(text or "") if not t.startswith(NOISE)}


def all_text(msgs):
    parts = []
    for m in msgs:
        for c in m.get("content", []):
            if c.get("type") == "text":
                parts.append(c.get("text", ""))
            elif c.get("type") == "tool_use":
                parts.append(json.dumps(c.get("input")))
            elif c.get("type") == "tool_result":
                parts.append(irlib.result_text(c))
    return "\n".join(parts)


def own_use(msgs):
    """Counter of tokens in the agent's own text and tool inputs."""
    cnt = collections.Counter()
    for m in msgs:
        if m.get("role") != "assistant":
            continue
        for c in m.get("content", []):
            if c.get("type") == "text":
                cnt.update(toks(c.get("text", "")))
            elif c.get("type") == "tool_use":
                cnt.update(toks(json.dumps(c.get("input"))))
    return cnt


def pack_text(path):
    if path.endswith(".jsonl"):
        parts = []
        for line in open(path):
            r = json.loads(line)
            if r.get("type") in ("user", "assistant"):
                cont = r["message"].get("content")
                if isinstance(cont, str):
                    parts.append(cont)
                    continue
                for c in cont or []:
                    if c.get("type") == "text":
                        parts.append(c.get("text", ""))
                    elif c.get("type") == "tool_use":
                        parts.append(json.dumps(c.get("input")))
                    elif c.get("type") == "tool_result":
                        parts.append(irlib.result_text(c))
            elif r.get("type") == "attachment":
                parts.append(json.dumps(r.get("attachment")))
        return "\n".join(parts)
    return open(path).read()


def run(pred_msgs, succ_msgs, packs, common=()):
    pred_tok = toks(all_text(pred_msgs))
    standing = set()
    for path in common:
        standing |= toks(pack_text(path))
    use = own_use(succ_msgs)
    needed = {t: n for t, n in use.items() if t in pred_tok and t not in standing}
    total_use = len(use)
    rows = []
    for name, path in packs:
        txt = pack_text(path)
        have = toks(txt)
        found = [t for t in needed if t in have]
        missing = sorted((t for t in needed if t not in have), key=lambda t: -needed[t])
        rows.append({
            "pack": name, "path": path, "bytes": len(txt.encode()),
            "recall": round(len(found) / len(needed), 3) if needed else None,
            "recall_weighted": round(sum(needed[t] for t in found) / sum(needed.values()), 3) if needed else None,
            "missing_top": [(t, needed[t]) for t in missing[:25]],
        })
    return {"successor_distinct_tokens": total_use, "needed": len(needed),
            "needed_share_of_successor_tokens": round(len(needed) / total_use, 3) if total_use else None,
            "packs": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred")
    ap.add_argument("--succ")
    ap.add_argument("--self")
    ap.add_argument("--cut", type=int)
    ap.add_argument("--pack", action="append", default=[], help="NAME=FILE")
    ap.add_argument("--common", action="append", default=[],
                    help="a standing document every seat reads (SEAT-COMMON, COORDINATION.md): its tokens are not counted as needed")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    packs = [tuple(p.split("=", 1)) for p in a.pack]
    if a.self:
        m = json.load(open(a.self))["messages"]
        pred, succ = m[:a.cut], m[a.cut:]
    else:
        pred = json.load(open(a.pred))["messages"]
        succ = json.load(open(a.succ))["messages"]
    r = run(pred, succ, packs, a.common)
    if a.json:
        print(json.dumps(r, indent=1))
        return
    print(f"needed tokens: {r['needed']} of {r['successor_distinct_tokens']} distinct tokens the successor wrote "
          f"({(r['needed_share_of_successor_tokens'] or 0)*100:.0f}%)")
    for p in r["packs"]:
        print(f"  {p['pack']:28s} {p['bytes']/1e3:8.1f} kB  recall {p['recall']}  weighted {p['recall_weighted']}")
        print("     misses:", ", ".join(f"{t}({n})" for t, n in p["missing_top"][:10]))


if __name__ == "__main__":
    main()
