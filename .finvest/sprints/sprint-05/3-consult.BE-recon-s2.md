# Consult BE-recon-s2 (owners: sa, ai)

## Question
Acceptance says: "FPT 2026-09-18 S2 close equals V2 65,182.47 -> 0 mismatches between the two sources on that date".
The fixture `ssi/history/FPT-1d.json.gz` has c = 65.18 (thousand VND, 2 decimals) for 2026-09-18, i.e. **65,180 VND**,
while V2 stores 65,182 (rounded from 65,182.47). S2 only has 10 VND resolution.

`reconcile()` (finvest_analytics/adjust/recon.py) requires **exact equality when G == 1** (`UNIT_OR_ADAPTER` if diff != 0),
and only applies the 0.1 % threshold when G != 1. So every S2 day with a rounding gap of 1..9 VND on a name with no
ex-date after that day is reported as a mismatch: S2 cross-check would be mostly noise, and the acceptance cannot pass.

## Options
1. AI changes `reconcile` with a `slack_vnd` parameter (e.g. 10 for S2): diff <= slack counts as equal in the G == 1 branch. BE passes it for `ssi`. (Recommended; domain rule belongs in the analytics package, outside my file set.)
2. BE filters S2 mismatches itself with a 10 VND slack after the call (my file set only; but duplicates the rule and the diff_pct/note live in the result).
3. Change the acceptance to "S2 within 10 VND" and leave reconcile exact (noise stays).

## State
Implementation is built and pushed on task/sprint-05/BE-recon-s2 (`--cross-check ssi`, `_cross_check` in feeds/recon.py, SourceBlocked stops it, summary "... | vci: k, ssi: m mismatches"). Tests not yet written; they wait for the answer on the slack.
