# evidence/scripts

The one-off analyses behind `evidence/*.md`. They are not instruments (those are in `tools/`): they
run from a scratch directory that holds the caches they build, and they read transcripts only.

- `fetch_seats.py` builds `seats.json` (the fn seat lines from `cv lanes <root> --json` of the five
  coordinator roots, saved as `lanes/<root>.json`) and caches each seat's IR as `ir/<agent>.json`
  with `cv show <root> --agent <id> --json`.
- `seat_orient2.py` runs `tools/orientation_cost.py` over every seat; `endcause.py` classifies how
  each seat ended; `succession_causes.py` classifies each succession's cause.
- `misroute.py`, `deadwakes.py`, `parkctx.py`, `resumes.py`: messages to parked or superseded seats,
  and resumes after a park.
- `codex_seats.py`: Codex worker sessions in fn lanes and the Opus seats that resumed them.
- `briefscan2.py`, `xproj.py`: successor briefs in every project, and their orientation cost.
- `recall_batch.py` (with `context_extract.py`): `tools/carry_recall.py` over 15 consecutive seat pairs.
- `find.py`, `narr.py`, `early_disc.py`, `stale_scan.py`, `selfcorr.py`, `rereads.py`: reading aids
  used to find the cited messages.
