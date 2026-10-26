# 3-pr BE-ca-repo

## Round 1 (fi-tech-lead, BE, 2026-10-26) — APPROVE

Reviewed head H = `0a440c1b24a9b991498f2a06eb1e4023facffe43` (a589ae2 + sync merge of origin/sprint-05 f6a6c67, clean, no conflicts;
BE-v5-adapter is now in sprint-05 so the diff is the task's own two files).

Files reviewed: `packages/market_data/finvest_market_data/infrastructure/repositories.py` (+115/-2),
`packages/market_data/tests/test_repositories_db.py` (+64/-2). Size 179/-4 vs plan ~160 (stop 240): OK, no consult needed.

Checklist
- Plan / file set: exactly the two planned files; all 11 functions the card names are present.
- Contract (data.md §3): column names/types match `corporate_actions`, `corporate_action_log(field, old, new TEXT)`, `adj_factors.factor NUMERIC(20,12)`,
  `recon_mismatches`, `symbols.ca_checked_at`; press order VN30 current (`valid_to IS NULL`) -> scenarios -> `ca_checked_at NULLS FIRST, symbol`, delisted out.
- Correctness: all CA money/ratio fields are int (VND) in both dataclass and table, so `!=` and `str()` compare without spurious logs; factor goes
  `Decimal(str)` -> NUMERIC, never float. Upsert is idempotent (re-run writes no log; only `fetched_at` moves). `LIMIT NULL` = no limit in PG.
  `corporate_actions_for` positional constructor matches the dataclass field order (proved by the round-trip assert `== [moved]`).
- Tests: every acceptance item has a db test that fails without the change (diff log 05->07 one row + re-run none; order
  `[VN30M, SCEN, NULLS, OLD, NEW]` incl. VN30/scenario names with a newer `ca_checked_at` still first, delisted absent, limit=2;
  factor `0.980000000000` text + Decimal round trip; recon twice -> 1 row; newest_src_bars picks newest fetched_at per date).
- Layering: lint-imports 5 kept / 0 broken; no new dependency (`distinct_on` is SQLAlchemy 2.1.4 already installed).
- Security: only bound parameters (`:n`, SQLAlchemy core); no secrets.

Must-fix: none.

Nits (no action required)
1. `replace_recon_mismatches` stamps `checked_at = now()` (transaction time); fine for now, pass a time if the recon job ever needs one stamp per run across transactions.
2. `ca_symbols_in_order` plain-SQL read of api-owned `scenarios` carries the planned `# shortcut:` comment — keep it visible in the debt ledger.

Checks on H (q.sh)
- db (`-m db`, per-branch db finvest_be_ca_repo_test): `36 passed, 297 deselected` in 13 s.
- side kernel `make test-kernel`: `297 passed, 36 deselected`; ruff all checks passed; mypy no issues (5 files); lint-imports 5 kept / 0 broken.

Merged: `ec4275adfe4229df17c9cae248cb467976978368` into sprint-05 (base f6a6c67). Worktree removed.
