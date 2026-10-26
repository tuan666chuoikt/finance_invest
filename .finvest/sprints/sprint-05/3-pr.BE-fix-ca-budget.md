# 3-pr BE-fix-ca-budget round 1
CHANGES_REQUIRED (head ccd8c58fbbbc47deb05b80e370b56524213c8e9f, synced with sprint-05 via clean merge ccd8c58)
Files reviewed: settings.py, repositories.py (ca_symbols_in_order), test_feed_corporate_actions.py, test_repositories_db.py (+11/-8, within 1.5x of ~30). Contract data.md 1.2 V5 v1.8 honoured: budget 28, ORDER BY tier, ca_checked_at NULLS FIRST, symbol; test fails without the change (VN30N NULL first).
Must-fix:
1. packages/market_data/tests/test_repositories_db.py:414 ruff E501 (126 > 110) from the trailing comment; `ruff check .` is part of make test-kernel. Shorten/move the comment; proof: `ruff check services packages` exit 0.
Nits: none.
Checks: db tests (test-be db, throwaway db) 31 passed; kernel `-m "not db"` 340 passed, 1 failed (apps/api test_jobs test_step_2_target_is_decided_after_step_1[15-2026-10-23]: passes 3x alone, unrelated to the diff, flake under full run); lint-imports ok; ruff 1 error (above).

# round 2
APPROVE (head d9620e3e27b91b927422b8de8d27c3a74b7c1fe4, already synced with sprint-05)
Must-fix 1 resolved: comment on its own line; `ruff check services packages` exit 0. Diff since round 1 is only that comment; round-1 db (31 passed) and kernel results stand. Re-run: crawler 176 passed, 25 skipped; lint-imports ok.
Merge sha 2f5c6b7247d16eb36b63d1bb0a53383c8a2de6a4
