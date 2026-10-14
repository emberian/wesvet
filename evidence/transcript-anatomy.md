# Transcript anatomy of eight long veterans (2026-10-13)

What a 770K to 980K transcript is made of, as evidence for what a prune may remove and what it may
not. Instruments: `cv doctor <id> --json` (token attribution, compactions), `tools/anatomy.py`
(byte buckets, below), hand-marked dead ends for one transcript, and the self-cut test of
`tools/sharpen.py` (section 5). Data: `evidence/data/anatomy/` (one `*.anatomy.json` and one
`doctor_*.json` per transcript). Command for each: `tools/anatomy.py <ir.json> --json` over
`cv show <root> --agent <id> --json`.

## 1. The transcripts

| name | project, role | agent (root) | span (UTC) | messages | peak context | API requests | tokens |
|---|---|---|---|---|---|---|---|
| fn_A1 | fn, Builder A (runtime contract proofs) | a2858c6e (35f3668a) | 10-09 06:42-08:33 | 2,067 | 791K | 500 | 243M |
| fn_B1 | fn, Builder B (integrator, trains 61-67) | a07c5a47 (35f3668a) | 10-09 06:42-13:07 | 2,113 | 838K | 555 | 288M |
| fn_C1 | fn, Builder C (spans generator proofs) | ae2f9782 (35f3668a) | 10-09 07:18-09:12 | 1,977 | 787K | 470 | 228M |
| fn_M20 | fn, Builder M (L-RUN-LAUNCH), died at the weekly wall | a44f7f78 (905fe751) | 10-11 17:45-23:02 | 2,125 | 918K | 555 | 297M |
| fn_coord | fn coordinator main thread (forked; 473K inherited) | 4a22422c | 10-09 09:51-10-10 14:28 | 4,684 | 976K | 846 | 585M |
| delvetalk_objects | delvetalk objects lane, resumed by message for 4 rounds | a1387d82 (81183e86) | 10-10 00:29-03:24 | 1,901 | 976K | 504 | 289M |
| dclutch_spine2 | dragons-clutch SPINE-2 | a103dbc3 (e9d68d2f) | 08-29 12:39-23:33 | 2,032 | 974K | 678 | 413M |
| bread_mergekeeper | breadstuffs Mini swarm merge-keeper | a6ac8c6c (ce776c01) | 10-07 00:47-18:17 | 2,174 | 769K | 531 | 235M |

None of the eight was ever compacted (`cv doctor`: "never compacted"; `autoCompactEnabled false`).
Each is one uninterrupted context, so its transcript is what a resume would reload.

## 2. What the context is made of, in tokens (`cv doctor`)

| source | fn_A1 | fn_B1 | fn_C1 | fn_M20 | fn_coord | delvetalk | dclutch | bread |
|---|---|---|---|---|---|---|---|---|
| thinking | 41% | 31% | 40% | 36% | 27% | 33% | 38% | 26% |
| tool results | 24% | 42% | 25% | 40% | 6% | 38% | 41% | 32% |
| tool-call arguments | 26% | 19% | 24% | 18% | 25% | 25% | 20% | 23% |
| system reminders (notifications, queued messages) | 8% | 6% | 9% | 6% | 26% | 4% | 0% | 19% |
| assistant text | 1% | 1% | 1% | 0% (93 tokens) | 6% | 1% | 1% | 0% |
| user text | 0% | 0% | 0% | 0% | 9% | 0% | 0% | 0% |
| fixed overhead per turn | 33K | 34K | 34K | 32K | 473K (fork) | 29K | 27K | 46K |

Thinking is a quarter to two fifths of every context. Claude Code stores it as an opaque signature
(the visible `thinking` text is empty), so no instrument here can say what in it mattered. The
agent's own prose is about 1% of a builder seat; M20 wrote 93 tokens of text in 918K.

## 3. What the bytes are made of, by prune relevance (`tools/anatomy.py`)

Each byte the model would reload goes in one bucket (definitions in `tools/anatomy.py`'s
docstring). "Unreferenced" means no distinctive token the output introduced (sha, path, `fn-`
name, run id, UPPER-CASE id, 5+ digit number) appears in anything the agent later wrote or ran.

| bucket group | fn_A1 | fn_B1 | fn_C1 | fn_M20 | fn_coord | delvetalk | dclutch | bread |
|---|---|---|---|---|---|---|---|---|
| waiting: harness notifications + poll calls | 9.5% | 8.4% | 12.6% | 7.4% | 26.2% | 3.1% | 3.5% | 14.0% |
| stale status: a status command run again later, superseded or identical re-reads | 5.9% | 3.2% | 3.8% | 6.4% | 0.3% | 5.4% | 9.0% | 3.7% |
| run/test output never used later | 1.4% | 3.4% | 1.6% | 3.4% | 0.8% | 6.4% | 3.6% | 5.3% |
| read output never used later | 7.6% | 11.6% | 6.9% | 11.2% | 0.3% | 16.2% | 8.3% | 6.0% |
| thinking signatures | 40.6% | 31.4% | 40.2% | 36.4% | 26.8% | 32.8% | 37.9% | 25.9% |
| read/run output used later | 4.3% | 18.9% | 5.9% | 13.3% | 0.3% | 4.2% | 16.9% | 9.3% |
| error output | 0.0% | 0.1% | 0.9% | 0.7% | 0.1% | 0.0% | 0.1% | 0.9% |
| state-changing calls, input and output (edits, commits, dispatches, messages) | 24.7% | 16.5% | 22.7% | 15.3% | 26.9% | 26.9% | 8.5% | 20.0% |
| other tool inputs | 4.3% | 4.8% | 3.6% | 5.5% | 1.5% | 3.5% | 10.8% | 5.4% |
| own words + messages received + brief | 1.6% | 1.7% | 1.8% | 0.4% | 16.8% | 1.5% | 1.3% | 9.4% |
| total bytes | 2.06 MB | 2.26 MB | 2.07 MB | 2.51 MB | 3.01 MB | 2.68 MB | 2.41 MB | 1.86 MB |

Counts:

| | fn_A1 | fn_B1 | fn_C1 | fn_M20 | fn_coord | delvetalk | dclutch | bread |
|---|---|---|---|---|---|---|---|---|
| tool calls | 504 | 553 | 469 | 559 | 671 | 507 | 694 | 560 |
| poll calls | 60 | 65 | 86 | 39 | 8 | 0 | 76 | 70 |
| harness notifications | 561 | 605 | 573 | 610 | 2,087 | 513 | 3 | 562 |
| messages received (coordinator, peers, human) | 4 | 14 | 4 | 5 | 312 | 14 | 3 | 127 |
| commits and pushes | 11 | 43 | 9 | 15 | 1 | 44 | 32 | 108 |
| edits | 202 | 53 | 171 | 120 | 229 | 176 | 78 | 36 |
| dispatches (codex exec, detached jobs, trains) | 3 | 49 | 1 | 7 | 6 | 0 | 6 | 24 |
| messages sent | 4 | 9 | 5 | 2 | 246 | 0 | 0 | 52 |

The coordinator is a different animal: a quarter of it is notifications (2,087 background-task
events), a sixth is what it was told and said, and almost none is tool output.

## 4. Dead ends, re-reads, corrections

**Re-reads inside a veteran are negligible.** Identical re-reads of a document (same path, same
range or command) total 0 to 6 kB per transcript, under 1% (`evidence/scripts/rereads.py`). Re-reading
is a succession phenomenon (a successor reads what its predecessor read), not a veteran one.

**Dead ends, marked by hand in fn_C1** (proof engineering; the five spans below, read from the
narrative `#index` lines):

| span | messages | share of bytes | what happened |
|---|---|---|---|
| #370-#412 | 42 | 0.7% | a 58 s foreground timeout cut a send and killed the REPL session; restart. Lesson stated at #382: "in the background this time" |
| #847-#887 | 40 | 1.7% | a proof route abandoned for "a cleaner route" (#887) |
| #1065-#1083 | 18 | 1.4% | the same foreground-timeout session death again: "From here, any send that can run long goes in the background" (#1065) |
| #1256-#1301 | 45 | 1.7% | a wedged client; killing it took the session; restart (#1272) |
| #1844-#1931 | 87 | 3.4% | a raw-mode timing driver misused the live stobj; redone through ACL2 (#1844, #1931) |
| total | 232 of 1,977 | 8.9% | |

The veteran repeated its own dead end: the lesson from #382 did not hold at #1065, although both
were in its context. Keeping a failure in the transcript did not make it a rule; stating it as one
did (#1065, and no third occurrence).

**Lessons that became artifacts.** In fn_B1 the coordinator's correction "you were finding reds one
certify submit at a time" (acknowledged at #1703) became the read-ahead script
(`build/coordinator/tools-builder-b/readahead.sh`), which B1's continuation names. Once a lesson is
a file, the dead end that taught it carries nothing a prune must keep.

**Corrections received.** Builder seats received 4 to 14 messages in their whole life; the merge
keeper 127; the coordinator 312 seat messages and 11 human prompts in its own span (4a22422c from
#2098). The human prompts are 4.1 kB of a 3 MB transcript and include the one that should have
prevented five successions: "i hadta restart the harness for pruning & upgrades, mind sendmsg those
running agents to resume em? :)" (4a22422c#2098), answered "The harness restart killed every
in-process seat (A4, B6, C6, D3, M3) ... respawning each from its own file" (#2115). `cv adopt`
shipped the next day (cv e34a52f8, 10-10 23:02 UTC) and no fn coordinator transcript after it uses
it, through three more restarts.

## 5. The prune, tested against the veteran's own future

`tools/sharpen.py --cut 500` sharpens fn seat P7 (a28ab660, 848 messages) as it stood at message
500; `tools/carry_recall.py --self --cut 500` scores each pack by the share of tokens P7 wrote after
message 500 that occur before it (142 such tokens, after removing SEAT-COMMON and COORDINATION.md's).
Outputs: `evidence/prune/a28ab66086a4f8c66.cut500.*`, `evidence/prune/p7-selfcut500-recall.json`.

| pack (P7 at message 500, recorded context 269K) | est. context | recall | weighted | what it missed |
|---|---|---|---|---|
| `cv distill --upto 500` | 43K | 0.62 | 0.67 | the rely, the runtime-contract request names, the reachability predicate (all from book and survey reads), `/proc/loadavg` (the box-load check) |
| sharpen profile 1 (drop every never-used output) | 173K | 0.94 | 0.94 | `fn-rtc-requests`, `fn-ptx-kd-of` (book reads not yet quoted at the cut), `TS-DONE` |
| sharpen profile 2 (keep document and source reads) | 213K | 0.986 | 0.984 | `TS-DONE` (a status line inside an unreferenced run), one worktree path |
| the full prefix | 269K | 1.00 | 1.00 | |

The first version of profile 1 scored 0.89: its "status command run again later" rule keyed on the
leading `cd DIR`, so different reads in one repo looked like repeats, and a second range of the same
book (`sed -n 1,32p` then `sed -n 95,236p`) looked like a repeat of the first. Both are fixed in
`anatomy.norm_cmd` and `sharpen.is_doc_read`. "Used later" is only known up to the cut, so a prune
taken at a park cannot know which document reads the next task needs: that is why profile 2 keeps
them.

## 6. What a prune may remove, and what it may not

May remove, on this evidence (low risk; 15% to 30% of a seat's bytes):
- harness notifications and poll-call outputs before the tail (3% to 14% of a seat, 26% of the
  coordinator);
- all but the last output of a repeated status command (3% to 9%);
- run and test outputs whose introduced tokens are never used again (1% to 6%);
- identical re-reads (under 1%).

May remove only with retrieval kept (`cv cat`), at measured cost:
- read outputs never used later (7% to 16%): dropping them cost the P7 self-cut 5 points of recall;
- thinking older than the tail (26% to 41% of tokens): the single largest lever, and the one no
  instrument here can evaluate, because the text is not stored.

Must not remove:
- the brief, every message received, and the agent's own words (1% to 2% of a seat): small, and the
  only place corrections and rulings live;
- state-changing calls, inputs and outputs (9% to 27%): the record of what was done, including the
  Codex briefs a seat writes as heredocs;
- outputs the agent later used (4% to 19%);
- error outputs (under 1%), and dead ends unless their lesson has been written down as a rule or a
  file. The fn_C1 repeat shows a dead end left in context does not by itself teach.
