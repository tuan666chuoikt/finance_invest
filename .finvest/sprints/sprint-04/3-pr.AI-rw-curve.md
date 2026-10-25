# 3-pr AI-rw-curve round 1
Verdict: APPROVE. Head H=e52ed241db1e1a1c5100e8f1ba896f52a04f8099 (already contains origin/sprint-04 59cfc03; no sync needed).
Files reviewed: sim/whatif.py (i=0 + assert + holding_days comment), tests/test_whatif_lumpsum.py, tests/test_whatif_dca.py. Matches plan AI-rw-curve; size 17+/1- (plan ~25).
Tests: lumpsum curve[0]=buy day, 9_985_975 = 635_975+100*93_500 (hand-checked); DCA curve[0].invested == contributions[0].amount_vnd.
Checks: analytics pytest 42 passed; kernel (pytest -m "not db" 259 passed, ruff, mypy, lint-imports) green. No db paths touched.
Nits: assert follows the rows[0] use on the preceding line (harmless). DCA test file is outside plan file list but plan names its fixture.
Re-sync (base moved to 7ed8cb8 after FE-tokens): chore(merge) 0013eeb, only apps/web files came in; kernel re-run green. Reviewed head H=0013eebc807f37c5dab61fdc36cef07e2c0dfafa.
Merged: 80c8247a33cc9586d98c093fa79fada5bfbe9272
