# Evaluation plan: the practices on fn's next two weeks

How to run `docs/practices.md` on fn from the first day the swarm runs again (call it day 1; the
plan is two weeks, days 1 to 14) and decide, by metrics fixed here before day 1, whether they beat
the current regime. Nothing below may be changed after day 1 except by a dated amendment at the end
of this file that names what changed and why; a metric changed after its data was seen does not
count.

## 1. Arms

- **Arm 0, the current regime** (the 10-09 to 10-13 baseline): park at 350K with a hand-written
  continuation; a fresh successor briefed by the coordinator; respawn from file after a restart;
  messages by agent id.
- **Arm 1, the cheap bundle**: practices 1 (adopt and resume after a restart), 2 (seat addresses),
  3 (resume-by-message thresholds), 4 (generated continuation: `cv distill` pack + intent note) and
  6 (Codex worker ledger and routing).
- **Arm 2, arm 1 plus practice 5** (one sharpened, resumed expert context per line).

## 2. Assignment: a crossover by seat line

| | week 1 (days 1-7) | week 2 (days 8-14) |
|---|---|---|
| arm 0 | B, D, M, O | A, C, L, P |
| arm 1 | A, C, L | B, D, O |
| arm 2 | P | M |

Each line is its own control across the weeks, and each week has both regimes running on the same
dev, the same boxes and the same coordinator, so a usage wall, a restart or a hard week lands on
both arms. P and M take arm 2 because both are proof lines with long landings (POST landing 2, 7
seats; L-RUN-LAUNCH, M21 to M28) and because arm 2 is the expensive one.

Restarts: when the coordinator's session restarts, arm-1 and arm-2 seats are adopted and resumed
(practice 1) and arm-0 seats are respawned from their files, as now.

## 3. Setup, before day 1

1. Freeze the instruments: tag this repository `wesvet-eval-v1` at the commit that adds this file.
   The scorer is `tools/seat_report.py`, `tools/orientation_cost.py`, `tools/carry_recall.py`,
   `tools/anatomy.py` and `evidence/scripts/` at that tag.
2. In fn's coordinator files: `build/coordinator/SEATS` and the send helper (practice 2); the park
   script for arm-1 lines (practice 4: `cv distill --pack`, the 2 kB intent note); the restart
   checklist (practice 1); the worker ledger per lane (practice 6); the routing line format in
   STATE.md (practice 3).
3. For arm 2, a sharpen emit that installs the sharpened transcript as a sub-agent of the live root
   (the step `cv distill --agent-of` performs), tested once on a parked seat outside the trial. If it
   is not ready on day 1, P runs arm 1 in week 1 and arm 2 runs on M in week 2 only; that is the only
   pre-authorized change.
4. Each brief names its arm in its first line ("arm 1"), so the scorer can split without a lookup.

## 4. Metrics, fixed

Collected nightly with:

    tools/seat_report.py --root <each coordinator root of the day> --since <day 1> \
      --common build/coordinator/briefs/SEAT-COMMON-*.md --common build/coordinator/COORDINATION.md \
      --json evidence/eval/day<N>.json

plus the per-landing ledger below. Baselines are from `evidence/data/seat-report-baseline-20261009-13.json`
and `docs/findings.md`.

**Primary (decide the trial):**

| id | metric | unit | baseline (arm 0, 10-09 to 10-13) | arm 1 wins if |
|---|---|---|---|---|
| P1 | carry recall of what each successor was given (brief + continuation or pack), median per succession | share | 0.37 (weighted 0.48) | median at least 0.65 |
| P2 | REDs and false statements against a line's own landing, per landing (RED messages to main naming the line, Codex FINDINGS false/unsound items, reverted or amended rows) | count per landing | measured in week 1's arm-0 lines | at most arm 0's, and not more than 1.0 higher on any line |
| P3 | wall-clock from the first brief that names a landing to the train that lands it on dev | hours per landing | measured in week 1's arm-0 lines (reference: POST landing 2 unlanded after 38 h and 7 seats) | median lower than arm 0's |
| P4 | Claude tokens per landing (`cv lanes` totals of the seats and Sonnets that worked on it) | tokens per landing | measured in arm 0 | at most 20% higher than arm 0's |

**Secondary (explain the result; no decision rests on them alone):**

| id | metric | baseline |
|---|---|---|
| S1 | successions per line per day, and the share caused by restarts, abeyances, walls (`evidence/scripts/succession_causes.py`) | 31 per day; restart or prune 15 of 156 |
| S2 | successor orientation: minutes, tokens and context to first work | 2.0 min, 1.32M, 91K |
| S3 | misroutes per 100 seat-addressed messages (`tools/seat_report.py`); dead wakes and their tokens (`evidence/scripts/deadwakes.py`) | 1.22 per 100 (24 of 1,968; misroute.py's earlier park time counts 26); 19 wakes, 22.3M |
| S4 | successors whose first 160 messages report a stale or wrong inherited fact (`evidence/scripts/early_disc.py`, then read) | 5 of 21 sampled rows |
| S5 | contexts per landing (seats plus resumed sessions that worked on it) and Codex worker sessions per landing | POST landing 2: 7 seats |
| S6 | per routed work item: tokens and minutes to READY or RED, by practice-3 rule branch | none |
| S7 | arm 2 only: expertise score per task (carry recall of the task's needed facts against the veteran's context at task start versus the pack a successor would get) | none |
| S8 | arm 2 only: tokens per hour of the sharpened veteran versus the line's arm-1 week | B1 resumed at 641K: 52M/h; B seats cold: 14M/h |

**Per-landing ledger.** A landing is the unit P2 to P4 are counted over. The coordinator keeps
`evidence/eval/landings.md` in this repository: landing name, line, arm, first brief (agent and
time), each context that worked on it, the train and dev sha that landed it, and every RED against it
with its message. A landing that spans the week boundary counts in the arm that started it.

## 5. Decision rules, fixed

- **Arm 1 becomes the default** if P1 and P3 win and P2 and P4 hold, on the pooled two weeks
  (each line contributes its arm-1 week against its own arm-0 week).
- **Arm 1 is refuted** if P1's median is under 0.55, or P2 is higher than arm 0's on three or more
  lines, or P4 is more than 20% higher pooled.
- **Each practice can fail alone**, by the refutation in `docs/practices.md`: practice 1 if adopted
  seats fail to resume more than 1 time in 5; practice 2 if misroutes stay above 0.3 per 100 among
  helper-sent messages; practice 4 if its successors' context at first work exceeds 130K; practice 6
  if review findings per resumed worker past 4 compactions exceed fresh workers'. A failed practice
  is dropped from arm 1 for the rest of the trial and the drop is recorded as an amendment.
- **Arm 2 stays** only if its line's P2 is lower than the same line's arm-1 or arm-0 week and its P4
  is at most 40% higher. Otherwise the sharpened veteran is not worth its tokens on this evidence,
  and practice 5 is retired.
- **Stop early** if any arm-1 or arm-2 line has two REDs in one day that trace to a missing inherited
  fact (the successor or veteran acted on something its predecessor knew was false): that line
  returns to arm 0 and the incident is written up in `evidence/eval/`.

## 6. What this cannot see, stated in advance

- Codex tokens (they run under `codex exec`, outside `cv lanes`); the worker ledger counts launches,
  not tokens.
- Thinking: dropped by practice 5's sharpen and invisible to every instrument here.
- Task difficulty: the crossover controls for line, not for which landing a line drew that week.
  Landings are reported one by one, not only as medians, so a hard landing is visible.
- The coordinator knows the arms. Briefs follow a template per arm and the scorer is deterministic,
  so the coordinator's influence is in routing and rulings, which S6 records.
- Small numbers: two weeks yield on the order of 10 to 20 landings. The decision rules are
  thresholds, not significance tests, and the report gives every landing's numbers.

## 7. The report

On day 15, `evidence/eval/REPORT.md`: one table per primary metric by line and week, the decision
each rule gives, the amendments, and the per-landing ledger. Present state, rewritten whole.

## Amendments

(none)
