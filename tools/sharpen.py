#!/usr/bin/env python3
"""sharpen: a prune profile that turns a long Claude transcript into a "sharpened veteran".

Usage:
  sharpen.py <root-session> --agent <agent-id> --out DIR [--keep-last 25] [--cut N]
  sharpen.py <ir.json> --out DIR ...

It reads the transcript through `cv show --json` (for the analysis) and the raw JSONL that the IR's
`source_path` names (for the rewrite), and writes only under --out:
  <agent>.sharpened.jsonl   a Claude-format transcript with the same records, rewritten (below)
  <agent>.sharpen.json      the report: what was kept and dropped, by bucket, with byte counts
It never writes under ~/.claude/projects. To resume the result you would copy it into the parent
session's subagents/ directory (or `claude --resume` a top-level copy); this script does not.

--cut N sharpens the transcript as it stood at IR message N (records after it are not written), so a
prune can be scored against what the agent actually did next.

KEPT VERBATIM (whole transcript):
  - the brief (first user record) and every message the agent received: coordinator and peer
    messages (queued_command attachments, "... sent a message ..." user records), human prompts
  - every text block the agent wrote (its decisions, reports, rulings it relayed, self-rules)
  - every tool call's input, except old Write/Edit bodies (see below)
  - the output of every state-changing call (edit, commit, push, merge, dispatch, spawn, SendMessage)
  - the output of a failed call (error text, head 1.5 kB + tail 1.5 kB): failures are lessons
  - the output of a read or run whose introduced tokens (shas, paths, fn- names, run ids, IDs) the
    agent used later, capped at head 3 kB + tail 3 kB
  - everything in the last --keep-last tool calls, thinking included
  - setup attachments (instructions, session context, environment, skills, tools)
DROPPED OR REPLACED (outside the tail):
  - thinking blocks (an assistant record left empty is removed and its child re-linked)
  - poll calls' outputs (sleep/until loops, Monitor, TaskOutput): replaced by a one-line marker
  - background-task notifications ("[SYSTEM NOTIFICATION ...]" user records), hook_success and
    total_tokens_reminder attachments: removed, children re-linked
  - outputs of a status command run again later (same verb and paths): all but the last occurrence
  - outputs of reads/runs never used later: replaced by a marker naming the byte count and the
    `cv cat` call that fetches the original. Profile 2 (the default) treats reads of documents and
    source files (.md .lisp .lsp .lean .rs .py .json .txt, READY/BRIEF/STATEMENTS) apart: never a
    "repeat" (a second range of the same book is new text), head+tail 8 kB if used later, 4 kB if
    not, because "never used later" is only known up to the cut and reference reads are used late
  - Write/Edit bodies of a file that is written again later: head 1 kB + marker (the last write stays)
Every replaced output carries `[sharpened: ... cv cat <session> <tool_use_id>]`, so nothing is lost
from the source; the source transcript is never modified.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import irlib  # noqa: E402
import anatomy  # noqa: E402

DROP_ATTACH = {"hook_success", "total_tokens_reminder"}
NOT_LOADED = {"hook_success"}  # recorded by the harness, not rendered into the model's context


def loaded_bytes(rec):
    """Bytes of a record that the model reloads: message content, or a rendered attachment."""
    t = rec.get("type")
    if t in ("user", "assistant"):
        content = rec.get("message", {}).get("content")
        if isinstance(content, list):
            n = 0
            for c in content:
                if c.get("type") == "thinking":
                    n += len(c.get("thinking", "")) + len(c.get("signature", ""))
                elif c.get("type") == "text":
                    n += len(c.get("text", "").encode())
                elif c.get("type") == "tool_use":
                    n += len(json.dumps(c.get("input")).encode())
                elif c.get("type") == "tool_result":
                    n += len(irlib.result_text(c).encode())
            return n
        return len(str(content).encode())
    if t == "attachment" and rec.get("attachment", {}).get("type") not in NOT_LOADED:
        return len(json.dumps(rec.get("attachment")).encode())
    return 0


def headtail(s, n):
    b = s.encode()
    if len(b) <= 2 * n:
        return s
    return b[:n].decode(errors="ignore") + f"\n[sharpened: {len(b) - 2*n} bytes elided from the middle]\n" + b[-n:].decode(errors="ignore")


DOC = re.compile(r"\.(md|lisp|lsp|lean|rs|py|txt|json|toml|ts|js|mjs|tsx|lsp)\b|STATEMENTS|README|BRIEF|READY", re.I)
LOGISH = re.compile(r"\.(log|out|err|pid|rc|status)\b|/tasks/|tool-results/")


def is_doc_read(c):
    """A read whose target is a document or source file, not a log or a status file."""
    paths = [p for p, _r in c["targets"]]
    if not paths and c["name"] == "Bash":
        paths = re.findall(r"(?:/|~/)[\w.@+/-]+|\b[\w/-]+\.(?:md|lisp|lsp|py|lean|rs)\b", c["input"].get("command", ""))
    if c["name"] == "Read":
        paths = [c["input"].get("file_path", "")]
    return any(DOC.search(p) and not LOGISH.search(p) for p in paths)


def plan(ir, keep_last, cut, profile=2):
    msgs = ir["messages"][:cut] if cut else ir["messages"]
    calls = [c for c in irlib.tool_calls(msgs)]
    for c in calls:
        c["cls"], c["detail"] = irlib.classify(c)
        c["targets"] = irlib.read_targets(c)
        cmd = c["input"].get("command", "") if c["name"] == "Bash" else ""
        c["key"] = anatomy.norm_cmd(cmd) if cmd else None
    refs = anatomy.reference_map(msgs, calls)
    tail_ids = {c["id"] for c in calls[-keep_last:]}
    tail_start_ts = calls[-keep_last]["ts"] if len(calls) >= keep_last else msgs[0]["timestamp"]
    last_key_idx = {}
    for c in calls:
        if c["key"]:
            last_key_idx[c["key"]] = c["index"]
    last_write = {}
    for c in calls:
        if c["name"] in ("Write", "Edit"):
            last_write[c["input"].get("file_path")] = c["id"]
    decide = {}
    for c in calls:
        if c["id"] in tail_ids:
            decide[c["id"]] = ("keep", "tail")
            continue
        nintro, used = refs.get(c["id"], (0, False))
        res = c["result"] or ""
        if c["cls"] == "poll":
            decide[c["id"]] = ("marker", "poll")
        elif c["cls"] in irlib.STATE_CLASSES or c["cls"] in ("message", "spawn"):
            decide[c["id"]] = ("keep", "work")
        elif c["is_error"] or re.match(r"Exit code [1-9]", res):
            decide[c["id"]] = ("headtail1500", "error")
        elif profile >= 2 and is_doc_read(c):
            # v2: a read of a document or source file is reference material the agent may use much
            # later (the self-cut test on P7: 3 of v1's top misses were READY/book/survey reads, cut
            # either as a "repeat" of a different range of the same book or in a head+tail middle)
            decide[c["id"]] = ("headtail8000", "doc_read_referenced") if used else ("headtail4000", "doc_read")
        elif c["key"] and last_key_idx.get(c["key"], -1) > c["index"] and c["cls"] in ("read", "run", "other"):
            decide[c["id"]] = ("marker", "repeated_status")
        elif used:
            decide[c["id"]] = ("headtail3000", "referenced")
        elif len(res.encode()) <= 400:
            decide[c["id"]] = ("keep", "small")
        else:
            decide[c["id"]] = ("marker", "unreferenced")
        if c["name"] in ("Write", "Edit") and last_write.get(c["input"].get("file_path")) != c["id"] and c["id"] not in tail_ids:
            decide[c["id"]] = decide[c["id"]] + ("old_write_body",)
    return msgs, calls, decide, tail_start_ts


def check(lines):
    """Structural checks a resume needs: parent links resolve, every tool_use has its result."""
    recs = [json.loads(l) for l in lines]
    uuids = {r.get("uuid") for r in recs if r.get("uuid")}
    uses, results = set(), set()
    for r in recs:
        c = r.get("message", {}).get("content") if r.get("type") in ("user", "assistant") else None
        if isinstance(c, list):
            for b in c:
                if b.get("type") == "tool_use":
                    uses.add(b.get("id"))
                elif b.get("type") == "tool_result":
                    results.add(b.get("tool_use_id"))
    return {
        "dangling_parent": sum(1 for r in recs if r.get("parentUuid") and r["parentUuid"] not in uuids),
        "tool_use_without_result": len(uses - results),
        "result_without_use": len(results - uses),
        "empty_assistant": sum(1 for r in recs if r.get("type") == "assistant" and not r["message"].get("content")),
    }


def sharpen(ir, out_dir, keep_last=25, cut=None, profile=2):
    msgs, calls, decide, tail_ts = plan(ir, keep_last, cut, profile)
    src = ir["source_path"]
    sess = "agent-" + ir["id"].split("agent-")[-1] if "agent-" in (ir.get("id") or "") else ir.get("id")
    last_ts = msgs[-1]["timestamp"]
    records = [json.loads(l) for l in open(src)]
    out, relink = [], {}
    stats = {"records_in": 0, "records_out": 0, "bytes_in": 0, "bytes_out": 0, "by_reason": {}}

    def bump(reason, before, after):
        r = stats["by_reason"].setdefault(reason, {"n": 0, "bytes_before": 0, "bytes_after": 0})
        r["n"] += 1
        r["bytes_before"] += before
        r["bytes_after"] += after

    for rec in records:
        ts = rec.get("timestamp")
        if ts and ts > last_ts:
            break
        stats["records_in"] += 1
        raw = json.dumps(rec)
        stats["bytes_in"] += len(raw)
        stats["loaded_in"] = stats.get("loaded_in", 0) + loaded_bytes(rec)
        in_tail = bool(ts and ts >= tail_ts)
        par = rec.get("parentUuid")
        while par in relink:
            par = relink[par]
        rec["parentUuid"] = par
        uid = rec.get("uuid")
        t = rec.get("type")
        drop = False
        if t == "attachment" and not in_tail and rec.get("attachment", {}).get("type") in DROP_ATTACH:
            drop, reason = True, "attachment:" + rec["attachment"]["type"]
        elif t == "user" and not in_tail and isinstance(rec["message"].get("content"), str) \
                and rec["message"]["content"].startswith("[SYSTEM NOTIFICATION"):
            drop, reason = True, "notification"
        elif t == "assistant" and not in_tail:
            content = rec["message"].get("content", [])
            kept = [c for c in content if c.get("type") != "thinking"]
            if len(kept) != len(content):
                before = len(json.dumps(content))
                rec["message"]["content"] = kept
                bump("thinking", before, len(json.dumps(kept)))
                if not kept:
                    drop, reason = True, "thinking_only_record"
            for c in rec["message"].get("content", []):
                if c.get("type") == "tool_use":
                    d = decide.get(c.get("id"), ("keep", "?"))
                    if "old_write_body" in d:
                        inp = c.get("input", {})
                        for k in ("content", "new_string", "old_string"):
                            if isinstance(inp.get(k), str) and len(inp[k]) > 1200:
                                before = len(inp[k])
                                inp[k] = inp[k][:1000] + f"\n[sharpened: older write of this file, {before} chars; the last write is kept; cv cat {sess} {c.get('id')} --input]"
                                bump("old_write_body", before, len(inp[k]))
        elif t == "user" and isinstance(rec["message"].get("content"), list):
            for c in rec["message"]["content"]:
                if c.get("type") != "tool_result":
                    continue
                d = decide.get(c.get("tool_use_id"), ("keep", "?"))
                text = irlib.result_text(c)
                before = len(text.encode())
                if d[0] == "marker":
                    new = f"[sharpened: {d[1]} output, {before} bytes; cv cat {sess} {c.get('tool_use_id')}]"
                    if d[1] == "poll":
                        lastline = text.strip().splitlines()[-1][:200] if text.strip() else ""
                        new += f" last line: {lastline}"
                elif d[0] == "headtail1500":
                    new = headtail(text, 1500)
                elif d[0] == "headtail3000":
                    new = headtail(text, 3000)
                elif d[0] == "headtail4000":
                    new = headtail(text, 4000)
                elif d[0] == "headtail8000":
                    new = headtail(text, 8000)
                else:
                    new = None
                if new is not None and len(new.encode()) < before:
                    c["content"] = new
                    bump(d[1], before, len(new.encode()))
                else:
                    bump("kept:" + d[1], before, before)
        if drop:
            relink[uid] = par
            bump(reason, len(raw), 0)
            continue
        line = json.dumps(rec)
        stats["bytes_out"] += len(line)
        stats["loaded_out"] = stats.get("loaded_out", 0) + loaded_bytes(rec)
        stats["records_out"] += 1
        out.append(line)
    # revive: Claude Code's resume gate reads the last turn's recorded usage as the current size, so
    # rewrite it to the estimate (the same correction `cv prune` applies by default)
    overhead = 31000
    usage_all = list(irlib.usage_rows(msgs))
    peak = irlib.ctx_size(usage_all[-1][2]) if usage_all else 0
    est = int(overhead + max(peak - overhead, 0) * stats.get("loaded_out", 0) / max(stats.get("loaded_in", 1), 1))
    for k in range(len(out) - 1, -1, -1):
        r = json.loads(out[k])
        u = r.get("message", {}).get("usage") if r.get("type") == "assistant" else None
        if u:
            u["cache_read_input_tokens"] = max(est - u.get("input_tokens", 0) - u.get("cache_creation_input_tokens", 0), 0)
            out[k] = json.dumps(r)
            stats["revived_usage"] = est
            break
    stats["check"] = check(out)
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, (ir.get("id") or "session").replace("agent-", "") + (f".cut{cut}" if cut else "") + f".v{profile}")
    with open(base + ".sharpened.jsonl", "w") as fh:
        fh.write("\n".join(out) + "\n")
    stats["source"] = src
    stats["cut"] = cut
    stats["keep_last"] = keep_last
    stats["profile"] = profile
    stats["recorded_context_at_end"] = peak
    stats["est_context_after"] = est  # fixed overhead (31k, cv doctor's figure for these seats) + scaled conversation
    stats["note"] = ("est_context_after = fixed overhead (31k) + the recorded conversational context scaled by "
                     "the ratio of loaded bytes (message content, thinking signatures, rendered attachments) "
                     "after/before; an estimate, not a measured resume")
    with open(base + ".sharpen.json", "w") as fh:
        json.dump(stats, fh, indent=1)
    return base, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--agent")
    ap.add_argument("--out", required=True)
    ap.add_argument("--keep-last", type=int, default=25)
    ap.add_argument("--cut", type=int)
    ap.add_argument("--profile", type=int, default=2, help="1: drop every unreferenced output; 2 (default): document/source reads are never a 'repeat' and keep head+tail 8 kB if used later, 4 kB if not")
    a = ap.parse_args()
    if os.path.realpath(a.out).startswith(os.path.realpath(os.path.expanduser("~/.claude/projects"))):
        sys.exit("refusing to write under ~/.claude/projects")
    ir = irlib.load(a.source, a.agent)
    base, st = sharpen(ir, a.out, a.keep_last, a.cut, a.profile)
    print(f"{base}.sharpened.jsonl: {st['records_in']} -> {st['records_out']} records, "
          f"{st['bytes_in']/1e6:.2f} -> {st['bytes_out']/1e6:.2f} MB on disk, loaded {st['loaded_in']/1e6:.2f} -> {st['loaded_out']/1e6:.2f} MB; recorded context {st['recorded_context_at_end']/1e3:.0f}k "
          f"-> est {st['est_context_after']/1e3:.0f}k")
    for k, v in sorted(st["by_reason"].items(), key=lambda kv: -(kv[1]["bytes_before"] - kv[1]["bytes_after"])):
        print(f"  {k:32s} n={v['n']:4d}  {v['bytes_before']/1e3:8.0f} kB -> {v['bytes_after']/1e3:8.0f} kB")
    print("  check:", json.dumps(st["check"]))


if __name__ == "__main__":
    main()
