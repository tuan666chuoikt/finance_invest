# 3-pr BE-v5-adapter (F-014)

## Round 1 — 2026-10-26, fi-tech-lead (BE, sonnet) — CHANGES_REQUIRED

Reviewed head H = f223cc5 (f7ede20 + sync merge of origin/sprint-05 0950502, no conflicts; pushed by the dev branch, merge commit local to the worktree, see below).
Size: 5 files, +258/-0 (fixture 1 line) = 257 lines vs plan ~150, stop 225 (1.5x). No `3-consult.BE-v5-adapter.md`. Source 144 lines
(events.py 95, payloads.py 30, models.py 19) is on the estimate; the 113-line test file is the overage.

Files reviewed: `services/crawler/finvest_crawler/adapters/vci/events.py`, `.../vci/payloads.py`,
`packages/market_data/finvest_market_data/domain/models.py`, `services/crawler/tests/test_adapter_vci_events.py`, fixture `FPT-2026.json` (copy of spike v5-call4).

Review of the code itself: no findings. Mapping matches the card (data.md V5, VN§6): DIV+valuePerShare -> cash int(1000); title fallback -> stock_dividend;
ISS thuong -> stock_dividend; CBCNV/ESOP -> listing_change; quyen mua/phat hanh them -> rights with price regex (10,000 / 10.000 / 15000); else unmapped.
Hand check of ratios: r = b/a, Fraction(0.1)=1/10 -> 10:1; 0.15 = 3/20 -> 20:3; 0.2 -> 5:1; matches VN§6 "holder of a shares gets b new". Dates are date-only,
`toDate = run_date+400d` always in the URL (test: 20271130), a page is archived only after the shape parsed, 418 x3 -> SourceBlocked, `last` loop bounded (MAX_PAGES=40, `shortcut:` comment).
Each acceptance line has a test (fixture 4 rows; 15% title -> 20:3; neither -> NULL + anomaly; toDate in request; 418). Layering: lint-imports clean.
The 4 silent-card decisions in the build note are consistent with the card and data.md; accepted (no contract change).

### Must-fix
1. Size stop skipped (retro S01 R2): 257 lines > 225 and no consult. Fix without code change: write `SPRINT_DIR/3-consult.BE-v5-adapter.md`
   stating the overage (source 144 on estimate, tests 113 = 8 cases for the 4 mapping branches + fetch/418/archive) and ask the architect to confirm or waive;
   proof = that file exists and its answer is "waive" (or the tests are trimmed under 225 total). Then re-request review; no other change needed.

### Nits (optional)
- ESOP ratios are stored for `listing_change` as 741:1 / 200:1 (informational per the build note); the press step must never feed `listing_change` rows into `adj_factors`.
- `_ratio(r)` has no type annotation (mypy passes); `Settings.rate_per_s["vci_iq"]` is for BE-ca-step3 (noted in the build note).

### Checks on H (offline, `make test-kernel` via q.sh)
- kernel: exit 0 in 8 s; 268 passed, 28 deselected; ruff All checks passed; mypy no issues in 5 source files; lint-imports exit 0
- `-m db` not run: no migration, repository or SQL touched.

## Round 2 — 2026-10-26, fi-tech-lead (BE, sonnet) — APPROVE

Reviewed head H = 4cb33a6 (f7ede20 code unchanged since round 1; only sync merges of origin/sprint-05 f5bb4dd, no conflicts). Diff vs sprint-05: 5 files, +258/-0.
Must-fix 1 (size stop) resolved: `3-consult.BE-v5-adapter.md` exists, architect answer = waive (`3-consult.BE-v5-adapter.answer.sa.md`); plan block re-estimated to ~260, dag.json size 260.
No new findings; round-1 code review stands. Nits from round 1 carried to BE-ca-step3 (`listing_change` never feeds `adj_factors`).
Checks on H: `make test-kernel` via q.sh exit 0 in 8 s: 268 passed, 28 deselected; ruff clean; mypy no issues in 5 source files; lint-imports 5 kept, 0 broken. `-m db` not needed (no migration/repository/SQL).
Merged into sprint-05: 7c8087b.
