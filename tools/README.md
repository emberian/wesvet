# tools

Instruments over cv's unified IR (`cv show <id> --json`, `cv show <root> --agent <id> --json`). All
are read-only on transcripts: they call `cv show` and parse its stdout, and write only where `--out`
or a redirect points. `sharpen.py` refuses an `--out` under `~/.claude/projects`. Python 3, standard
library only. `irlib.py` is the shared reader and classifier.

## orientation_cost.py

What a seat paid before it first changed state.

    orientation_cost.py <ir.json> [--from-index N] [--json]
    orientation_cost.py <root-session> --agent <agent-id> [--from-index N] [--json]

From message 0 (or N, for a resume by message) to the first tool call of each class: `setup` (git
merge, rebase, worktree add, checkout -b, branch, reset --hard), `edit` (Edit/Write outside /tmp and
scratchpads, a shell redirect, tee or `sed -i` into a real path, an inline `python3 - <<EOF` program
that opens a file for writing), `commit` (commit, push, cherry-pick, am, revert, tag), `dispatch`
(`codex exec`, nohup/setsid/`& echo $!` jobs, `train.py certify|push|regen|...`, swarm-build),
`spawn` (Agent/Task), `message` (SendMessage, reported but not counted). For each: wall-clock
seconds, API tokens summed once per request (input + cache read + cache write + output), the context
of the turn that made it, calls and tool-output bytes before it. `first_work` is the earliest of
edit, commit, dispatch, spawn; `first_state_change` adds setup.

Limits: classification is by regex over the command. A write made by a script file run by path, or
by `make`, counts as `run`. Redirects into `*.log`, `*.pid`, `*.out`, `rc` and `status` files are
bookkeeping, not edits. Token totals are mostly cache reads; they are what a usage window counts,
not a price.

## anatomy.py

What a long transcript is made of, in prune-relevant buckets (the list and definitions are in its
docstring): brief, incoming, notification, poll, superseded_read, repeated_cmd, error_output, reread,
read/run_referenced, read/run_unreferenced, work_call, assistant_text, thinking_signature,
tool_input. "Referenced" means a distinctive token the output introduced (a sha, an absolute path, an
`fn-` name, a run id, an UPPER-CASE id, a 5+ digit number) appears later in the agent's own words or
tool inputs. Also counts calls by class, notifications, messages received, commits.

    anatomy.py <ir.json> [--json]

Limits: "superseded" and "repeated" are by path and command identity, not content. Thinking is
counted by signature length, because Claude Code stores the text empty. Use with `cv doctor`, whose
token attribution is the better measure of context share.

## carry_recall.py

How much of what an agent needed next does a handoff pack carry.

    carry_recall.py --pred <ir> --succ <ir> --pack NAME=FILE ... [--common FILE ...] [--json]
    carry_recall.py --self <ir> --cut N --pack NAME=FILE ... [--common FILE ...] [--json]

"Needed" = distinctive tokens the successor (or the agent after message N) wrote in its own words or
tool inputs that occur in the predecessor's transcript (or before N), minus tokens in `--common`
standing documents. Each pack (a continuation file, a `cv distill` pack, a `.sharpened.jsonl`, a
brief) gets recall, use-weighted recall, size, and its most-used misses.

Limits: a token proxy. It credits a sha or a path, not the reason it matters; it cannot see
knowledge used without a distinctive token; it counts a token the successor re-read from disk as
needed even when re-reading was cheap.

## seat_report.py

The evaluation plan's nightly measurement of a swarm's seat lines.

    seat_report.py --root ROOT [--root ROOT ...] [--since DATE] [--seat-re REGEX] [--common FILE ...]
                   [--cache DIR] [--json OUT]

For the coordinator roots' sub-agents whose description matches `--seat-re` (default fn's "fn Builder
X<n>"), de-duplicated across forked roots: successions per line, each successor's orientation and the
carry recall of what it was given (its brief plus what it read from lanedumps, a distill pack or
persisted tool results in its first 40 calls), messages to seats after their final park notice and
misroutes (sent while the successor was running), seat lifetimes. Baseline run:
`evidence/data/seat-report-baseline-20261009-13.json` (164 seats, 156 successions, 20 s).

Limits: a seat is recognized by its description; a successor that read its continuation through an
unusual path in its first 40 calls is scored on its brief alone.

## sharpen.py: the sharpened-veteran prune profile

    sharpen.py <root-session> --agent <agent-id> --out DIR [--profile 2] [--keep-last 25] [--cut N]
    sharpen.py <ir.json> --out DIR ...

Rewrites a Claude transcript into `DIR/<agent>[.cutN].v<profile>.sharpened.jsonl` with the same
records, and reports in `DIR/....sharpen.json` (counts and bytes by reason, the estimated context,
and a structural check: parent links resolve, every tool_use has its result, no empty assistant
record). `--cut N` sharpens the transcript as it stood at IR message N, so the result can be scored
against what the agent actually did next.

**Kept verbatim, everywhere:**
- the brief, and every message received: coordinator and peer messages (queued_command attachments
  and "... sent a message ..." user records) and human prompts;
- every text block the agent wrote;
- every tool call's input, except older bodies of a file written again later;
- the outputs of state-changing calls (edit, commit, push, merge, dispatch, spawn, SendMessage);
- outputs under 400 bytes;
- everything in the last `--keep-last` tool calls (25), thinking included;
- setup attachments (instructions, session context, environment, skills, tool lists).

**Kept shortened:**
- a failed call's output: head 1.5 kB + tail 1.5 kB;
- a read or run output whose introduced tokens are used later: head 3 kB + tail 3 kB;
- profile 2 only: a read of a document or source file (`.md .lisp .lsp .lean .rs .py .json .txt`,
  READY, BRIEF, STATEMENTS): head and tail 8 kB if used later, 4 kB if not, and never treated as a
  repeat (a second range of the same book is new text);
- an older Write/Edit body of a file written again later: its first 1 kB.

**Dropped, outside the tail:**
- thinking blocks (an assistant record left empty is removed and its child re-linked);
- background-task notifications, `hook_success` and `total_tokens_reminder` attachments (removed,
  children re-linked);
- poll outputs (sleep and until loops, Monitor, TaskOutput): replaced by a marker with the last line;
- all but the last output of a status command run again later (same verb and paths);
- read and run outputs never used later (profile 1: all of them; profile 2: all but documents).

Every replaced output carries `[sharpened: <reason> output, N bytes; cv cat <session> <tool_use_id>]`,
so the original stays one command away. The last assistant record's recorded usage is rewritten to
the estimate (the "revive" `cv prune` applies), because Claude Code's resume gate reads it.

**To resume a sharpened seat** you would copy the `.sharpened.jsonl` into the parent session's
`subagents/` as `agent-<new id>.jsonl` with a `.meta.json`, as `cv adopt` does, and `SendMessage` to
it. This study never did that: it writes nothing under `~/.claude/projects`.

### The test on a real fn seat: P7 (a28ab660, POST landing 2), 2026-10-12

Full transcript (848 messages, recorded context 383K):

| profile | records | estimated context | largest drops |
|---|---|---|---|
| 1 | 1,319 to 605 | 240K | thinking 612 kB, hook attachments 306 kB, token reminders 119 kB, repeated status 92 kB, unused output 80 kB |
| 2 | 1,319 to 605 | 290K | the same, keeping document reads |

Self-cut at message 500 (recorded context 269K), scored against the 142 tokens P7 wrote after 500
that occur before it (`evidence/prune/p7-selfcut500-recall.json`):

| pack | estimated context | recall | weighted |
|---|---|---|---|
| `cv distill --upto 500` | 43K | 0.62 | 0.67 |
| `cv distill --upto 500 --keep-last 40 --tail-result-max 8000 --note-max 12000` | 60K | 0.78 | 0.83 |
| the same with `--keep-last 100` | 132K | 0.92 | 0.94 |
| sharpen profile 1 | 173K | 0.94 | 0.94 |
| sharpen profile 2 | 213K | 0.986 | 0.984 |
| the full prefix | 269K | 1.00 | 1.00 |

**What the sharpened P7 would have gotten wrong against the original:**
- Profile 1 dropped two reads that P7 had not yet quoted at message 500 and used afterwards: the
  survey `c2/SURVEY.md` (#285, which explains `fn-rtc-requests`: refusals continue through later
  requests and do not roll back earlier ones) and the head of `books/post-transaction-sim.lisp`
  (#161, the rely and `fn-ptx-kd-of`). P7 used both at #567 (the brief it wrote for Codex worker c7,
  which names `fn-ptx-kd-of`) and #700 to #712 (its revision of section R after c6's two findings).
  A profile-1 veteran would have written that brief from memory of a summary, or re-read both files
  first (`cv cat` returns them).
- Profile 2 keeps those, and misses two tokens of one run output (#402): a `test_search` driver
  script whose text set `ACL2_PROJECTS=/Users/ember/dev/fn/build/lanes/post/acl2-projects` and
  echoed the `TS-DONE` marker. P7 reused both when it wrote the next driver (#718). A profile-2
  veteran writing that driver without them could have run the search against the wrong certificate
  projects directory, or waited on a marker the script never prints.
- Both profiles drop P7's thinking before the tail. What it held is not recoverable from the stored
  transcript, so neither the score above nor any other instrument here measures that loss.

The two rule bugs this test found are fixed: a status-command key that included the leading
`cd DIR` (different reads in one repo looked like repeats) and a repeat rule applied to a second range
of the same book. Profile 1 scored 0.89 before the first fix.

### What cv would need to do this itself

- `cv prune` addressing a sub-agent: today `cv prune agent-<id> --dry-run` resolves to the parent
  session (it reported 35f3668a for B1's id), and a transcript path is refused.
- A "used later" test for snipping (sharpen's referenced/unreferenced split) beside `--min-size`.
- A document-read exemption, or a per-tool keep rule, so book and design reads survive.
- `--drop-attachments hook_success,total_tokens_reminder` and notification removal with re-linking.
- An `--agent-of <root>` emit for the pruned result, as `cv distill` has, so a sharpened seat can be
  resumed by `SendMessage` without copying files by hand.
