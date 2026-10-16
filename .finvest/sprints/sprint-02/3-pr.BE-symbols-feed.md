# 3-pr BE-symbols-feed

# 3-pr BE-symbols-feed, round 1 (lead)
Verdict: APPROVE. Reviewed head H=db5c5b4b978b245e8dae2c472b24a68e870971cd.
Synced with origin/sprint-02 (clean merge, no conflicts). Shortstat 400+/18- over 14 files incl. tests; 241 non-test lines vs plan ~230 (limit 345), no consult needed.

Files reviewed: 0003_symbols.py, models.py, ports.py, tables.py, repositories.py, vci/source.py, kbs/ssi source.py (signature only), cli.py, feeds/symbols.py, and the 4 test files.
- Contract: symbols columns/CHECKs match data.md §3; delisted_at COALESCE never cleared; empty payload does not delist; one crawl_runs row, shared getAll archive (ADR-S-008); exit 2 on SourceBlocked.
- Outside-set edits (ports.py, kbs, ssi: optional kwarg) are needed by the port call and backward compatible; accepted. codebase.md §3 `symbols(self)` is stale: architect to update at review.
- Tests: rerun identical + requests 1 then 0, vanished -> is_delisted/delisted_at/row count, relisted anomaly, check constraints, migration round trip, blocked, CLI exit code.
- No look-ahead, no secrets, no SQL string building, no new dependency.

Must-fix: none.
Nits: (1) `parse_symbols` BOARD.get(..., "UPCOM") placeholder is documented; fine. (2) live docker run `docker compose run --rm crawler symbols` still to be done after merge (image rebuild), per 3-build deviation.

Checks on synced head: make test-kernel 116 passed, 13 deselected, ruff clean, mypy clean (5 files), import-linter 4 kept 0 broken; pytest -m db on finvest_test 13 passed.
Merge sha: 2e6356197503856dc716e90bbb172699d576ffb9
