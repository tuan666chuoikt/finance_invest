# 3-pr BE-rw-ledger-rank (round 1, lead)

**APPROVE** — reviewed head cc016a6cf40861bf6eb4d20261724aa19c538f65 (task head ab23b9c + chore(merge) sync of origin/sprint-04).

Files reviewed: packages/market_data/finvest_market_data/infrastructure/repositories.py, packages/market_data/tests/test_repositories_db.py. Size: 2 files, +19/-2 (plan ~25, within 1.5x). No schema/migration, no secrets, no new dependency.
Contract: rank complete=3, partial=2, blocked=2, missed=1, else 0 as a SQLAlchemy case() on both sides; where = rows >= stored AND rank(new) >= rank(stored), exactly as the task card.

Must-fix: none.
Nits (no action):
- A lower-rank row with more rows (blocked 10_357 over complete 4_949) is now rejected; the reverse (complete with fewer rows over a richer blocked row) is still rejected by the rows clause. That is the card's stated semantics; the existing 10-23 row is repaired only by a complete press with >= rows (out of scope per card).
- _status_rank has no type hints (mypy passes).

Checks (synced head, db = throwaway finvest_leadrank_test, dropped after):
- make test-kernel: 259 passed, ruff clean, mypy ok, lint-imports ok.
- pytest -m db test_repositories_db.py: 22 passed; full -m db: 27 passed.
- New test test_status_rank_is_never_lowered fails on the old repositories.py (AssertionError at line 160), passes on the new.
Merged into sprint-04: e5ac19f2c3e7ebf0189e2f1a35faa964f75e151c
