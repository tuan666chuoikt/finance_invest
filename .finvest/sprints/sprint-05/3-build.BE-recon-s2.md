# 3-build BE-recon-s2 (F-016, S2 cross-check as second `theirs`)
Files: services/crawler/finvest_crawler/{feeds/recon.py,cli.py}, tests/test_recon_feed.py.
`recon --cross-check ssi`: fetch S2 (archive-first, 1 req/s), store as bars_1d_src source='ssi', reconcile; first block stops it, local summary stands.

## Fix round 1 (review 3-pr round 1)
1. Merged origin/sprint-05 (chore(merge)) -> `self_check` param from AI-recon-xsrc.
2. `_compare` passes `self_check=(source == "vci")` (round-2 decision, no slack).
3. Tests added (test_recon_feed.py): FPT 2026-09-18 lands as 65,180 in bars_1d_src 'ssi', ours 65,182.73 -> 0 mismatches,
   reconcile called with self_check [True, False]; hand-broken close 65.28 -> 1 factor_or_event (0.149 % > 0.1 %);
   418 -> ssi_blocked, local summary kept, run status ok. Verified: with `self_check=True` forced, 2 of the 3 fail.
Checks: make test-db (db name finvest_be_recon_s2_test) 60 passed; test-kernel pytest 337 passed, mypy ok, lint-imports 5 kept,
ruff clean on services/crawler.
Not mine: ruff E501 at services/analytics/tests/test_recon.py:118 (from AI-recon-xsrc, already on sprint-05).
Test note: the worktree has no .env; I symlinked it temporarily for `make test-db` and removed it. Compose `db` runs as finvest-live-db-1.
