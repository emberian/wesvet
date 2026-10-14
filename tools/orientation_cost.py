#!/usr/bin/env python3
"""orientation_cost: what a seat paid before it first changed state.

Usage:
  orientation_cost.py <ir.json>                      # a saved `cv show ... --json`
  orientation_cost.py <root-session> --agent <id>    # read through cv (read-only)
  orientation_cost.py ... --from-index N             # measure from message N (a SendMessage resume)
  orientation_cost.py ... --json

Measured from the start point (message 0, or --from-index) to the first tool call of each class:
  edit      Edit/Write/NotebookEdit outside /tmp and scratchpads, or a Bash redirect/tee/sed -i into a real path
  commit    a git command that changes refs or history (commit, push, merge, rebase, cherry-pick, branch, tag, worktree add)
  dispatch  starting work elsewhere: `codex exec`, nohup/setsid jobs, `train.py certify|push|regen|...`, swarm-build
  message   SendMessage (reported, but not counted as a state change: the first one is often an ack)
  spawn     Agent/Task
  setup     workspace/branch moves: git merge, rebase, worktree add, checkout -b, branch <new>, reset --hard
first_state_change = the earliest of setup, edit, commit, dispatch, spawn.
first_work = the earliest of edit, commit, dispatch, spawn (new work, not preparation).
Redirects into *.log/*.pid/*.out/rc/status files are run bookkeeping, not edits.

For each: wall-clock seconds, API tokens summed per request (input + cache read + cache write + output),
the context size of the turn that made it, the tool calls and the bytes of tool output read before it.
Limits: classification is by regex over the command. An inline `python3 - <<EOF` program that opens a file
for writing counts as an edit; other generated writes (a script file run by path, `make`) count as `run`.
"""
import argparse
import json
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
import irlib  # noqa: E402

CLASSES = ("setup", "edit", "commit", "dispatch", "spawn", "message")


def measure(ir, start=0):
    msgs = ir["messages"]
    t0 = irlib.ts(msgs[start]["timestamp"]) if start < len(msgs) else None
    usage = [(i, u) for i, _m, u in irlib.usage_rows(msgs) if i >= start]
    calls = [c for c in irlib.tool_calls(msgs) if c["index"] >= start]

    def tokens_upto(idx):
        tot = sum(irlib.tok_total(u) for i, u in usage if i <= idx)
        ctx = 0
        for i, u in usage:
            if i <= idx:
                ctx = irlib.ctx_size(u)
        return tot, ctx

    first = {}
    nread = 0
    bytes_read = 0
    for c in calls:
        cls, detail = irlib.classify(c)
        key = cls if cls in CLASSES else None
        if key and key not in first:
            tot, ctx = tokens_upto(c["index"])
            first[key] = {
                "index": c["index"],
                "ts": c["ts"],
                "seconds": round((irlib.ts(c["ts"]) - t0).total_seconds(), 1),
                "tokens": tot,
                "context": ctx,
                "calls_before": nread,
                "bytes_read_before": bytes_read,
                "detail": detail,
            }
        nread += 1
        bytes_read += len(c["result"].encode())
    def earliest(keys):
        got = [(first[k]["index"], k) for k in keys if k in first]
        if not got:
            return None
        _i, k = min(got)
        return dict(first[k], cls=k)
    fsc = earliest(irlib.STATE_CLASSES)
    fwork = earliest(irlib.WORK_CLASSES)
    total_tok = sum(irlib.tok_total(u) for _i, u in usage)
    peak = max((irlib.ctx_size(u) for _i, u in usage), default=0)
    end = irlib.ts(msgs[-1]["timestamp"])
    return {
        "id": ir.get("id"),
        "start_index": start,
        "start_ts": msgs[start]["timestamp"] if start < len(msgs) else None,
        "messages": len(msgs) - start,
        "tool_calls": len(calls),
        "duration_s": round((end - t0).total_seconds(), 1) if t0 else None,
        "total_tokens": total_tok,
        "peak_context": peak,
        "first": first,
        "first_state_change": fsc,
        "first_work": fwork,
        "orientation_share_tokens": round(fwork["tokens"] / total_tok, 4) if fwork and total_tok else None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--agent")
    ap.add_argument("--from-index", type=int, default=0)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    ir = irlib.load(a.source, a.agent)
    r = measure(ir, a.from_index)
    if a.json:
        print(json.dumps(r, indent=1))
        return
    print(f"{r['id']}  from msg {r['start_index']}  {r['messages']} msgs  {r['tool_calls']} calls  "
          f"{r['total_tokens']/1e6:.1f}M tokens  peak ctx {r['peak_context']/1e3:.0f}k")
    for label, f in (("first state change", r["first_state_change"]), ("first work", r["first_work"])):
        if not f:
            print(f"{label}: none")
            continue
        print(f"{label}: {f['cls']} at #{f['index']} after {f['seconds']/60:.1f} min, "
              f"{f['tokens']/1e6:.2f}M tokens, ctx {f['context']/1e3:.0f}k, {f['calls_before']} calls, "
              f"{f['bytes_read_before']/1e3:.0f} kB read  [{f['detail']}]")
    for k in CLASSES:
        d = r["first"].get(k)
        if d:
            print(f"  {k:9s} #{d['index']:<5d} {d['seconds']/60:7.1f} min {d['tokens']/1e6:6.2f}M  {d['detail'][:70]}")


if __name__ == "__main__":
    main()
