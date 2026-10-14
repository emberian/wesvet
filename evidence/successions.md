# Successions, measured (2026-10-13)

What a successor costs, how it was briefed, and what it did not get from its predecessor. Measured
from transcripts with `cv show --json` and the instruments in `tools/`; every number below names the
command or script that produced it.

**Citations.** `P12 aa50a39b#19` is seat P12, agent id prefix `aa50a39b`, message 19:
`cv show <root> --agent aa50a39b --around 19`. The fn seats' roots are in
`evidence/data/fn-seats-20261009-13.json` (`root`); the coordinator sessions are 35f3668a, 4a22422c,
905fe751, 608deb34 and d5d27b94 (forks of one another, cwd `~/dev/minidregg`). Other projects cite
`<root>/<agent>#index`. Times are UTC.

## 1. The fn seats, 2026-10-09 to 2026-10-13: every succession

164 seat transcripts in 8 seat lines (A 28, M 28, B 25, C 24, L 22, D 16, P 13, O 8), so 156
successions. Source: `cv lanes <root> --json` for the five coordinator roots, de-duplicated by agent
id (`evidence/scripts/fetch_seats.py`), then `tools/orientation_cost.py` on each
(`evidence/scripts/seat_orient2.py`). Data: `evidence/data/fn-seats-20261009-13.json`.

### 1a. Orientation cost is small and uniform

"First work" is the first edit of a real file, commit or push, dispatch (`codex exec`, a detached
job, `train.py certify|push|...`) or spawn. "First state change" also counts workspace moves (merge,
rebase, `worktree add`).

| measure (successor seats, n = 155 with a first work) | median | p25 | p75 | p90 | max |
|---|---|---|---|---|---|
| minutes to first work | 2.0 | 1.0 | 3.8 | 7.6 | 152 |
| API tokens to first work | 1.32M | 0.74M | 2.18M | 3.43M | 6.29M |
| context at first work | 91k | 72k | 112k | 143k | 212k |
| tool calls before first work | 19 | 13 | 29 | 39 | 59 |
| tool output read before first work | 108 kB | 79 kB | 141 kB | 187 kB | 246 kB |
| share of the seat's whole token spend | 2.7% | | | | |

The two long tails are waits, not orientation: C14 a539afeb (152 min) and B15 a81728e3 (180 min to a
first state change, never a first work) both waited on a peer.

The same instrument over every successor brief in every other project (briefs matching succession
language; a 25-row spot check found about three in four are real successions, the rest are words
like "succeeds" in another sense): `evidence/data/successor-briefs-all-projects.json`, 744 agents.

| project | successors | median min to first work | median tokens | median context |
|---|---|---|---|---|
| fn (cwd ~/dev/fn, 09-22 to 10-03) | 231 | 2.5 | 0.99M | 80k |
| breadstuffs | 158 | 3.8 | 1.13M | 95k |
| minidregg dir (fn deputies 10-04 to 10-08, Lean lanes) | 129 | 2.5 | 0.74M | 70k |
| delvetalk | 63 | 1.4 | 1.13M | 105k |
| dragons-clutch | 57 | 4.1 | 1.30M | 99k |
| breadstuffs/metatheory | 31 | 6.5 | 1.19M | 84k |
| graphplay | 28 | 1.2 | 0.35M | 48k |
| loicense | 13 | 1.6 | 0.39M | 41k |

The process audit's 1.4M to 2.2M tokens and 3 to 6 minutes per succession (PROCESS-AUDIT-20261009
§2) holds across projects. It measures the wrong thing: a successor is quick to act; what it acts on
is the question (§3).

### 1b. Why seats were succeeded

Classified by regex over the successor's brief and the predecessor's last message to "main"
(`evidence/scripts/endcause.py`, `evidence/scripts/succession_causes.py`). A brief that names
the abeyance file is counted as abeyance, so that bucket is an upper bound.

| cause | successions | examples |
|---|---|---|
| context ceiling park, by policy ("park at 350K", SEAT-COMMON-20261012) | 81 | A1→A2, A10→A11, P8→P9 |
| park, mark unstated | 24 | B1→B2, D7→D8 |
| abeyance (planned stops 10-12 22:04 and 10-13) | 16 | A22→A23, C21→C22 |
| parent session restart or prune | 15 | B9→B10 ("killed by a harness restart"), A25→A26, C22→C23 |
| wind-down by ember | 8 | A2→A3, M9→M10 |
| usage wall or failure | 6 | B3→B4, M20→M21 |
| predecessor still running or stopped | 6 | A27→A28, P12→P13 |

Seat peak context: median 347k (p25 312k, p75 422k). The 350K park rule came from the process
audit's recommendation 4.2 ("a builder writes its continuation and parks at 400k, not 790k"), which
priced a succession at its orientation cost alone. About two thirds of the 156 successions are that
rule firing.

### 1c. How they were briefed

Every fn successor got the same shape: a coordinator-written brief of 0.7 to 6.5 kB naming the
predecessor's continuation file (`lanedumps/builder-<x>-continuation.md`, written by hand by the
predecessor, median 10 kB, rewritten whole at the park) plus SEAT-COMMON and COORDINATION.md. None was
resumed by `SendMessage`; none was handed a `cv distill` pack. Counted over the 156 briefs:

- 88 re-list the current seat ids, because the continuation's ids are stale by construction
  ("Seat ids (every id in the continuation is stale)", D8 a2ac2d26#0).
- 58 mention a predecessor that died, was killed by a restart, or stopped for an abeyance.
- 36 hand over live processes (Codex workers, certifies, REPLs) with "re-arm a waiter".
- 29 hand over uncommitted or unaudited edits.
- 16 say the continuation is stale or was not rewritten.

### 1d. What the continuation did not carry (`tools/carry_recall.py`)

For 15 consecutive pairs in the 10-12 regime, "needed" is the set of distinctive tokens (shas,
absolute paths, `fn-` names, run ids, UPPER-CASE ids, 5+ digit numbers) that the successor wrote in
its own words or tool inputs and that occur in the predecessor's transcript, minus every token in
SEAT-COMMON and COORDINATION.md. Each pack is scored by the share of needed tokens it contains.
Script: `evidence/scripts/recall_batch.py`; data: `evidence/data/carry-recall-15-pairs.json`.

| pack | median recall | weighted by uses | min | max | size |
|---|---|---|---|---|---|
| coordinator brief alone | 0.06 | 0.07 | 0.00 | 0.15 | 0.7-3 kB |
| continuation file, as the successor read it | 0.40 | 0.46 | 0.24 | 0.67 | 17-55 kB |
| brief + continuation (what the successor got) | 0.43 | 0.46 | 0.24 | 0.67 | |
| `cv distill` pack of the predecessor | 0.73 | 0.83 | 0.58 | 0.89 | ~69k tokens |
| `tools/sharpen.py` profile 1 | 0.955 | 0.97 | 0.85 | 1.00 | ~206k tokens |
| `tools/sharpen.py` profile 2 | 0.986 | 0.99 | 0.96 | 1.00 | ~238k tokens |
| the predecessor's full transcript | 1.00 | 1.00 | | | ~343k tokens |

Pairs: P7→P8, P8→P9, P9→P10, M21→M22, M22→M23, L14→L15, L15→L16, B17→B18, B18→B19, A18→A19,
A19→A20, C19→C20, C20→C21, O5→O6, D13→D14. Over all 156 successions, `tools/seat_report.py` (brief
plus whatever the successor read from lanedumps or persisted tool results in its first 40 calls)
gives a median of 0.37, weighted 0.48 (`evidence/data/seat-report-baseline-20261009-13.json`); over
the 51 successions of 10-12 and 10-13 alone, 0.44 and 0.47. Needed tokens per pair: median 81 (55 to 138), 41% to 54%
of the distinct tokens the successor wrote. A successor got under half of what it went on to use
from its predecessor's context; it re-acquired the rest from disk, peers or the coordinator. The
token proxy cannot see knowledge used without a distinctive token, so these are bounds on fact
carriage, not on understanding.

### 1e. Misrouted messages and woken parked seats

`evidence/scripts/misroute.py` over every `SendMessage` from the 164 seats and the five coordinator
transcripts; `evidence/scripts/deadwakes.py` for the wakes. Data: `evidence/data/misrouted-messages.txt`,
`evidence/data/post-park-wakes.json`.

- 1,965 messages were addressed to a seat id. 107 reached a seat after its park notice; 26 of those
  went to a seat whose successor was already running (REDs, READYs, seam answers; for example A26's
  "READY K1 owner-retain" to the parked B22, 10-13 06:55, and B14's two C4 REDs to the parked A16).
- 14 parked seats were woken 19 times and changed nothing: 22.3M tokens, median 1.5M per seat (a
  300K+ context re-read to say "I am parked").
- Two of those wakes resumed retired seats beside their successors: "your C4 REDs went to A16 and
  O3, which are retired, and the messages resumed them beside their successors; I have stopped both
  again" (coordinator to B14, B14 ade14494#1062). A16 then did two state-changing calls as a ghost.
- M4 a3fd97d6#1411, woken by B's train-81 merge request: "another Builder M seat is already working
  in the same worktree".

## 2. Sampled successions, with what the successor got wrong or had to recover

Orientation is minutes and tokens to first work (`tools/orientation_cost.py`). "Got wrong / had to
recover" cites the successor's own words or the message that corrected it; "predecessor knew" says
where the fact lived.

| # | predecessor → successor | briefed by | orientation | got wrong or had to recover (cited) | outcome |
|---|---|---|---|---|---|
| 1 | fn P6 a76063db → P7 a28ab660 | continuation + brief | 7.9 min, 4.93M | Read landing 1's READY (#51), the sim book (#161) and c2's survey (#285) to build landing 2's packet that P6's context had held; the continuation carried 24% of the needed tokens (§1d) | landing 2 statements drafted; parked 376K |
| 2 | P7 → P8 a480ab59 | continuation + brief | 1.5 min, 0.35M | Found P7's c6 REPL already exited and resumed c6 "in the form P7 used" (#118, #125); re-read the 28.7 kB packet (#54) | R1 found false (RED #779); parked 370K |
| 3 | P8 → P9 ae621c1b | continuation + brief | 3.6 min, 0.98M | Armed waiters on the two workers handed over running (#43), re-read STATEMENTS.lsp (#58, #61); repointed the continuation's seat ids "so a successor doesn't message a parked seat" (#88); continuation recall 0.32 | A1 found false (#847); parked for abeyance |
| 4 | P9 → P10 a630e7a8 | brief (abeyance file) + continuation | 1.3 min, 0.80M | First act was to audit c6's uncommitted R8 edits P9 left (#34) | R11, M-HALF legs; parked 417K |
| 5 | P10 → P11 a38c8464 | brief + continuation | 3.7 min, 1.91M | Inherited c6 with "NO waiter armed: arm one first" (brief) | died in the 10-13 01:10 coordinator restart without rewriting the continuation |
| 6 | P11 → P12 aa50a39b | coordinator ground truth + P10's continuation | 1.3 min, 0.74M | Brief said c6's ACL2 driver and REPL were LIVE; "The ACL2 driver and REPL have already exited" (#19). Rewrote the continuation first "before anything else can be lost" (#64) | M-HALF legs 4 to 8; stopped |
| 7 | P12 → P13 af7cd219 | brief + P12's 10:55 continuation | 3.2 min, 2.30M | Handed 133 uncommitted, unaudited files from a Codex leg whose process was dead; "Leg 2 died mid-replay" (#50) | audited merge landed; parked 340K; POST landing 2 still unlanded after 7 seats in 38 h |
| 8 | B3 a308efa5 → B4 a849a862 | STATE.md stop paragraph + B2's continuation | 1.7 min, 0.82M | B3 died at the weekly wall mid-train-74 with no continuation; B4 rebuilt "B3 left: batch integrate/20261009v = train 74, unpushed" from git (#56); two detached jobs B3 started were in no ledger (PROCESS-AUDIT §5) | train 74 finished; train 76 pushed |
| 9 | B9 afd2a0a6 → B10 a5d59ed3 | brief with coordinator delta | 1.7 min, 1.42M | "its present-state file (02:02 EDT) predates its last acts" (brief #0): the coordinator reconstructed train 86's state for it | trains 86 to 88; killed |
| 10 | B17 a7936b16 → B18 a6c4b6a1 | continuation + brief | 0.4 min, 0.35M | "B17's waiter died with B17, so I re-armed farm.py wait" (#143) | C8 Fungus + train; parked 335K |
| 11 | L15 a8b1c96e → L16 aa57c0d7 | continuation | 0.9 min, 0.76M | "Reclaim carry (2b(b)): already on dev ... so the continuation is stale on this point" (#301) | log-loop-call READY; parked 350K |
| 12 | D2 a8aeb20e → D3 a084f11f | continuation, post-restart | 2.1 min, 0.53M | "The glob search my predecessor left running had walked into certcache and was never going to finish; I killed it (it was ours)" (#992) | four READYs; wound down |
| 13 | A25 ac5fb887 → A26 a8519c19 | coordinator brief: A25 "had likely only begun reading" | 2.0 min, 0.40M | Wrong: "A25 did act briefly: it wrote the two tooth books and submitted a dev tooth certify" (#55) | K1 and one-world gates; parked 400K |
| 14 | A26 → A27 a201f465 | brief + continuation | 0.7 min, 0.26M | Ran beside its predecessor: "A27 had already started editing that file, so it's A27's now" (A26 #1196) | running at the 10-13 restart |
| 15 | C22 ad191609 → C23 a3fe1f54 | brief names "the STALE continuation" (C21's from the abeyance) plus LB ground truth | 1.4 min, 0.55M | Found L21's grep had missed a reader of the deleted column in an uncommitted book (#89) | LB DECISION; returned |
| 16 | D7 a0697ba9 → D8 a2ac2d26 | continuation + brief | 5.9 min, 2.66M | "every id in the continuation is stale" (brief #0) | burndown READYs; 640K peak |
| 17 | M19 abf5fdfc → M20 a44f7f78 | continuation + brief | 8.5 min, 4.44M | M20 then ran to 918K without parking and died at the weekly limit (#2124) without a continuation | failed |
| 18 | M20 → M21 a5c435de | M19's continuation; "recover its exact state from commits and worktree" | 0.9 min, 0.75M | Measured the wrong image against M20's figure: "M20 measured fn-host, the production image ... I measured fn-host-developer ... Re-measuring" (#963) | L-RUN-LAUNCH work; parked |
| 19 | B14 ade14494 → B15 a81728e3 | continuation + brief | no work in 6 h | Waited on a Fungus seat that had stopped: "in six hours the Fungus seat has not pushed ... or committed anything" (#113) | BLOCKED; succeeded by a Sonnet |
| 20 | A1 a2858c6e → A2 a2f3c632 | continuation | 8.6 min, 1.85M | none found (the audit's "no lost thread", PROCESS-AUDIT §1) | T1-T15 certified |
| 21 | A2 → A3 a00be507 "(resume)" | continuation + fairy dossiers | 5.3 min, 4.53M | named "resumed by message, never replaced from a summary" (brief #0) but is a new agent: the word "resume" in the seat name did not mean SendMessage | landing 1; 714K peak |
| 22 | fn compress → compress-2 a5e94875 (09-29) | brief: predecessor "ended with prompt too long" | 13.7 min, 1.15M | brief's first rule is context hygiene; recovered from the worktree | READY 148 µs median |
| 23 | fn limits-live-6 → -7 a5fbdf1c (09-29) | brief "handed off at count, NOT READY" | 5.1 min, 3.45M | one of seven consecutive limits-live seats on 09-29 (limits-live-3 to -9), each handed off "at the count" | partial |
| 24 | fn coordinator, 7 harness swaps 09-29 to 10-11 | handoff files | | each swap re-derived state; ember: "please use `cv` to orient yourself into the precompaction state !!! very thoroughly" (9627d694#3264) | AUDIT-TWO-WEEKS §d |
| 25 | delvetalk objects lane (945e6fa2/a0b02f89) | brief: predecessor crashed before first commit, 14 uncommitted files | 0.7 min, 1.05M | "a second part of step 4 that never reached the worktree: a helper's PLACE work" (#483) | step 4 committed |
| 26 | delvetalk objects lane (0b46c079/a501e761) | brief: predecessor at token ceiling, branch red | 2.0 min, 1.56M | Read the predecessor's last ~100 turns with cv: "add nothing the handoff lacked. One thing it missed: its helper had dropped test_strangers' creator assertion" (#635) | steps 1a/1b committed |
| 27 | delvetalk test cull (945e6fa2, six agents at 22:37) | brief: predecessor crashed mid-way | 0.7 min, 0.37M each | six forks of one crashed lane split by file set | culls landed |
| 28 | delvetalk host lane, 21 seats 10-09 16:26 to 10-12 07:18 | "You are taking over the host lane" | median 1.4 min (all delvetalk) | same seat regime as fn: objects 21 seats, host 21, kernel 10 in 3 days | |
| 29 | cv perf → perf-2 (c6df902e/a3d96bdb) | continuation file "written by the agent that did the earlier work" | 13.5 min, 6.89M | none found; the longest orientation in the sample | perf numbers recorded |
| 30 | dclutch DESIGN → DESIGN-2 (e9d68d2f/aac1b38f) | brief: "a machine crash ate its transcript"; inherited commit + uncommitted WIP | 1.5 min, 0.45M | had to reconstruct the design tokens from the predecessor's diff (#7) | |
| 31 | dclutch GENERAL lane (3db4cac9/af0d560c) | brief: "a lane lost to a context trim" | 16.5 min, 9.0M | "The commit message restated a CU figure I inherited rather than measured. Fixing that." (#245) | |
| 32 | breadstuffs CarrierContent fixer (c8ad371d/aa2257a3) | brief: predecessor "reported it green. It does not compile. Fix it" | no edit needed | "The failure does not reproduce; it was already fixed at 03:49, after your check" (#75): a succession spawned on a stale report | none |
| 33 | graphplay (3ce72080/a207dc6c) | brief: predecessor "INTERRUPTED mid-edit" | 0.9 min, 0.45M | "The predecessor's interrupted edit was in OperatorSystem.tensor (the operator-system tensor product). The 8 build ..." (#123) | build green |
| 34 | breadstuffs/metatheory F1b (3b829648/a59e1f6d) | brief: predecessor session-capped, ~60 uncommitted files | 7.9 min, 2.71M | oriented by `git diff` over 60 files (#49 to #84); 977K peak itself | |
| 35 | loicense HTTP client (5b2df577/ac7be9be) | brief: "A previous agent ... ran out of context" | 5.4 min, 3.26M | found the predecessor's URL-object handling "actually covers the case reasonably well already" (#96) | |
| 36 | breadstuffs Path of Angels "standing" lanes (042a2645, a39c8058) | "I will revive you across cycles" | | 26 standing-lane agents on 08-05/06; 2 were ever revived by message (3 revivals); crew, descent-emit, emit-authority and judged-play were spawned again 2 to 3 times each: across the parent-session change (042a2645 to a39c8058, 08-05 to 08-06), and again at 07:15 on 08-06 because the 06:51 spawns "stopped before doing work" | see §3 |

## 3. Counter-cases: veterans resumed instead of replaced

A resume here is a message that reached an agent after its `end_turn` and its park notice and woke it
(`evidence/scripts/resumes.py`, `parkctx.py`, `deadwakes.py`); orientation is measured from the
resume point with `tools/orientation_cost.py <ir> --from-index N`. Within a seat's life, resumes by
message are the normal state (seats end a turn and wait); the rows below are resumes after the seat
had parked, the case a successor would otherwise have covered.

| veteran | resumed at | context at resume | to first work | what it did | cost |
|---|---|---|---|---|---|
| B1 a07c5a47 (fn integrator) | #1336, 18 min after parking at 633K for ember's wind-down | 641K | 0.8 min, 3.20M | trains 64 to 67 pushed in 3 h with its own read-ahead script; parked again at 838K | 156M tokens after resume, about 52M/h; B2 to B25 from cold ran a median 14M/h (p25 11, p75 21) |
| M17 a3e52ae0 | #603, 3 h after its park (freeze lifted) | 230K | 11.2 min, 6.69M | under-charge restatement committed; parked at 315K | 23M |
| L8 aaae924b | #672, 8.5 h after its park | 231K | 11.0 min, 6.18M | 2a-host started, design settled; parked at 350K | 12M |
| L8 again | #850, a RED from B13 | 307K | none | declined: "L8 is past its context mark, so please spawn L9 now; its NEXT 0 is that fix" | 1.5M |
| C2 ab611ee2 | #551, a certify RED after its park | 364K | 1.3 min, 2.88M | fixed its two reds and refiled the READY in 9 min (#625, #682) | 14M |
| Codex worker c6, session 01a12fca (post lane) | 28 prompts, 10-12 11:05 to 10-13 15:25 | compacted 9 times | | one worker context carried POST landing 2's proofs across six Opus seats, P7 to P12; each seat re-briefed it with a delta ("Seat P8 (succeeds P7). Your last turn ended on ...") | 35 MB transcript |
| 9 more Codex workers | | | | resumed by 2 to 5 consecutive seats: 01a13031 (post, P7-P12), 01a130de (memory-run-launch, M22-M25), 01a131f1 (b-native-launch, B20-B22), 01a1311e (log-seq, L16-L20), 01a12f86, 01a13104, 01a130f8, 01a12fd8, 01a12fa1 | `evidence/data/codex-workers-fn-20261009-13.json` |
| fn coordinator, forked 9627d694 → be1e9dcf → 35f3668a → 4a22422c → 905fe751 → 608deb34/d5d27b94 | each fork | 4a22422c: 976K peak, 473K inherited | | the coordinator kept its own context across six sessions by fork and prune, the only Claude veteran that did | ember on the cost: "after compaction we tend to achieve drift" (905fe751#5190) |
| batch runner BE a502d174 and four fork workers (09-29 10:06) | fork | parent's | 1.2 min each | four forks inherited BE's context and each fixed one red | |
| breadstuffs hidden-instance ae963e7e and signal-wire af5bbf25 lanes | 2 and 1 revivals by message, 08-05 | | | the two standing lanes revived as designed | |

## 4. Reading the table

- Every successor acted within minutes; none was idle for want of a brief. The successor's real
  cost was carrying under half of what it went on to use (§1d), and recovering live state the
  continuation could not hold: handed-over processes whose waiters died with the predecessor (rows
  2, 6, 10), uncommitted work from dead workers (4, 7, 25, 34), and coordinator paraphrases that were
  wrong (6, 13).
- The fn regime manufactures successions: about two thirds fire the 350K park rule, which was set on
  a measurement of orientation cost alone. The rest come from parent-session restarts, abeyances
  and walls, which kill every seat at once.
- Where a veteran was resumed, it acted in about a minute with no re-reading (B1, C2). The
  per-turn cost scales with the context it carries: B1 at 641K to 838K spent about 52M tokens an hour.
- The fn lanes' real veterans are the Codex workers: one c6 session outlived six Opus seats.
- The one designed "standing lane" experiment (breadstuffs, 08-05) decayed into respawn within a
  day: 2 of 26 standing lanes were ever revived; the rest were replaced at the parent-session change
  or after stopping early.
