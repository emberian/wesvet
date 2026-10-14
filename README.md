# wesvet: veterans at the front

A study of the "veteran at the front" pattern in agent swarms (the Wesnoth rule: never park your
high-XP units), across every project transcript on this machine, with the aim of tools and practices
whose effectiveness we can later evaluate methodically.

## The question

An agent that has just built context (diagnosed a failure, read a subsystem, written a design) is the
most valuable unit we have, and the recurring failure is to let it exit, summarize lossily, and spawn a
fresh agent to implement from the summary. The fn swarm paid for this 157 times in five days (10-09 to
10-13): one landing went through seven consecutive seats in 38 hours, each re-orienting from a stale
continuation file. The one counter-example tonight: a two-week audit agent was sent back to build the
two files its findings implied, and did it without re-reading anything.

Three sub-questions:
1. **Resume, don't respawn.** When is `SendMessage` to a parked agent (full transcript intact) better
   than a successor from a continuation file, and when is it worse (context past the ceiling, compacted,
   poisoned by a long dead-end)? What does the orientation cost of a successor actually measure as?
2. **Prune the veteran.** A long transcript carries dead ends, polling turns, stale tool outputs. Can a
   transcript be pruned (`cv prune`, `cv distill`, `cv rewind`, `cv splice`) into a *sharper* veteran:
   the brief, every message it received, its own decisions and words, the commits, the last N turns as
   real turns, and nothing else? What must never be pruned (the user's corrections, the false starts
   that taught it something)?
3. **Promote and develop.** Can a veteran become an "expert context": a durable, resumable session for
   a subsystem (the runtime contract, the train tool, the memory equation) that successive tasks are
   routed *to*, rather than a fresh seat per task? What is the lifecycle: when is it retired, how is it
   kept from drifting, how is its expertise measured?

## Method

- Corpus: every session `cv ls` discovers (claude, codex, and the rest), across all projects.
- Instrument first, then intervene: measure orientation cost (tokens and wall-clock to first
  state-changing command), succession count per landing, re-read volume, and outcome, before proposing
  any tool. `cv lanes`, `cv deferrals`, `cv doctor`, `cv stats`, `cv tools` are the starting
  instruments; what they cannot measure gets a new one here.
- Every practice proposed here states its own evaluation: what we would measure, on which sessions,
  and what result would refute it.

## Layout

- `docs/` findings and practices, present-state, rewritten whole.
- `tools/` instruments and prunes, each with a README stating what it measures and its known limits.
- `evidence/` raw measurements, dated, with the command that produced each.

## Where it stands (2026-10-13)

- `evidence/successions.md`: 156 fn seat successions and samples from eight other projects, measured.
- `evidence/transcript-anatomy.md`: eight long veterans, and the prune tested against one's future.
- `docs/findings.md`: the answers to the three sub-questions, on that evidence.
- `docs/practices.md`: six practices, each with its evaluation and cost.
- `docs/evaluation-plan.md`: the two-week fn trial, metrics fixed in advance.
- `tools/`: `orientation_cost.py`, `anatomy.py`, `carry_recall.py`, `seat_report.py`, and the
  `sharpen.py` prune profile; `tools/README.md` says what each measures and its limits.
