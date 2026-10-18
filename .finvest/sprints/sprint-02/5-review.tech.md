# 5-review.tech — sprint-02 (fi-software-architect, 2026-10-18)

Reviewed: origin/sprint-02 50dce14 against `4-test.be.md` (RED), the sprint-02 task blocks and platform.md §4 / data.md §1.2.
**Verdict: FAIL — 2 build bugs, both root-caused to a wrong assumption in my contract/plan (tagged `arch`), fixed by
FIX-ticks-probe and FIX-index-value, folded into sprint-03 (dag rev 4). No sprint-02 code is rolled back.**

## 1. Per task

| Task | Verdict | Finding (owner) |
|---|---|---|
| QA-S01-tests, OPS-host-user, BE-calendar, S-index-members, BE-symbols-feed, BE-symbols-enrich | PASS | — ; root-owned `FI_ROOT/data/raw` still needs the documented `sudo chown` (OPS-cleanup-1015, sponsor) |
| BE-status-no-trades | **FAIL** | B1 — `feeds/ticks.py:97-103` reads an empty tape on `trading_date < today` as "source moved on". The rule came from platform.md §4 v1.3 ("K1 serves the current session only, so a past-day empty tape is conclusive"), which was an **uncited assumption** (retro R3): the live 10-16 re-run shows K1 still serving two days later while A32, the first sorted name, legitimately had no trades. Owner: `arch` (contract) + `build` (fix). |
| BE-scheduler (catch-up) | PASS as built, **blocked by B1** | see §2: every catch-up of a past day hits B1. |
| BE-bars-store | **FAIL** | B2 — `adapters/vci/source.py:_rows` applies ×1e6 to every `accumulatedValue`; data.md §1.2 V2 said "million VND" from one 2026 fixture. Live VN30 history is raw VND until ~2024 → 2.2e17 VND → `NumericValueOutOfRange` on `index_1d.value BIGINT`. Owner: `arch` (data.md) + `build`. |
| BE-bars-backfill | **FAIL (consequence of B2)** | the index upsert raises outside the per-name `except`, the whole run ends `failed` after 21 min of good stock work (rows are committed, so nothing is lost), no `crawl_sessions` row, no summary/coverage line → G2 cannot be judged. VNINDEX/VN30 have 0 bars → **blocks sprint-03 F-048 (AI-whatif-benchmarks) live acceptance**. |

## 2. Does B1 hit the timer `catchup` path? Yes — for every past day, not for the same-day runs.
`catchup()` (feeds/catchup.py) walks `trading_days(last_session_date, end)` with `end = today` after 15:05, else yesterday;
`run_ticks` sets `today = now_vn.date()`.
- 15:30 and 20:00 runs on a trading day T, T-1 `complete`: only T is run, `trading_date == today` → empty tapes are
  `no_trades`. **Not hit.** C1–C5 manual crawls at 21:00 the same day: not hit either.
- `Persistent=true` replay after the machine was off at 15:30 and 20:00 of T (boot the morning after, before 15:05):
  `end = T`, `trading_date = T < today` → A32 is empty → `missed` after 1 request, 0 rows, and `upsert_crawl_session`
  writes `missed` — which `catchup` then skips **forever** (`session_status in ("complete","missed")`). The ticks of T
  are never fetched although K1 would still have served them (10-16 was served on 10-18). **Hit: nightly tick loss for
  exactly the case the catch-up exists for (ADR-S-009 "machine off").**
- T-1 ended `partial`/`blocked` (e.g. 20:00 retry blocked): the next 15:30 run re-walks T-1 → `missed`, and the
  on-conflict update **overwrites** the partial session row (rows → 0, checksum → empty, fetched → 0); the tick rows
  stay in `ticks`, the audit record is corrupted and terminal. **Hit.**
- Manual recovery `make crawl DATE=<past>` hits B1 identically, so today there is no recovery path at all for a past day.
Until FIX-ticks-probe is merged the SM must keep C1–C5 strictly same-day (before midnight VN); a day missed by both
timer runs and not crawled before midnight is lost.

## 3. Per contract
| Contract | Verdict | Change made (archived first) |
|---|---|---|
| platform.md §4 past-date rule | FAIL (v1.5) → fixed in **v1.6** (`platform.prev-6.md`) | other-session tape stays conclusive; empty tape never is; past day = probe `FPT, HPG, VNM` first, all empty → `missed` (≤ 3 requests), else empty = `no_trades`. |
| platform.md §4 bars canonical line / `value` | FAIL → **v1.6** | `accumulatedValue` is mixed-unit: stocks pick ×1 vs ×1e6 by closeness to `v × c`; indices `≥ 1e9` = VND; non-BIGINT → NULL + warning. |
| data.md §1.2 V2 | FAIL → **v1.2** (`data.prev-1.md`) | unit line corrected with the two live values. |
| data.md §3 `index_1d`, `bars_1d_src` | PASS | BIGINT is right once the unit is; no migration. |

## 4. Other findings
- B3 (`adj_*` vs F-012 C9 "nominal"): **intended**. `bars_1d_src` is the source-adjusted layer (data.md §1.2 V2 "prices are
  source-adjusted", §3 `bars_1d.nominal_kind observed|reconstructed`); nominal history is reconstructed by F-014/F-015 and
  the backlog honesty rule flags results `approximate` until then. C9 is met by the design, not by this table. PM: reword
  C9 to "all years the source provides, in VND; nominal via F-014" (tag `pm`).
- `value` NULL on 80 % of rows: V2 `accumulatedValue` is null on old bars (payloads.py:49, live 10-16). Expected; the
  ratio check in FIX-index-value acceptance tells unit bugs from nulls. Tag `data`, no task.
- B4 shared `finvest_test` DB migrated under the tester: tests must use a per-branch DB name (`FINVEST_TEST_DB` default
  `finvest_test_<branch>`); small, tag `ops`, folded into the next OPS task — not blocking.
- bars_1d `_run`: a DB error for one name ends the run `failed` with no summary even though rows are committed. Acceptable
  for now (per-name commit = no data loss); FIX-index-value removes the trigger. Tag `build`, no task.
- `upsert_crawl_session` lets a later `missed` overwrite a `partial` row; FIX-ticks-probe adds the guard (a `missed`
  manifest never overwrites a stored `partial`/`complete`).

## 5. Fix tasks (sprint-03 2-tech-plan.md, dag rev 4)
- **FIX-ticks-probe** (B1, ~120 lines, Effort high, Lead opus) — start now; no `after`.
- **FIX-index-value** (B2, ~110 lines, Effort high, Lead opus) — start now; `AI-whatif-benchmarks` now `after` it so the
  F-048 live acceptance has VNINDEX bars; re-run `make backfill` from archive (0 live requests, ~20 min) is part of the task.
Sprint-02 stories S02-3 (re-crawl 10-16) and F-012 index coverage are re-tested by the BE tester on sprint-03 after both
merge.
