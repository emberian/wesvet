# Practices to evaluate

Six practices, each from a measured cost in `docs/findings.md`. Each states its claim, its mechanism,
how it is evaluated (metric, sessions, what refutes it) and its cost. `docs/evaluation-plan.md` runs
them together on fn's next two weeks; the metrics and thresholds below are the ones fixed there.

Baselines are the fn seats of 10-09 to 10-13 (`evidence/data/fn-seats-20261009-13.json`): 156
successions, median seat life 2.6 h, 218 API requests and 46M tokens; orientation 2.0 min and 1.32M
tokens to first work; carriage (what a successor was given) 0.37 of needed facts over all 156
(`tools/seat_report.py`), 0.43 over the 15 hand-checked pairs.

## 1. After a parent restart, adopt and resume; never respawn a live seat from its file

**Claim.** Parent-session restarts, prunes and forks stop causing successions. Every in-process seat
comes back with its whole context instead of a successor with 43% of it.

**Mechanism.** The coordinator's restart checklist, run before anything else in the new session:
`cv lanes --recent 3 --cwd <dir> --unfinished` (the rescue list), `cv adopt <agent-ids> --into
<live-session>`, then `SendMessage` to each adopted id: "Resumed after a harness restart at HH:MM.
Re-check your running jobs by PID file, then continue." A seat past its park mark is adopted anyway
and asked only for its pack (practice 4), so nothing is lost even when it is retired.

**Evaluation.** Metric R1: share of successions whose cause is a parent restart, prune or fork
(classifier: `evidence/scripts/succession_causes.py`). Baseline 15 of 156, plus every seat of the 8
mass respawns. Metric R2: for adopted seats, minutes and tokens from the resume message to first
work (`tools/orientation_cost.py --from-index N`) and the first-two-hours RED count against them.
Refuted if adopted seats fail to resume in more than 1 of 5 attempts (harness refusal, stale-usage
wall), or if their first-two-hours RED rate is higher than respawned seats' at matched seat lines.

**Cost.** One context re-read per adopted seat on its first turn: 0.3M to 3M tokens (its context
size), against 1.3M for a successor's orientation. Five commands per restart.

## 2. Address seats, not agents

**Claim.** Messages stop reaching retired seats; ghost resumes stop.

**Mechanism.** One file maps each seat to its live agent id (`build/coordinator/SEATS`, one line per
seat: `P aa50a39b3d3a6d96d since 2026-10-13T05:18Z`), rewritten by the coordinator at each spawn,
adopt or retirement. Seats and the coordinator send by seat letter through a three-line helper that
reads the file and calls `SendMessage` with the current id; a message to a retired id is refused by
the helper with the current one named. Continuations and briefs name seat letters, never ids.

**Evaluation.** Metric M1: messages delivered to a seat after its park notice whose successor was
running, per 100 seat-addressed messages (`evidence/scripts/misroute.py`); baseline 26 of 1,965
(1.3 per 100). Metric M2: wakes of parked seats that change nothing, and their tokens
(`evidence/scripts/deadwakes.py`); baseline 19 wakes, 22.3M tokens. Metric M3: ghost resumes; baseline
2. Refuted if M1 does not fall below 0.3 per 100 while the helper is in use.

**Cost.** A file and a helper; the coordinator's one extra write per spawn.

## 3. Resume by message under fixed thresholds

**Claim.** Short follow-ups go to the veteran that holds the context, and long tasks start from a
pack, by a rule the coordinator does not have to re-derive each time.

**Mechanism.** The rule, from the break-even arithmetic in findings §1 (a successor overtakes a
resumed veteran at context C after about 1.3M / (C - 91K) requests):
- Resume the parked seat by `SendMessage` when the work item is a RED, a review question or a
  seam answer on its own lane, at any context below 600K.
- Resume it for a new task when its context is under 200K and it has not compacted. The price is
  stated: at 200K a resumed context costs more tokens than a successor from about 12 requests on;
  what it buys is the whole context instead of 43% of it.
- Otherwise start the next context from practice 4's pack, or from practice 5's sharpened veteran
  where that is running.
The coordinator records each routing decision as one line in STATE.md: item, seat, rule branch.

**Evaluation.** Metric T1: per work item, tokens and wall-clock from routing to READY or RED, split
by rule branch. Metric T2: REDs found later against that item's own work. Sessions: every routed item
in the trial. Refuted if resumed items cost more tokens per item than pack-started items at matched
item type (RED fix, review, landing), or carry more later REDs.

**Cost.** Resumed turns read the veteran's whole context: at 300K about 3.3 times the per-request
tokens of a successor at 91K. The rule bounds that to short items and small contexts.

## 4. A continuation is generated, then annotated; never written alone

**Claim.** A successor gets most of what it will use. Carriage rises from 43% (brief +
continuation) to at least 70% at no larger starting context, and fewer successors discover a stale
continuation.

**Mechanism.** At its park mark a seat runs one script instead of hand-writing the continuation:
1. `cv distill agent-<own id> --pack build/coordinator/lanedumps/<seat>-distill.md` (deterministic,
   about 2 s; the pack keeps the brief, every message received and the agent's own words verbatim,
   indexes commits, paths and errors, and keeps the last 12 calls as real turns).
2. A short intent note written by the seat, at most 2 kB: NEXT (the first act), UNVERIFIED (claims
   not yet checked), LIVE (each running process with its PID file and waiter), and RULES LEARNED
   (lessons stated as rules, so the dead ends that taught them can be dropped).
3. The successor's brief is the coordinator's delta, then the intent note, then the pack. The
   coordinator does not paraphrase state it has not read: every live-process claim in a brief cites
   the PID file and its `ps` result at brief time.

**Evaluation.** Metric C1: carry recall of what each successor was given (`tools/seat_report.py`)
on every succession in the trial, against the baseline median 0.37 (weighted 0.48). Metric C2: successor
orientation (minutes, tokens, context at first work) against 2.0 min, 1.32M, 91K. Metric C3:
successors whose first 160 messages report a stale or wrong inherited fact
(`evidence/scripts/early_disc.py`, read by hand); baseline: rows 2, 6, 10, 11, 13 of S §2 in a sample
of 21 fn rows. Target: C1's median at least 0.65. Refuted if it is under 0.55, or C2's context at first work
exceeds 130K.

**Cost.** The pack is about 69K tokens (median of 15), read once; the successor's starting context
moves from about 91K to about 100K, about 2M more tokens over a 218-request seat (4%). Two seconds of
`cv distill` per park.

## 5. One expert context per seat line, sharpened and resumed, retired by rule

**Claim.** A seat line that keeps one context, sharpened at each park mark and resumed with the next
task, makes fewer errors on its subsystem than a line of successors, at a token cost the error
savings repay.

**Mechanism.** At the park mark the seat is not replaced: `tools/sharpen.py` profile 2 rewrites its
transcript (drops old thinking, notifications, poll output, repeated status, unused run output; keeps
messages, own words, work calls, used outputs, errors and document reads), a sharpened copy is
installed as the seat's sub-agent (the step `cv distill --agent-of` and `cv adopt` already perform
for their outputs; sharpen needs the same emit), and the next task is sent to it by message.
Retirement, to a practice-4 pack successor, when any of:
- the sharpened context is over 250K (it can no longer buy headroom);
- it has compacted twice;
- a correction from ember or the coordinator is followed by the same wrong claim again;
- its expertise score (below) falls under a pack successor's for two consecutive tasks.
Expertise score: for each new task, `tools/carry_recall.py` of the facts the task ended up using,
against the veteran's context at the task's start versus the generated pack.

**Evaluation.** Run on two of the eight seat lines (one proof line, one host line), the other lines
as controls. Metric E1: REDs and false statements found against the line's own landings per landing.
Metric E2: tokens per landing. Metric E3: seats (contexts) per landing; baseline POST landing 2, 7.
Metric E4: expertise score per task. Refuted if E1 is not lower than the control lines' and E2 is
more than 40% higher.

**Cost.** The sharpened veteran starts at about 206K to 238K instead of 91K: up to about 115K more
tokens per request, about 25M over a 218-request seat life (+54% of a 46M seat), shrinking as both
approach the park mark. This is the expensive practice; its evaluation is what decides whether it
stays.

## 6. Name the de facto experts: route a lane's next task to its Codex worker session

**Claim.** The Codex worker sessions that already outlive the Opus seats (c6 across six seats) become
the lane's declared expert context, and the seat becomes a thin router, so landings stop depending on
how many seats they pass through.

**Mechanism.** A worker ledger per lane (`build/lanes/<lane>/WORKERS`: session id, what it knows,
last prompt, compactions, last report path), written by the seat at each worker launch and resume.
A seat's continuation names the ledger instead of restating the workers' state. A new task on the
lane resumes the session that holds its context (`codex exec resume <session>`) unless that session
has compacted more than 6 times, in which case a fresh worker is started from the last report.

**Evaluation.** Metric W1: worker sessions per landing and seats per landing (baseline for POST
landing 2: c6, c9, c4 and more across 7 seats). Metric W2: false statements and unsound claims found
in review against resumed-worker output versus fresh-worker output (from the Codex review FINDINGS
files). Metric W3: seat orientation tokens, which should fall when the seat no longer restates the
worker's state. Refuted if W2 is higher for workers past 4 compactions than for fresh workers.

**Cost.** One ledger line per launch. Codex token use is not visible to `cv lanes` (PROCESS-AUDIT §5);
the ledger is the only record of it.
