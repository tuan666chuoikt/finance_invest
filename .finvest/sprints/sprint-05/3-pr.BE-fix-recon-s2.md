# 3-pr BE-fix-recon-s2 round 1
APPROVE (head f2ee03c1fee64f66dbc4a3109b8153605939e393, synced with sprint-05 via merge f2ee03c)
Files reviewed: recon.py, cli.py, test_recon_feed.py (+19/-7, within 1.5x of ~25).
Must-fix: none. Contract data.md §3 source ssi_s2 honoured; self_check stays vci-only; S1 'ssi' reserved. Exit code 1 on missing|mismatches|ssi_mismatches.
Tests: S2 test asserts ssi_s2 row and 0 'ssi' rows; new exit 1/0 test fails without the change.
Checks: recon tests 13 passed; crawler suite 201 passed (db test, localhost:15433); ruff clean.
Merge sha 4d477105bff44abc51ea56f1db317d87bde945a2
