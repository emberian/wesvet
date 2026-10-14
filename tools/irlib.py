"""Shared reader for cv's unified IR (`cv show <id> --json`, `cv show <root> --agent <a> --json`).

Read-only: it calls `cv show` and parses its stdout; it never writes a session file.
"""
import datetime as dt
import json
import re
import subprocess

SCRATCH = re.compile(r"^(/private)?/tmp/|/scratchpad/|^/dev/null$")


def load(source, agent=None):
    """source: a path to a saved IR JSON file, or a cv session id (with agent= for a sub-agent)."""
    if source.endswith(".json"):
        with open(source) as fh:
            return json.load(fh)
    cmd = ["cv", "show", source, "--json"]
    if agent:
        cmd = ["cv", "show", source, "--agent", agent, "--json"]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def text_of(msg):
    return "\n".join(c.get("text", "") for c in msg.get("content", []) if c.get("type") == "text")


def result_text(block):
    c = block.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(x.get("text", "") for x in c if isinstance(x, dict))
    return ""


def usage_rows(msgs):
    """Yield (index, msg, usage) once per API request (IR splits one response into several messages)."""
    seen = set()
    for i, m in enumerate(msgs):
        if m.get("role") != "assistant" or not m.get("usage"):
            continue
        ex = m.get("extra", {}).get("claude", {})
        key = ex.get("requestId") or ex.get("message.id") or m.get("id")
        if key in seen:
            continue
        seen.add(key)
        yield i, m, m["usage"]


def tok_total(u):
    return (u.get("input_tokens", 0) + u.get("cache_read_tokens", 0)
            + u.get("cache_creation_tokens", 0) + u.get("output_tokens", 0))


def ctx_size(u):
    return u.get("input_tokens", 0) + u.get("cache_read_tokens", 0) + u.get("cache_creation_tokens", 0)


def tool_calls(msgs):
    """List of dicts: index, ts, name, input, result (text), is_error, result_index."""
    calls, by_id = [], {}
    for i, m in enumerate(msgs):
        for c in m.get("content", []):
            if c.get("type") == "tool_use":
                d = {"index": i, "ts": m.get("timestamp"), "name": c.get("name"),
                     "input": c.get("input") or {}, "id": c.get("id"), "result": "",
                     "is_error": False, "result_index": None}
                calls.append(d)
                by_id[c.get("id")] = d
            elif c.get("type") == "tool_result":
                d = by_id.get(c.get("tool_use_id"))
                if d is not None:
                    d["result"] = result_text(c)
                    d["is_error"] = bool(c.get("is_error"))
                    d["result_index"] = i
    return calls


# ---- classification of a tool call -------------------------------------------------------

GIT_PRE = r"\bgit\b(?:\s+-C\s+\S+)?(?:\s+-c\s+\S+)*\s+"
# history-changing commands that record new work
GIT_WORK = re.compile(GIT_PRE + r"(commit|push|cherry-pick|am|revert|tag)(?![-\w])")
# workspace/branch moves: state changes, but preparation rather than new work
GIT_SETUP = re.compile(GIT_PRE + r"(merge|rebase|worktree\s+(add|remove)|checkout\s+-[bB]|switch\s+-c|"
                       r"branch\s+(-f|-D|-d|-m|[A-Za-z][\w/.-]*\s*$)|reset\s+--hard)(?![-\w])")
DISPATCH = re.compile(r"\bcodex\s+(exec|e)\b|\bnohup\b|train\.py\s+(certify|push|regen|merge|submit|image)|"
                      r"\bswarm-build\b|\bsetsid\b|&\s*echo\s+\$!|\bscreen\s+-dm|\btmux\s+new")
# an inline python program that writes a file (open(..., 'w'/'a'), .write_text, ...)
PY_WRITE = re.compile(r"python3?\s+-\s*(?:\S+\s+)*<<.*?(open\([^)]*['\"][wa]['\"]|\.write_text\(|\.write\()", re.S)
POLL = re.compile(r"\bsleep\s+\d|\buntil\b.*\bdo\b|\bwhile\b.*\bdo\b|tail\s+-f|kill\s+-0")
WRITE_REDIRECT = re.compile(r"(?:^|[^0-9&>])>>?\s*([^\s|&;]+)|\btee\s+(?:-a\s+)?([^\s|&;]+)|\bsed\s+-i\S*\s.*?(\S+)\s*$")
READISH = re.compile(r"^\s*(cat|sed\s+-n|head|tail|grep|rg|wc|ls|find|git\s+(-C\s+\S+\s+)?(log|show|diff|status|branch|rev-parse|ls-files|cat-file|blame)|jq|awk|cv\s+(show|ls|lanes|search|events|cat))\b")


PATHLIKE = re.compile(r"^[~/$.\w][\w~/$.{}@+-]*$")
RUNLOG = re.compile(r"\.(log|pid|out|err|rc|status)$|/(rc|status|exit)$")


def written_paths(cmd):
    """Files a shell command writes (redirect, tee, sed -i), skipping /dev/*, fd dups and non-paths."""
    out = []
    for m in WRITE_REDIRECT.finditer(cmd):
        p = next((g for g in m.groups() if g), None)
        if not p:
            continue
        p = p.strip("'\"")
        if p.startswith(("&", "/dev/")) or not PATHLIKE.match(p) or p.isdigit() or p.startswith("$?"):
            continue
        if not ("/" in p or "." in p):
            continue
        out.append(p)
    return out


def classify(call):
    """One of: edit, commit, dispatch, message, spawn, poll, read, run, other. Plus a detail string."""
    n, inp = call["name"], call["input"]
    if n in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
        p = inp.get("file_path", "")
        return ("scratch_write" if SCRATCH.search(p) else "edit"), p
    if n == "SendMessage":
        return "message", str(inp.get("to", "")) + ": " + str(inp.get("summary") or inp.get("message", ""))[:100]
    if n in ("Agent", "Task"):
        return "spawn", str(inp.get("description", ""))[:100]
    if n in ("Monitor", "TaskOutput", "BashOutput"):
        return "poll", n
    if n in ("Read", "Grep", "Glob", "ToolSearch", "WebFetch", "WebSearch"):
        return "read", str(inp.get("file_path") or inp.get("pattern") or inp.get("query") or "")[:100]
    if n == "Bash":
        cmd = inp.get("command", "")
        if GIT_WORK.search(cmd):
            return "commit", GIT_WORK.search(cmd).group(0)[:80]
        if DISPATCH.search(cmd):
            return "dispatch", DISPATCH.search(cmd).group(0)[:80]
        if PY_WRITE.search(cmd):
            target = re.search(r"open\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"][wa]", cmd)
            tp = target.group(1) if target else "(python write)"
            if not SCRATCH.search(tp):
                return "edit", tp
        real = [p for p in written_paths(cmd) if not SCRATCH.search(p)]
        if [p for p in real if not RUNLOG.search(p)]:
            return "edit", [p for p in real if not RUNLOG.search(p)][0]
        if GIT_SETUP.search(cmd):
            return "setup", GIT_SETUP.search(cmd).group(0)[:80]
        if POLL.search(cmd):
            return "poll", POLL.search(cmd).group(0)[:60]
        first = cmd.strip().split("\n")[0]
        if READISH.search(first) or (call.get("input", {}).get("description", "").lower().startswith(("read", "show", "list", "check", "inspect", "view", "look"))):
            return "read", first[:100]
        return "run", first[:100]
    return "other", n


WORK_CLASSES = ("edit", "commit", "dispatch", "spawn")
STATE_CLASSES = WORK_CLASSES + ("setup",)


def read_targets(call):
    """File paths a call reads (Read tool, or cat/sed -n/head/tail of absolute paths in Bash)."""
    n, inp = call["name"], call["input"]
    if n == "Read":
        p = inp.get("file_path")
        rng = (inp.get("offset"), inp.get("limit"))
        return [(p, rng)] if p else []
    if n == "Bash":
        cmd = inp.get("command", "")
        out = []
        for m in re.finditer(r"\b(cat|sed\s+-n\s+'?[^ ]+'?|head(?:\s+-n?\s*\d+)?|tail(?:\s+-n?\s*\d+)?)\s+((?:/|~)[^\s|;&>]+)", cmd):
            out.append((m.group(2), m.group(1).split()[0] + (m.group(1)[len(m.group(1).split()[0]):])))
        return out
    return []
