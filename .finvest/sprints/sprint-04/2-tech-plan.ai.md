# Sprint 04 — Tech plan (AI side: S04-RW notes AI-1…AI-3)

Owner: `fi-ai-architect`, 2026-10-25, plan v1. Inputs: `1-sprint-plan.md` (S04-RW, M2; AI-3 first to slip), `product/backlog.md`
S04-RW AI-1/AI-2/AI-3 + F-048 wording, `sprints/sprint-03/5-review.ai.md` notes 1–3, `contracts/analytics.md` v1.2 §2.4,
`architecture/analytics.md` **v1.2** (updated today: §1.3.1 `holding_days` display-only note = the doc half of AI-3;
v1.1 archived as `analytics.prev-2.md`). The software architect merges these two blocks into `dag.json`.

## Decisions

- **No contract change.** AI-2 needs to tell "ETF listed after N" from "gap inside N..M"; the web already has both dates
  (`result.dates.buy` and `benchmarks[].first_available`), so the rule lives in the card: `first_available > dates.buy` ⇒
  "data from <date>", `first_available ≤ dates.buy` ⇒ "missing in period", `null` ⇒ plain n/a. The engine's `_na` (benchmark.py)
  and `contracts/analytics.md` §2.4 stay as they are. A `reason` field in the contract would cost a v1.3 + platform.md mirror +
  TS types for the same three strings.
- **AI-1 and AI-3 share one task** (same file `whatif.py`, together < 30 lines). AI-3's code half is a 2-line comment, so it can
  no longer slip on its own — it costs nothing to keep. The doc half is already done (analytics.md v1.2).
- `Lead: sonnet`, `Effort: medium` for both: no money arithmetic changes; the curve fix is a loop guard whose result the golden
  values already pin (001–010 unchanged is the regression proof).
- Sizes count prod + test. Total AI side ≈ 65 lines over 2 tasks; both in the S04-RW parallel lane, milestone M2, no `after`
  (file sets disjoint from F-129…F-132, which touch CSS/shell files only — the software architect confirms against his blocks;
  `ScenarioCard.tsx` is also in F-131's set ⇒ order `AI-rw-bench-na` **before** F-131's card task or after it, never parallel).

## Tasks

#### AI-rw-curve — S04-RW AI-1 + AI-3: curve loop starts at the first fill; `holding_days` marked display-only
- Story: S04-RW ; Side: ai ; Effort: medium ; Size: ~25 lines ; Lead: sonnet
- Files: `services/analytics/finvest_analytics/sim/whatif.py`, `services/analytics/tests/test_whatif_lumpsum.py`
- Change:
  - In the curve loop (`curve, missing, last_close, i = [], [], rows[0]["price"], -1`): replace `i = -1` with `i = 0` and add
    before the loop `assert rows and rows[0]["date"] == n, "first calendar day must be the first fill"` — `n` is the shifted
    buy date (a bar day) and `view.calendar(n, m)` starts there, so `states[0]` is the right state on day 1 and `states[-1]` can
    never be read through a negative index. Keep the `while i + 1 < len(rows) and rows[i + 1]["date"] <= d: i += 1` advance.
  - Above `holding_days=days,` add a 2-line comment: `# holding_days is display-only (first fill -> valuation); feeds cagr for
    lump_sum only. XIRR must use contributions[].date, never this (analytics.md §1.3.1).`
  - Test (lumpsum file, reuse its fixture view): `equity_curve[0].date == result.dates.buy` and `equity_curve[0].market_value
    == position.cash + position.shares × close(buy)`; for golden 001 that is `635_975 + 100 × 93_500 = 9_985_975` on the buy day.
    One more: a DCA result (`test_whatif_dca.py` fixture) has `equity_curve[0].invested == contributions[0].amount_vnd`
    (the step line starts at the first contribution, not at the last state).
- Contract: contracts/analytics.md §2.4 `equity_curve` ("every trading day in [buy, sell]", `invested` cumulative), `returns.holding_days`;
  architecture/analytics.md v1.2 §1.3.1 (display-only note).
- Acceptance: `pytest services/analytics` green with the two new asserts; goldens 001–010 unchanged (no `hand` edit); the
  `i = -1` literal no longer exists in `whatif.py` (`rg -n 'i = -1' …` empty).
- Out of scope: XIRR itself (F-047), any change to `cagr`, `dates.py`, `benchmark.py`, the golden JSON files.

#### AI-rw-bench-na — S04-RW AI-2 (F-048 wording): "missing in period" vs "data from <date>" on the benchmark n/a line
- Story: S04-RW ; Side: fe ; Effort: medium ; Size: ~40 lines ; Lead: sonnet
- Files: `apps/web/src/features/scenarios/ScenarioCard.tsx`, `apps/web/src/features/scenarios/ScenarioCard.test.tsx`,
  `apps/web/src/i18n/vi.json`, `apps/web/src/i18n/en.json`
- Change:
  - `Bench` takes a second prop `buy: string` (ISO, from `r.dates.buy` at the call site, line ~83). Branch when `!b.available`:
    `b.first_available === null` → `card.bench_na_nodate` (unchanged); `b.first_available > buy` (ISO strings compare
    lexicographically) → `card.bench_na` (unchanged, "data from <date>" case: the benchmark listed after N);
    otherwise → new key `card.bench_na_gap`.
  - New i18n keys, both files: vi `"card.bench_na_gap": "{{name}} — n/a: thiếu dữ liệu trong kỳ"`, en `"{{name}} — n/a: data missing
    in period"` (backlog S04-RW AI-2 / F-048 R4-2 wording; `{{name}}` because VN-Index can hit the same branch — `benchmark._na`
    gives it `min(bar dates in [buy, sell])`, which is ≤ buy whenever the gap is inside the range).
  - Keep the two existing keys' text; no change to `ScenarioTable.tsx` (its cell stays the bare `n/a`, backlog line "the cell
    reads" is satisfied by the card line, which is the only place a date is shown) nor to `HowComputed.tsx`.
- Contract: contracts/analytics.md §2.4 `benchmarks[].first_available: string | null` (unchanged); product/backlog.md F-048 +
  S04-RW AI-2; product/ux/scenario-dashboard.md (card benchmark lines).
- Acceptance (vitest, `ScenarioCard.test.tsx`, fixture `envelope-001.json` with `dates.buy = 2026-10-14`-style value):
  - `first_available: "2014-10-06"` (< buy) → text matches `/E1VFVN30 — n\/a: thiếu dữ liệu trong kỳ/` and contains **no** date;
    the existing test "unavailable shows n/a + date" must be updated to use a `first_available` **after** `dates.buy`
    (e.g. buy + 1 day) so it keeps asserting the dated wording.
  - `first_available > dates.buy` → still "n/a: không có dữ liệu trước dd/mm/yyyy"; `null` → `/^VN-Index — n\/a$/` (existing).
  - `npm test` in `apps/web` green; no `0 %` ever rendered for an unavailable benchmark (existing assert kept).
- Out of scope: engine or contract fields, table cell wording, the visual restyle of the card (F-131 owns the CSS), i18n of
  other card strings.
