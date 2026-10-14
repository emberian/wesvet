# Findings

What the transcripts on this machine say about the three sub-questions, as of 2026-10-13. Evidence
is in `evidence/successions.md` (S), `evidence/transcript-anatomy.md` (A) and the data under
`evidence/data/`; citations follow those files' form (`P12 aa50a39b#19`; `<root>/<agent>#n`).
Scope: 156 fn seat successions (10-09 to 10-13), 744 successor briefs in ten projects, 15 scored
successions, 8 anatomized veterans, 1 self-cut prune test. No sharpened or distilled veteran was
resumed; every prune result is offline.

## The three strongest findings

1. **A successor gets under half of what it goes on to use.** Across 15 consecutive fn seat pairs
   the coordinator's brief plus the predecessor's hand-written continuation file contain a median
   43% (range 24% to 67%) of the distinctive facts the successor later wrote that existed in its
   predecessor's context, and 37% over all 156 successions; the brief alone 6%. `cv distill` of the predecessor carries 73% at about
   69K tokens, a context no larger than the 91K a successor reaches before its first act. A
   sharpened transcript carries 95% to 99% at 206K to 238K (S §1d). Orientation cost, the measure
   the fn swarm used to price successions, is about 2 minutes and 1.3M tokens and 2.7% of a seat
   (S §1a); it does not see this loss.
2. **The fn regime manufactures successions, and the tools to avoid them sat unused.** About two
   thirds of the 156 successions were the 350K park rule firing; most of the rest were parent-session
   restarts, abeyances and walls that killed every seat at once (S §1b). ember asked for the
   alternative in words ("mind sendmsg those running agents to resume em?", 4a22422c#2098); the
   coordinator respawned five seats instead (#2115). `cv adopt`, which makes a dead session's
   sub-agents resumable from a live one, shipped the next day and was never run through two more
   mass respawns (A §4).
3. **The veterans that did exist were the ones nobody designed.** One Codex worker session (c6,
   01a12fca) carried POST landing 2's proofs across six consecutive Opus seats, P7 to P12, through 28
   prompts and 9 compactions; nine more workers spanned two to five seats (S §3). The Opus seats,
   briefed as "a long-lived seat ... resumed by message for days, never replaced" (C1 ae2f9782#0),
   lived a median 2.6 hours each (p25 1.2, p75 5.0; 218 API requests). The one designed standing-lane experiment (breadstuffs, 08-05)
   revived 2 of 26 standing lanes by message (3 revivals); the rest were replaced at the parent-session change or after stopping early (S row 36).

## 1. Resume, don't respawn

**What orientation cost measures as.** Time and tokens from spawn to the first edit, commit,
dispatch or spawn: median 2.0 min (p75 3.8, p90 7.6) and 1.32M tokens (p75 2.18M), context 91K, 19
tool calls and 108 kB read (n = 155 fn successors). Other projects agree: 1.2 to 6.5 minutes and
0.35M to 1.3M tokens at the project median (S §1a). It is cheap and uniform because successors act
early on whatever they were given; it is the wrong measure of a succession's cost.

**What a succession actually costs.**
- Carriage: 43% of the needed facts (finding 1). The rest is re-acquired from disk, peers or the
  coordinator, or not at all.
- In-flight state the continuation cannot hold. 36 of 156 briefs hand over live processes, 29 hand
  over uncommitted or unaudited edits, 16 flag a stale continuation (S §1c). Waiters die with the
  predecessor ("B17's waiter died with B17", B18 a6c4b6a1#143); dead workers leave work unaudited
  (133 files, P13 af7cd219#0 and #50); predecessors leave processes that will never finish (D3
  a084f11f#992).
- Coordinator paraphrase, which is wrong when the coordinator does not have the state: P12's brief
  said c6's REPL was live; "The ACL2 driver and REPL have already exited" (P12 aa50a39b#19). A26's
  brief said A25 "had likely only begun reading"; "A25 did act briefly: it wrote the two tooth books
  and submitted a dev tooth certify" (A26 a8519c19#55).
- Renaming the seat. Each successor is a new agent id, so peers keep the old one: 26 messages went to
  a seat whose successor was running, 19 wakes of parked seats changed nothing (22.3M tokens), and
  two retired seats were resumed beside their successors as ghosts (B14 ade14494#1062) (S §1e).
- Landing latency. POST landing 2 went through seven seats in 38 hours and is unlanded; each seat did
  real work (two false keystones found, S rows 2 and 3), and each began by rebuilding the packet the
  last one held.

**What resume costs.** A resumed veteran pays for its context on every turn. B1, resumed at 641K,
pushed four trains in three hours with no re-reading and spent about 52M tokens an hour; B seats
started cold ran a median 14M an hour (S §3). In raw tokens a successor overtakes a resumed 350K
veteran after about five API requests: the veteran carries about 260K more per request than a
successor at 91K, and the successor's whole orientation is 1.3M. A resumed veteran therefore wins
on tokens only for short follow-ups (C2 fixed its own two reds 9 minutes after parking, C2
ab611ee2#551 to #682), and on carried facts always.

**When resume is worse.**
- Near the ceiling: M20 ran past every park mark to 918K and died at the weekly wall without a
  continuation; M21 recovered from commits and then measured the wrong image against M20's figure
  (M21 a5c435de#963). A veteran that does not checkpoint loses everything at once.
- After compaction: ember on the coordinator, "after compaction we tend to achieve drift"
  (905fe751#5190). None of the eight anatomized veterans compacted, so this study has no measured
  case.
- Poisoned by dead ends: not observed. The fn_C1 dead ends (8.9% of its bytes) did not mislead it;
  they also did not teach it: the same foreground-timeout failure recurred at #382 and #1065 until it
  wrote the rule down (A §4).

**The answer, on this evidence.** Resume by message when the follow-up is short or the veteran is far
below the ceiling. For anything longer the choice is not resume-or-respawn but which pack the next
context starts from, and the hand-written continuation file is the worst of the measured packs.

## 2. Prune the veteran

**What a long transcript is made of** (A §2, §3), for builder seats of 770K to 920K:
- thinking signatures, 31% to 41% of tokens, stored opaque, so unevaluable;
- waiting (harness notifications and poll calls), 6% to 11% of bytes; the coordinator 26%;
- stale status (repeated status commands, superseded reads), 3% to 9%;
- outputs never used later, 9% to 23% (reads 7% to 16%, runs 1% to 6%);
- the agent's own words, the brief and every message received, 0.4% to 1.8%;
- state-changing calls, 15% to 27%, and outputs used later, 4% to 19%.
Identical re-reads inside a veteran are under 1%.

**A sharper veteran is possible and measurable.** `tools/sharpen.py` profile 2 cuts P7's recorded
383K to an estimated 290K and, at a cut at message 500, kept 98.6% of the facts P7 used afterwards
(profile 1: 94.4%; `cv distill --upto 500`: 62% at 43K) (A §5). Over the 15 succession pairs the
medians are 206K and 95.5% (profile 1) and 238K and 98.6% (profile 2) against the predecessor's
343K (S §1d). Most of the saving is thinking; the rest is waiting and stale status.

**What must never be pruned**: the brief, every message received (corrections and rulings live
nowhere else, and they are 1% to 2% of a seat), the agent's own words, state-changing calls with
their outputs (they hold the Codex briefs and the edits), outputs used later, errors, and a dead end
whose lesson has not been written down as a rule or a file. Reads of documents and source must be
kept or retrievable: "used later" is known only up to the cut, and three of profile 1's misses were
book and survey reads used after it.

**The tools today.** `cv distill` takes a sub-agent id and keeps the right things verbatim (brief,
messages, own words) but elides the outputs a seat's knowledge lives in, which is why it scores 73%.
`cv prune` cannot address a sub-agent: `cv prune agent-<id> --dry-run` resolves to the parent session
and a transcript path is refused, so no fn seat can be pruned with it. `cv rewind`, `cv splice` and
`cv distill --session` write under `--out`; `cv distill --agent-of` and `cv adopt` write into
`~/.claude/projects`, which is what makes a result resumable by `SendMessage`.

**Unknown.** Whether a sharpened veteran, resumed, behaves like the original: thinking is dropped and
cannot be scored, and the recall proxy credits a sha or a path, not the reason it matters.

## 3. Promote and develop

**The seat lines are expert contexts by name, not by context.** fn's eight seat lines (A runtime
contract, B integrator, C spans, D burndown, L log, M memory equation, O OVER, P POST) route work to a
subsystem owner, as sub-question 3 proposes. Each line was 8 to 28 separate contexts in five days,
and the expertise travelled in continuation files (43% carriage) and in Codex worker sessions.

**Where durable contexts did form**:
- Codex workers, resumed by session id with a delta prompt ("Seat P8 (succeeds P7). Your last turn
  ended on ..."), across up to six seats; at least 10 of 186 fn worker sessions over 300 kB since 10-09 span
  two or more seats (a lower bound: seats are recognized only when a prompt names one) (`evidence/data/codex-workers-fn-20261009-13.json`).
- The delvetalk objects lane a1387d82, resumed by message for four rounds of work (#982, #1103,
  #1224, #1849) to 976K, then succeeded.
- The fn coordinator, carried across six sessions by fork and prune; the context ember repeatedly
  asked to be re-oriented "with cv" after each swap (AUDIT-TWO-WEEKS §d).

**Why designed expert contexts did not survive.** A sub-agent is resumable only from its parent
session. Every parent restart, prune-and-fork or abeyance ended every seat at once (8 mass respawns,
AUDIT-TWO-WEEKS §d), and the breadstuffs standing lanes were replaced the same way at their
parent-session change. The fix exists (`cv adopt`)
and has not entered practice.

**Lifecycle, as practiced**: birth by spawn with a continuation file; a life of a median 2.6 hours
and 218 API requests to a 350K park; retirement by the park rule, never by a measure of drift or expertise; no instrument for
either. **Not measured anywhere**: whether a routed expert context makes fewer errors in its
subsystem than a successor would. The practices in `docs/practices.md` start that measurement.
