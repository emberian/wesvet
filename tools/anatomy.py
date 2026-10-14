#!/usr/bin/env python3
"""anatomy: what a long transcript is made of, as candidate material for a prune.

Usage:
  anatomy.py <ir.json> [--json]
  anatomy.py <root-session> --agent <id> [--json]

Every byte the model would reload on resume (message text, tool inputs, tool outputs, injected
messages; thinking is counted by its visible text, which Claude Code stores empty) is put in exactly
one bucket, first match wins:

  brief            message 0
  incoming         messages from the coordinator or peers ("... sent a message ...") and human prompts
  notification     harness background-task notifications and other injected reminders
  poll             a poll call (sleep/until/while-do/tail -f/kill -0, Monitor, TaskOutput) and its output
  superseded_read  output of a read whose file is read again later or edited later (the later state wins)
  repeated_cmd     output of a status command (same normalized command) that is run again later
  error_output     output of a call that failed (is_error, or "Exit code N" with N != 0)
  reread           output of a read of a file already read, with no edit to it in between (redundant)
  read_referenced / run_referenced
                   any other read (or run/test/build) output that introduced a token (a sha, a path, an
                   fn- identifier, a run id, a 5+ digit number, an UPPER-CASE-ID) which the agent's own
                   later words or tool inputs use: evidence the output fed a later step
  read_unreferenced / run_unreferenced
                   the same, with no introduced token ever used again: the safest material to prune
  work_call        inputs and outputs of edit/commit/dispatch/setup/spawn/message calls
  other_output     outputs that could not be paired to their call
  assistant_text   the agent's own words
  thinking_signature  thinking blocks (stored as an opaque signature; it is reloaded on resume)
  tool_input       tool-call arguments not counted above

Also counted: decisions (DECISION/READY/RED/BLOCKED messages to "main", and assistant turns that
state a ruling), coordinator corrections (incoming messages with correction language), commits.
Limits: "superseded" and "redundant" are by path/command identity, not by content; a read of a large
file in parts counts each part as a separate read target only when the offsets differ.
"""
import argparse
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import irlib  # noqa: E402

CORRECTION = re.compile(r"\b(correction|wrong|not what I|don't|do not|stop |never |no longer|instead|rule[ds]?\b|must not|right call|you missed|re-?do)", re.I)
DECIDE_TEXT = re.compile(r"\b(DECISION|I decide|I've decided|I rule|ruling:|I'll go with|chose|choosing)\b")


def norm_cmd(cmd):
    """A status command's identity: its leading verb plus the file paths it names.

    `tail -n 20 /x/run.log` and `tail -5 /x/run.log; cat /x/rc` both key on the log, so a later
    look at the same files supersedes an earlier one. A leading `cd DIR &&` is dropped first, so
    `cd /repo; cat a.md` and `cd /repo; cat b.md` stay distinct."""
    c = re.sub(r"\s+", " ", cmd.strip())
    c = re.sub(r"^cd \S+ ?(&&|;) ?", "", c)
    verb = c.split(" ")[0]
    paths = sorted(set(re.findall(r"(?:/|~/)[\w.@+/-]+|\b[\w.-]+(?:/[\w.@+-]+)+|\b[\w-]+\.\w{1,5}\b", c)))
    if not paths:
        c = re.sub(r"\b[0-9a-f]{7,40}\b", "<sha>", c)
        return c[:300]
    return verb + " " + " ".join(paths[:8])


TOKEN = re.compile(r"\b[0-9a-f]{9,40}\b|\bfn-[a-z0-9*$-]{4,}|(?:/|~/)[\w.@+-]+(?:/[\w.@+-]+)+|\brun-\d{8}T\w+|\b[A-Z]{2,}[-_][A-Z0-9-]{3,}\b|\b\d{5,}\b")


def introduced_tokens(text, seen):
    out = set()
    for t in TOKEN.findall(text or ""):
        if t not in seen:
            out.add(t)
    return out


def reference_map(msgs, calls):
    """For each tool call id: (introduced token count, whether any is used later by the agent)."""
    seen = set()
    later_use = []  # (index, text) of the agent's own words and tool inputs
    for i, m in enumerate(msgs):
        if m.get("role") == "assistant":
            parts = [c.get("text", "") for c in m["content"] if c.get("type") == "text"]
            parts += [json.dumps(c.get("input")) for c in m["content"] if c.get("type") == "tool_use"]
            later_use.append((i, "\n".join(parts)))
    out = {}
    order = sorted(calls, key=lambda c: c["result_index"] if c["result_index"] is not None else 10**9)
    ptr_seen_msg = 0
    for c in order:
        ri = c["result_index"]
        if ri is None:
            continue
        while ptr_seen_msg < ri:
            m = msgs[ptr_seen_msg]
            if m.get("role") != "tool":
                seen.update(TOKEN.findall(irlib.text_of(m)))
                for x in m.get("content", []):
                    if x.get("type") == "tool_use":
                        seen.update(TOKEN.findall(json.dumps(x.get("input"))))
            ptr_seen_msg += 1
        intro = introduced_tokens(c["result"], seen)
        seen.update(intro)
        used = False
        if intro:
            for i, t in later_use:
                if i > ri and any(tok in t for tok in intro):
                    used = True
                    break
        out[c["id"]] = (len(intro), used)
    return out


def blen(s):
    return len(s.encode()) if isinstance(s, str) else len(json.dumps(s).encode())


def analyze(ir):
    msgs = ir["messages"]
    calls = irlib.tool_calls(msgs)
    by_result_idx = {}
    for c in calls:
        c["cls"], c["detail"] = irlib.classify(c)
        c["targets"] = [(p, str(r)) for p, r in irlib.read_targets(c)]
        cmd = c["input"].get("command", "") if c["name"] == "Bash" else ""
        c["key"] = norm_cmd(cmd) if cmd else None
        if c["result_index"] is not None:
            by_result_idx.setdefault(c["result_index"], []).append(c)

    # file events in order: reads and edits
    edits_at = collections.defaultdict(list)
    for c in calls:
        if c["cls"] == "edit":
            p = c["input"].get("file_path") or c["detail"]
            edits_at[os.path.basename(str(p))].append(c["index"])
    reads_at = collections.defaultdict(list)
    for c in calls:
        for p, r in c["targets"]:
            reads_at[(p, r)].append(c["index"])
    cmd_at = collections.defaultdict(list)
    for c in calls:
        if c["key"] and c["cls"] in ("read", "poll", "run", "other"):
            cmd_at[c["key"]].append(c["index"])

    refs = reference_map(msgs, calls)

    def result_bucket(c):
        res = c["result"]
        if c["cls"] == "poll":
            return "poll"
        if c["cls"] in irlib.STATE_CLASSES or c["cls"] in ("message", "spawn"):
            return "work_call"
        nintro, used = refs.get(c["id"], (0, False))
        if c["targets"]:
            later_read = any(any(j > c["index"] for j in reads_at[t]) for t in c["targets"])
            later_edit = any(any(j > c["index"] for j in edits_at[os.path.basename(t[0])]) for t in c["targets"])
            if later_read or later_edit:
                return "superseded_read"
            earlier = any(any(j < c["index"] for j in reads_at[t]) for t in c["targets"])
            edited_between = any(
                any(max([j for j in reads_at[t] if j < c["index"]] or [10**9]) < e < c["index"]
                    for e in edits_at[os.path.basename(t[0])]) for t in c["targets"])
            if earlier and not edited_between:
                return "reread"
        if c["is_error"] or re.match(r"Exit code [1-9]", res or ""):
            return "error_output"
        if c["key"] and any(j > c["index"] for j in cmd_at.get(c["key"], [])):
            return "repeated_cmd"
        kind = "read" if (c["targets"] or c["cls"] == "read") else "run"
        if used:
            return kind + "_referenced"
        return kind + "_unreferenced"

    b = collections.Counter()
    turns = collections.Counter()
    for i, m in enumerate(msgs):
        role, kind = m.get("role"), m.get("kind")
        if i == 0:
            b["brief"] += sum(blen(c.get("text", "")) for c in m["content"])
            continue
        if role == "tool":
            for c in m["content"]:
                if c.get("type") != "tool_result":
                    continue
                owner = next((x for x in by_result_idx.get(i, []) if x["id"] == c.get("tool_use_id")), None)
                bucket = result_bucket(owner) if owner else "other_output"
                b[bucket] += blen(irlib.result_text(c))
            continue
        if role == "assistant":
            for c in m["content"]:
                if c.get("type") == "text":
                    b["assistant_text"] += blen(c.get("text", ""))
                elif c.get("type") == "thinking":
                    # Claude Code stores thinking as an opaque signature; its length tracks the hidden text
                    b["thinking_signature"] += blen(c.get("text", "")) + blen(c.get("signature", ""))
                elif c.get("type") == "tool_use":
                    cls, _ = irlib.classify({"name": c.get("name"), "input": c.get("input") or {}, "result": ""})
                    if cls == "poll":
                        b["poll"] += blen(c.get("input"))
                    elif cls in irlib.STATE_CLASSES or cls in ("message", "spawn"):
                        b["work_call"] += blen(c.get("input"))
                    else:
                        b["tool_input"] += blen(c.get("input"))
            continue
        t = irlib.text_of(m)
        if kind == "prompt" or "sent a message" in t[:200]:
            b["incoming"] += blen(t)
            turns["incoming"] += 1
            if CORRECTION.search(t):
                turns["incoming_with_correction_language"] += 1
        else:
            b["notification"] += blen(t)
            turns["notification"] += 1

    for c in calls:
        turns["calls"] += 1
        turns["calls_" + c["cls"]] += 1
        if c["cls"] == "commit":
            turns["commits"] += 1
        if c["name"] == "SendMessage" and str(c["input"].get("to")) == "main":
            head = str(c["input"].get("message", ""))[:40].upper()
            for k in ("DECISION", "READY", "RED", "BLOCKED"):
                if k in head:
                    turns["to_main_" + k] += 1
                    break
            else:
                turns["to_main_other"] += 1
    for m in msgs:
        if m.get("role") == "assistant" and DECIDE_TEXT.search(irlib.text_of(m)):
            turns["assistant_decision_turns"] += 1
    total = sum(b.values())
    reread_files = collections.Counter()
    for (p, _r), idxs in reads_at.items():
        if len(idxs) > 1:
            reread_files[p] += len(idxs) - 1
    usage = list(irlib.usage_rows(msgs))
    return {
        "id": ir.get("id"),
        "messages": len(msgs),
        "bytes_total": total,
        "buckets": dict(b),
        "share": {k: round(v / total, 4) for k, v in b.items()} if total else {},
        "counts": dict(turns),
        "top_reread_files": reread_files.most_common(8),
        "peak_context": max((irlib.ctx_size(u) for _i, _m, u in usage), default=0),
        "api_requests": len(usage),
        "tokens_total": sum(irlib.tok_total(u) for _i, _m, u in usage),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--agent")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = analyze(irlib.load(a.source, a.agent))
    if a.json:
        print(json.dumps(r, indent=1))
        return
    print(f"{r['id']}  {r['messages']} msgs  {r['bytes_total']/1e6:.2f} MB  peak ctx {r['peak_context']/1e3:.0f}k  "
          f"{r['api_requests']} requests  {r['tokens_total']/1e6:.0f}M tokens")
    for k, v in sorted(r["buckets"].items(), key=lambda kv: -kv[1]):
        print(f"  {k:18s} {v/1e3:9.0f} kB  {r['share'][k]*100:5.1f}%")
    print("  counts:", json.dumps(r["counts"]))
    print("  most re-read:", r["top_reread_files"][:5])


if __name__ == "__main__":
    main()
