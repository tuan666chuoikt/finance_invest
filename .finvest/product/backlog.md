# Finvest — Product backlog

Owner: `fi-pm`. Source: `product/prd.md` (Approved v2, 2026-10-15), `product/sponsor-answers.md` (A1–A15),
`knowledge/vn-market.md` (cited VN§n). Roadmap and velocity: `product/roadmap.md`. UX specs: `product/ux/`.

Status: **Approved (sponsor 2026-10-15)**.
Changelog: 2026-10-15 — applied sponsor answers A13 (risk-free default 5 %/year, editable) and A14+A15 (default
watchlist = top 30 by 20-session average traded value, refreshed weekly); updated F-018, F-061, F-090.
2026-10-16 — sponsor priority change (sponsor-answers 2026-10-16 23:17): **scenario dashboard pulled forward to
sprint-03** (slice below). Refined F-040, F-041, F-048, F-051 to Ready and narrowed them; split F-001 → F-001 + F-006
and F-032 → F-032 + F-033; new F-055, F-056, F-057; F-042 and F-081 shrink (parts moved). No new scope: PRD R2
(what-if, PR-030–034, PR-110) and R4 (scenario compare PR-072, DCA PR-070) already cover it.
2026-10-24 — sponsor scope change **A23** (sponsor-answers 2026-10-24): crawling is **manual only** from a button in the
web app; no timer. New **F-034** (5 pts) added to the S03 slice; **F-019** timer/boot-catch-up criteria superseded
(manual `crawl --date` kept). FE test bugs U1–U7 (`sprints/sprint-03/4-test.fe.md`) added as **S03 rework** acceptance
items on F-032/F-055/F-056 (no new ids, no points: the stories were committed and are not done until these pass).
PO note: PRD PR-020 still says "runs from a timer" — PO to align the PRD with A23.
2026-10-25 — sponsor request **A25** (no visual design): new **Sprint-04 slice** F-129…F-132 (15 pts) + S04-RW carry-overs
(3 pts); UX spec `ux/visual-design.md`; DoD for UI stories now requires screenshots checked against it. F-048 n/a wording refined (R4-2).
2026-10-26 — sprint-05 planning: **Sprint-05 slice** (F-013, F-014, F-015, F-016, F-023, F-033 + S05-RW, 19 pts). F-013 2→1 and
F-023 3→2 (mostly delivered in S03); F-014 needs a V5 block spike first (retro S03 R2) and runs as crawl step 3 (A23);
F-015 adds reconstructed nominal (A18-A) and a rights example; F-016 list shows on F-021 later (CLI until then).


Conventions
- `F-###` story → `PR-###` requirement. Points 1/2/3/5/8 (nothing above 8). Status: **Ready** (refined,
  can enter a sprint) · **Backlog** (has G/W/T, refine before planning) · **Deferred** (R6, rough points).
- Money criteria carry a worked numeric example. Prices in the examples are **illustrative**, not market data.
  Default fee 0.15 % per side (A6, VN§5), sell tax 0.1 % (VN§5), cash-dividend tax 5 % (VN§5), lot 100 (VN§4).
- Every analysis story states its **decision time** (what data was knowable) so look-ahead is testable.
- Every screen story inherits: EN/VI labels (PR-137), disclaimer on analysis screens (PR-130), "how computed
  + as-of" on every figure from R2 on (PR-110), and the states in its UX spec.

## Summary

| Release | Epics | Stories | Points | Status |
|---|---|---|---|---|
| **S03 slice — Scenario dashboard** (pulled forward; + F-034 by A23) | E1, E3, E4 | 11 | 30 | Ready |
| **S04 slice — Visual design** (A25) + S04-RW | E3 | 4 (+RW) | 18 | Ready |
| **S05 slice — Prices are right** + S05-RW | E2, E3 | 6 (+RW) | 17 (+2) | Ready |
| R1 Data foundation (rest) | E1, E2, E3 | 15 | 57 | Ready |
| R2 What-if (rest) | E4, E8 | 11 | 38 | Backlog |
| R3 Price board | E5, E8 | 13 | 45 | Backlog |
| R4 Scenarios | E6, E8 | 14 | 46 | Backlog |
| R5 Why it moved | E7, E8 | 7 | 24 | Backlog |
| **v1 (S03 + S05 slices + R1–R5)** | | **77** | **257** | |
| R6 Later | E9 | 9 | ~41 (rough) | Deferred |

Traceability: every one of the 61 PR-### maps to at least one story (table at the end). PR-112 (exercises) has
no release in PRD §8; the PM ships each level's exercise with the screen it needs (R2–R5) — a sequencing
choice, not a scope change.

## Sprint-03 slice — Scenario dashboard (pulled forward 2026-10-16)

Goal: the sponsor saves many investment scenarios and follows them side by side in the web UI. A scenario =
**one symbol, start date, end date or "today", amount VND, style lump-sum or DCA (monthly amount)**, run by the
what-if engine on the daily bars from F-012, fees/tax/lot per VN§4–§5. UX: `ux/scenario-dashboard.md`.

| Story | Pts | What | Depends on |
|---|---|---|---|
| F-031 | 3 | Web app shell, EN/VI (first `apps/web`) | — |
| F-032 | 1 | Disclaimer banner on analysis routes | F-031 |
| F-006 | 1 | Trading-cost rules v1 (fee, sell tax, lot, T+2) with `effective_from`, `rules_version` | — |
| F-040 | 3 | Lump-sum buy on close of N: lots, fee, residual cash, non-trading shift | F-006, F-012 |
| F-041 | 2 | Value at end date: liquidation value, P/L ₫ and %, CAGR | F-040 |
| F-057 | 3 | DCA: monthly amount on a fixed day, whole lots, carried cash | F-040, F-003 |
| F-055 | 3 | Saved scenarios: create / edit / delete (API + form) | F-040, F-057 |
| F-056 | 5 | Scenario dashboard: cards side by side, value, P/L, mini equity curve, approximate flag, states | F-041, F-055 |
| F-048 | 2 | Benchmarks per scenario: VN-Index (price-only), E1VFVN30 (same model) where data exists | F-041, F-057 |
| F-051 | 2 | "How it is computed" panel for every dashboard figure | F-041 |
| F-034 | 5 | "Cào dữ liệu" button: manual crawl of today (ticks + daily catch-up), no automatic crawl (A23) | F-017, F-012, F-031 |
| **Total** | **30** | | |

**S03 rework (from `4-test.fe.md`, 2026-10-18).** Acceptance items RW-U1…RW-U7 are written under the story they
belong to (F-056: U1, U3, U6, U7; F-032: U2; F-055: U4; F-056/F-031: U5). **must** = the story is NOT DONE until it
passes; **should** = fixed this sprint, a miss is listed at review but does not block the story.

Honesty rule for the whole slice (until F-014 + F-015 + F-043/F-044 land): every result computed on source-adjusted
closes (`bars_1d_src`) carries `price_basis = source_adjusted`, `approximate = true` and shows the flag
"≈ Gần đúng — giá điều chỉnh, chưa tính cổ tức / Approximate — adjusted prices, dividends not yet modelled" with a non-colour cue (icon + text). Share counts are bought at adjusted prices, so they can
differ from what was buyable on the day; the "how computed" panel says so.
Not in the slice (later, unchanged): several symbols per scenario (F-089), fill rules other than close-of-N
(F-042), corporate-action events (F-043–F-045), ledger/CSV (F-049, F-092), risk metrics (F-090), IRR for DCA.

---

## Sprint-04 slice — Visual design (A25, 2026-10-25)

Goal: the web app looks like a real product — calm, readable, data-dense, light + dark — instead of browser defaults.
UX: `ux/visual-design.md` (wins over the other specs on appearance). No behaviour change; all existing tests stay green.
**DoD addition for every UI story (from S04):** the FE tester attaches the screenshots of `ux/visual-design.md` §9
(375 + 1280 px, light + dark) to `4-test.fe.md` and marks each checklist line pass/fail; the PM review compares them to
the spec. A UI story without screenshots is NOT DONE.

| Story | Pts | What | Depends on |
|---|---|---|---|
| F-129 | 5 | Design tokens + base stylesheet (colours incl. VN board, type, spacing, buttons, inputs, focus, light/dark) | F-031 |
| F-130 | 3 | Shell look: top bar, disclaimer band, crawl status line, mobile top bar | F-129 |
| F-131 | 5 | Scenarios screen look: header, cards grid 1/2/3, card, table, form panel, how-computed, states | F-129 |
| F-132 | 2 | Visual acceptance check: screenshot script + undefined-variable / serif / contrast guards | F-129 |
| S04-RW | 3 | Carry-overs from sprint-03 retro R3/R4 (technical + AI notes, F-048 wording) | — |
| **Total** | **18** | | |

**F-129 Design tokens and base stylesheet** · PR-137 (UI), PR-130 (banner look), A25 · 5 pts · Ready · S04 · UX: `ux/visual-design.md` §2–§3, §8
Decision time: n/a (presentation only).
- Given any route, Then the computed `font-family` of `body` is the system sans stack (§3.4) and no element renders in a serif font.
- Given `apps/web/src`, Then every `var(--name)` used (incl. `--chart-line`, `--chart-invested`, `--color-error`) is defined in
  `styles/tokens.css` for light and, for colour tokens, again under `@media (prefers-color-scheme: dark)`; a check fails the build otherwise.
- Given a P/L of +610.975 ₫ / −610.975 ₫ / 0 ₫, Then it shows "▲ +610.975 ₫" in `--up`, "▼ −610.975 ₫" in `--down`, "= 0 ₫" in `--ref`
  (sign + icon + colour, never colour only); `--ceiling` purple and `--floor` cyan tokens exist for the board.
- Given money/percent figures, Then they use `font-variant-numeric: tabular-nums`.
- Given Tab through the app, Then every interactive element shows the 2 px `--focus` ring on `:focus-visible`.
- Given buttons/inputs/segmented controls, Then none show OS default grey styling; primary/secondary/danger/icon styles per §3.6.
- Given axe in light and dark, Then 0 `color-contrast` violations on /scenarios.

**F-130 Shell look** · PR-137, PR-130, PR-020 · 3 pts · Ready · S04 · UX: `ux/visual-design.md` §4–§5
- Given 1280 px, Then the top bar is one 52 px sticky row: Finvest · nav (active underlined, `aria-current`) · freshness chip · crawl button · VI | EN.
- Given 375 px, Then the top bar stays one row (☰ menu, icon-only crawl button with the same accessible name, VI | EN visible) and
  `document.documentElement.scrollWidth <= 375`.
- Given an analysis route, Then the disclaimer is a full-width warn band with ⓘ, both lines, VI first.
- Given a crawl running / done / error (mocked), Then the status line shows spinner + progress bar / ✓ in `--ok` + dismiss /
  ✕ on `--error-bg` with the cause in mono, as in §5; stale freshness chip is warn with ⚠.

**F-131 Scenarios screen look** · PR-030, PR-072, PR-110 · 5 pts · Ready · S04 · UX: `ux/visual-design.md` §6
- Given 3 saved scenarios, Then the grid shows 1 column at 375, 2 at 800, 3 at 1280 (content max 1280 px), cards equal height per row.
- Given a card, Then it has the §6.3 frame and order; "Giá trị nếu bán" is the headline figure (20 px, 600); the approximate flag is a
  warn chip; benchmark n/a is muted text "n/a — thiếu dữ liệu ETF trong kỳ", never 0; the sparkline uses `--chart-line` + dashed `--chart-invested`.
- Given the table view, Then numeric columns are right-aligned tabular, the header is sticky inside its scroll container, the sorted
  column shows ▲/▼ + `aria-sort`, Name is sticky at 375, and only the table container scrolls sideways.
- Given Add or Edit at 1280, Then the form is a 440 px right drawer with backdrop, sticky header and footer (Lưu primary, Huỷ), errors
  under fields with ✕ in `--color-error`; at 375 it is full screen with stacked full-width buttons.
- Given (i) on a figure, Then how-computed opens in the same drawer with the formula in a mono block that wraps at 375.
- Given empty / no-bars / loading / API error / one-card error / partial data, Then each looks as §6.7 (skeletons sized like cards).

**F-132 Visual acceptance check** · PR-137 · 2 pts · Ready · S04 · UX: `ux/visual-design.md` §9
- Given the stack running, When the tester runs the screenshot script, Then it writes `sprint-04/screens/<screen>-<375|1280>-<light|dark>.png`
  for the 7 screens of §9.1 (28 files) using mocked API states where needed.
- Given the guards of §9.3 (undefined `var(--…)`, serif font, axe contrast both schemes), Then each runs in CI/`npm test` and fails when broken
  (proved once by removing one token).
- Given each screenshot, Then `4-test.fe.md` carries the §9.2 checklist with pass/fail per line.

**S04-RW Sprint-03 carry-overs** · retro S03 R3/R4 · 3 pts · Ready · S04 (technical; no new user value, no new id per item)
- **T5b** Given a ledger row `complete` for a date, When a later run upserts `partial`/`blocked`/`missed`, Then the row stays `complete`
  (rank `complete > partial = blocked > missed`); 1 db test.
- **T5c** Given the orphan `bars_1d` row for 2026-10-24 (a Saturday), Then ops deletes it and logs the command in `ops/README`.
- **T6** Given the tester, Then one documented test DSN lets `fi-be-tester` run the db suite (closes S02 B4 too).
- **E2E pin** Given `real-stack.mjs`, Then the FPT lump-sum case pins `sell_date`, so its numbers no longer drift with new bars.
- **Smoke** Given the BE smoke, Then it includes the VNINDEX `value / v` ratio query (detects a unit mix-up in index bars).
- **AI-1** Given `whatif.py` curve loop, Then it starts at 0 or asserts the first calendar day has a fill (no `states[-1]` on empty).
- **AI-2 (F-048 wording)** Given E1VFVN30 has a gap **inside** N..M (not only before listing), Then the cell reads
  "n/a — thiếu dữ liệu ETF trong kỳ / n/a — ETF data missing in period" instead of "since <date>"; the "data from dd/mm/yyyy" text stays only
  when the ETF's first bar is after N.
- **AI-3** Given `holding_days`, Then it is documented as display-only and not used as an XIRR input (comment + analytics.md note).

---

## Sprint-05 slice — Prices are right (2026-10-26)

Goal: daily update, corporate actions, nominal + adjusted series, reconciled on VN30 — under A23 (manual press only)
and retro S03 R2 (spike each new source's block behaviour before planning its throughput). Re-checked 2026-10-26:
F-013 and F-023 were mostly delivered in S03 (F-034, BE-ssi-snapshot, F-051) and shrink by 1 pt each.

| Story | Pts | What | Depends on |
|---|---|---|---|
| F-013 | 1 | Daily bar on each press: acceptance + missed-press case | F-034 |
| F-014 | 5 | Corporate-actions table + diff log, crawl step 3 (after the V5 spike) | F-034 |
| F-015 | 5 | Adjusted series + reconstructed nominal | F-014 |
| F-016 | 3 | Reconciliation, VN30 30/30 | F-015 |
| F-023 | 2 | data_snapshot definition, reproducibility, /health rules_version | F-014 |
| F-033 | 1 | No-broker audit test | — |
| S05-RW | 2 | Carry-overs from sprint-04 review/retro (UI) | — |
| **Total** | **19** | | |

**S05-RW Carry-overs from sprint-04** · 2 pts · Ready · UX: `ux/visual-design.md` §4, §6.3, §6.4, §9 (S05 lines)
- **OBS-7** Given 768 and 800 px, Then the top bar is one line (chip date only, icon crawl button) and no label breaks over 2 lines.
- **Shots (retro S04 R2)** Given the screenshot script, Then it also writes 768×1024 and 800×900 light shots for screens (a) and (f),
  and the §9.2 checklist has the 768/800 lines.
- **Header** Given the table at 1280, Then every header label is ≤ 2 lines ("so với E1VFVN30", unit in title + footer).
- **DCA shift lines** Given a DCA card with 5 shifted buy dates, Then it shows one line "Ngày mua dời sang ngày giao dịch kế tiếp: 5 lần" + "Xem".
- Tester-artifact rule (retro S04 R5) is a brief change for sa, not a story item.

---

## R1 — Data foundation

### E1 Market rules and reference data (L1)

**F-001 Rules module from vn-market.md** · PR-001 · 4 pts · Ready · (fees, tax, lot, T+2 moved to F-006 for S03)
- Given `knowledge/vn-market.md` §2–§5, When the rules module is generated, Then sessions, bands, tick sizes
  (and the F-006 cost values, extended in the same module) each exist as one value with `effective_from` and `verified: yes|no (date, source)`.
- Given HOSE reference 93,500 VND, band ±7 %, tick 100 for prices ≥ 50,000 (VN§3), When ceiling/floor are
  computed, Then raw 100,045 / 86,955 round **inward** to **100,000 / 87,000**.
- Given HNX reference 20,000, band ±10 %, tick 100, Then ceiling/floor = 22,000 / 18,000.
- Given the fee value is changed from 0.15 % to 0.20 % in the module, When a consumer reads it, Then it gets
  0.20 % with the new `effective_from` and older dates still return 0.15 % (PR-001 acceptance).

**F-002 Market rules page (EN/VI)** · PR-001, PR-137 · 3 pts · Ready · UX: `ux/market-rules.md`
- Given the rules module, When the sponsor opens "Market rules", Then every rule shows value, venue,
  `effective_from`, verification status and source section (VN§n).
- Given a rule with `verified: no`, Then it renders in the warning state with a non-colour cue (icon + text "Unverified").
- Given the UI language is switched, Then all labels change language; rule values are unchanged.

**F-003 Trading calendar** · PR-002 · 3 pts · Ready
- Given a calendar table per venue (holidays, bridge days, half sessions) maintained as data, When a date is
  queried, Then it returns trading / holiday (with name) / weekend; nothing is inferred from missing rows (VN§2).
- Given 2026-09-02 (National Day) is a holiday in the table and no crawl ran, Then it is **not** reported as a gap.
- Given a weekday trading date with no crawl, Then it **is** reported as a gap.

**F-004 Symbol master (all exchanges, delisted kept)** · PR-003 · 5 pts · Ready
- Given the free source's listings for HOSE, HNX, UPCoM stocks and ETFs (A1), When the daily refresh runs, Then
  each symbol has exchange, listing date, delisting date, ICB sector, and index-membership history (VN30 etc.).
- Given a symbol disappears from the source listing, Then it is kept with a delisting date, never deleted.
- Given the refresh runs twice the same day, Then the table is unchanged (idempotent).

**F-005 Session-phase service** · PR-004 · 3 pts · Ready
- Given the session table VN§2 and the calendar, When asked at 2026-10-15 09:10 Asia/Ho_Chi_Minh, Then HOSE =
  ATO, HNX = continuous, UPCoM = continuous.
- Given 11:45, Then HOSE = break; given 14:35, Then HOSE = ATC, UPCoM = continuous (no ATC on UPCoM).
- Given a holiday from F-003, Then every venue = holiday; given 16:00 on a trading day, Then = closed.

### E2 Data foundation: crawler and store

**F-006 Trading-cost rules v1** · PR-001 · 1 pt · Ready · **S03 slice**
- Given VN§4–§5, Then buy fee 0.15 %, sell fee 0.15 % (A6), sell tax 0.1 % of sale value, lot 100, settlement T+2
  each exist once in `packages/market_rules` with `effective_from`, `verified: yes|no (date, source)`, and the set has a
  `rules_version` string that every result carries.
- Given the fee is changed to 0.20 % from a later `effective_from`, Then a trade dated before it still uses 0.15 %.

**F-010 MarketDataSource adapter with fixtures and unit conversion** · PR-016, C9 · 5 pts · Ready
- Given a source that quotes 93.5 (thousand VND) and volume in units of 10 shares, When the adapter
  normalises, Then the stored price is 93,500 VND and volume 10 × the quoted unit; the unit rule is documented in the adapter.
- Given recorded fixtures, When the core test suite runs with networking disabled, Then it passes (offline).
- Given a second adapter implementing daily OHLCV, When it is configured instead of the first, Then no core code changes.

**F-011 Rate limits, caching, backoff, stop on block** · PR-135 · 3 pts · Ready
- Given a per-source request budget, When a crawl runs, Then it never exceeds the budget and every response is cached.
- Given the source returns HTTP 429/403 three times in a row, Then backoff is exponential and the crawl stops
  and records "source blocked" instead of retrying indefinitely.
- Given any request, Then the user-agent identifies a personal tool.

**F-012 Daily OHLCV back-fill** · PR-010 · 5 pts · Ready
- Given the symbol master and all indices, When back-fill runs, Then daily OHLCV + matched value is stored for
  all years the source provides, nominal, in VND (C9).
- Given the back-fill is interrupted, When re-run, Then it resumes without duplicates.
- Given back-fill completes, Then coverage % per exchange is computed for G2 (target ≥ 99.5 %).

**F-013 Daily incremental update** · PR-010 · ~~2~~ **1 pt** · Ready · **S05** · re-checked against A23 (2026-10-26)
Re-scope: no after-close job (A23); F-034's press + BE-ssi-snapshot (S03) already add the day's bar. What is left is
the acceptance of that path and the missed-press case. Decision time: n/a (data collection).
- Given trading day 27/10/2026 and a press after 15:00, Then the 27/10 bar is stored for every listed stock the SSI board
  (S1, 3 calls) answers — source `ssi`, observed nominal — and for VNINDEX and VN30 (V2); names the board did not answer
  are V2 gaps within the press budget (`GAP_MAX`), the rest are `deferred`, fetched first on the next press, and the done
  line says "· N mã chờ lượt sau".
- Given the same date is pressed twice, Then rows and the manifest checksum are identical (idempotent).
- Given no press on 27/10 and a press on 28/10, Then the board answers 28/10 only (SourceNoLongerServes for 27/10), 27/10
  comes from V2 (source-adjusted, so its nominal is `reconstructed` per F-015) and the run lists it — never silently absent.

**F-014 Corporate-actions table with diff log** · PR-011 · 5 pts · Ready · **S05** · re-checked against A23 and retro S03 R2 · UX: `ux/app-shell.md` §Crawl button (step 3)
Decision time: an event is knowable from its `publicDate` (V5), not its ex-date; store both so R2 (F-043/F-044) can test look-ahead.
**Spike first (retro S03 R2):** V5 (`iq.vietcap.com.vn`) block behaviour — block signal, request budget before a block,
hold/retry window, batch/page limit — and the pay-date / cash-per-share field names, in ≤ 6 polite calls, recorded in
`data.md` §1.2 V5. The per-press budget below cites that line.
- Given V5 events for a symbol, When a press runs step 3 ("Bước 3/3 — sự kiện quyền"), Then each row has symbol, type
  (cash_dividend, stock_dividend/bonus, rights, split/merge, listing_change), ex-date, record date, pay date,
  ratio / amount per share / issue price, public date, source, source event id, fetched-at (VN§6).
  Example: FPT "Trả cổ tức bằng tiền 1.000 đồng/cp", exrightDate 2026-11-05 → cash_dividend, amount 1,000 VND;
  "Thưởng cổ phiếu tỷ lệ 10:1"/`exerciseRatio` 0.1 → stock_dividend a:b = 10:1 (holder of 10 gets 1).
- Given a stored event whose ex-date changes at the source (2026-11-05 → 2026-11-07), When the next press runs, Then the row
  is updated and `corporate_action_log` gets one entry (field ex_date, old 2026-11-05, new 2026-11-07, changed_at);
  a press with no change writes no log entry (idempotent).
- Given ~1,600 listed symbols and the V5 per-press budget B (from the spike), Then each press checks VN30 members and the
  symbols of saved scenarios first, then the others oldest-checked first, up to B; the rest are deferred and counted in the
  done line ("· 12 mã chờ lượt sau"); repeated presses reach every listed symbol (no symbol is skipped for good).
- Given a field the spike could not map (pay date or cash amount), Then it is parsed from `eventTitleVi`; if that fails the row
  is stored with the value NULL and listed in `data_anomalies` ("corporate action amount missing") — never guessed.
- Given V5 blocks (3 × 429/403/418/hold, F-011), Then step 3 stops with "Lỗi: nguồn VCI IQ chặn (HTTP 418 ×3)", the reason is
  in `crawl_runs`, and steps 1–2 results stay stored.
- UI: step 3 progress and "+3 sự kiện quyền (1 thay đổi)" in the done line per `ux/app-shell.md`; screenshot DoD (screen f).

**F-015 Adjusted price series and reconstructed nominal** · PR-012 · 5 pts · Ready · **S05**
- Decision time: adjusted series are retroactive by design (VN§6) and are for charts/indicators only; the
  simulator uses nominal prices + events (F-043/F-044, R2 — so the scenario "approximate" flag stays until then).
- Given nominal closes D−2 = 51,000, D−1 = 50,000 and a cash dividend 1,000/share ex on D, When adjusted,
  Then factor = (50,000 − 1,000) / 50,000 = 0.98 and adjusted closes are D−1 = 49,000, D−2 = 49,980.
- Given a bonus issue 10:3 ex on D with D−1 close 93,500, Then factor = 10/13 and adjusted D−1 = 71,923.08.
- Given a rights issue 10:2 at 10,000 ex on D with D−1 close 50,000, Then adjusted reference = (50,000 × 10 + 10,000 × 2) / 12
  = 43,333.33 and factor = 0.866667; if the rights price ≥ the pre-ex price, factor = 1 (VN§6).
- Given both a cash and a bonus event, Then factors multiply; re-running yields byte-identical output (reproducible).
- Given a date before crawl start with V2 source-adjusted close 49,000 and our cumulative factor 0.98 after it, Then the
  reconstructed nominal close = 49,000 / 0.98 = 50,000 with `nominal_kind = reconstructed` (A18-A); a date with an S1
  board bar keeps `nominal_kind = observed` and is never overwritten by a reconstruction.

**F-016 Adjusted-series reconciliation** · PR-012 · 3 pts · Ready · **S05**
Decision time: n/a (data quality). Runs after step 3 of a press (local, 0 source calls) plus a VN30 cross-check on S2
(30 calls; block behaviour in the same spike as F-014).
- Given our adjusted close 49,000 and the source's 48,900, Then mismatch = 100 / 48,900 = 0.204 % > 0.1 % and a
  `recon_mismatches` row (symbol, date, ours, source, %) is written.
- Given 49,000 vs 48,980 (0.041 %), Then no row.
- Given the VN30 constituents, Then a reconciliation run covers all 30 (R1 release criterion) and reports "30/30, k mismatches".
- Given dates before crawl start, Then the check is self-consistency (reconstructed × factor == source-adjusted, to 1 VND).
- Display: the list appears on the Data-quality page when F-021 lands (S06); until then `crawl recon` (CLI) prints it.

**F-017 Tick crawl after close with manifest** · PR-013, C1 · 8 pts · Ready
- Given a trading day, When the after-close crawl runs, Then for each symbol it stores time, price, volume,
  side where given; the raw payload is archived and normalised rows are compressed.
- Given the crawl finishes, Then a per-session manifest lists symbols fetched, rows, checksum, skipped symbols with reason.
- Given the crawl is re-run for the same date, Then rows and checksum are unchanged (idempotent).
- Given the machine was off and the source no longer serves that day, Then the manifest reads "session
  missed: machine off / source no longer serves" — never silently absent (0 silent gaps, G1).

**F-018 Tick crawl priority order** · PR-013 · 3 pts · Ready
- Given the source's rate limit does not allow a full-market pass in the evening, When the crawl runs, Then the
  order is watchlist → VN30 → HOSE → HNX → UPCoM and the manifest lists every skipped symbol.
- Given the default watchlist is not yet computable (no stored sessions yet), Then the order starts at VN30
  until the first weekly watchlist refresh (F-061, A14/A15).

**F-019 Best-effort scheduler** · PR-020 · 3 pts · Ready · **criteria 1–2 superseded by A23 (2026-10-24): no timer, no
boot catch-up; crawling starts only from F-034's button or the manual command below**
- Given a systemd user timer (or equivalent), When a trading day reaches 15:30, Then the crawl starts with no manual action; retry at 20:00 if it failed.
- Given the machine was off at 15:30 and 20:00, When it boots, Then the catch-up job runs once and either
  fetches (if served) or records the gap.
- Given the command `crawl --date 2026-10-14`, Then that date is (re)crawled manually.
- Given non-trading days (F-003), Then nothing runs.

**F-020 Data folder under the repo, git-ignored** · PR-132 · 1 pt · Ready
- Given a fresh checkout, When the app starts, Then all data is written under `finance_invest/data/` (A12)
  and `git status` shows nothing from it (git-ignored).
- Given retention config, Then the default is "keep everything".

**F-021 Data-quality page: feeds, gaps, completeness, storage** · PR-017, PR-132, PR-136 · 5 pts · Ready · UX: `ux/data-quality.md`
- Given each feed (daily, corporate actions, ticks, symbols), Then the page shows last success time, sessions
  covered, completeness % and the list of missed sessions each with its reason (G1).
- Given 20 trading sessions since crawl start, 17 complete, 3 missed, Then tick completeness = 85.0 % and the 3 dates are listed.
- Given storage per feed, Then it shows size on disk (e.g. "Ticks: 412 MB"); and "No backup configured" (PR-136) until one exists.

**F-022 Data-quality anomalies** · PR-017 · 3 pts · Ready
- Given a stored price outside that day's [floor, ceiling] (F-001), or zero volume on a trading day, or a
  duplicate tick (same time, price, volume, sequence), Then each is listed with symbol, date and rule.
- Given an anomaly is fixed by a re-crawl, Then it disappears from the list on the next check.

**F-023 Data snapshot and rules version on results** · PR-133 · ~~3~~ **2 pts** · Ready · **S05**
Re-scope: S03 already returns `data_snapshot` and `rules_version` on every figure and shows them in "how computed".
Left: the definition, the reproducibility test and the health field. Decision time: n/a (provenance metadata).
- Given a result whose inputs were fetched at 26/10/2026 16:14 (bars) and 27/10/2026 16:22 (a corporate action), Then
  `data_snapshot` = 2026-10-27T16:22+07:00 (max fetched-at of the inputs actually used, not the last bar date).
- Given the same inputs, snapshot and `rules_version` (now 2026.10.16), When recomputed, Then every number is identical (test).
- Given `GET /health`, Then `rules_version` is the current RULES_VERSION, not null.

### E3 Platform and guardrails

**F-030 Local docker compose, one-command start and crawl** · PR-131 · 3 pts · Ready
- Given Ubuntu with Docker, When the sponsor runs one documented command, Then the app starts bound to
  127.0.0.1 only (not reachable from another host).
- Given one documented command with a date, Then that date is crawled.

**F-031 App shell with EN/VI switch** · PR-137 · 3 pts · Ready · **S03 slice** · UX: `ux/app-shell.md`
- Given `docker compose up`, Then `apps/web` is served on 127.0.0.1 only, with nav item **Kịch bản / Scenarios**
  as the start page (Data quality and Market rules appear when F-021/F-002 land); freshness chip shows the latest
  stored bar date ("Dữ liệu đến 23/10/2026" / "Data as of 23/10/2026").
- Given the app shell, When the sponsor picks VI or EN, Then every label switches and the choice survives a reload (stored locally).
- Given a translation key missing in either language, Then the test suite fails.
- Given technical docs, Then they stay English (not translated).

**F-032 Guardrail banner** · PR-130 · 1 pt · Ready · **S03 slice**
- Given any analysis route (S03: the scenario dashboard and its form), Then the banner shows both "Mô phỏng để học,
  không phải lời khuyên đầu tư" and "Educational simulation, not investment advice"; a test enumerates routes and asserts it.
- **RW-U2 (must, S03 rework)** Given axe on /scenarios, the form and the how-computed panel, Then no `region` violation:
  the disclaimer sits inside a landmark (e.g. within `<header>`/`<main>`, or `aside` with an accessible name as `complementary`).

**F-034 "Cào dữ liệu" — manual crawl button, no automatic crawl** · PR-020, PR-131, PR-013 · 5 pts · Ready · **S03 slice (A23)** · UX: `ux/app-shell.md` §Crawl button
Decision time: n/a (data collection, no analysis). Uses the existing `POST /jobs` (contracts/platform.md, 409 when the same job runs).
- Given the top bar, Then a button "Cào dữ liệu" / "Crawl data" sits left of the language switch on every route.
- Given today 2026-10-26 (a trading day) at 16:10, When the sponsor presses it, Then one crawl job starts that (1) crawls
  ticks for 26/10/2026 per F-017/F-018 and writes its manifest, then (2) back-fills daily bars for every trading day missing
  since the last stored bar (e.g. last bar 16/10/2026 → 19/10…26/10, 6 sessions), resuming without duplicates (F-012).
- Given today is a trading day at 10:30 (session open), When pressed, Then ticks so far are crawled and the manifest is
  marked `partial` with the cut-off time; a later press after 15:00 re-crawls that day and replaces it (F-017 idempotent).
- Given today is not a trading day (weekend/holiday per F-003), When pressed, Then only the daily catch-up runs and the
  result says "Hôm nay không có phiên — chỉ cập nhật giá ngày" / "No session today — daily bars only".
- Given a crawl is running, Then the button shows a spinner + progress ("Đang cào… 12/30 mã" / step name) and is disabled;
  Given a second press from another tab or the CLI, Then the API answers 409 and the UI says "Đang có một lượt cào chạy"
  — never two crawls at once. Given a page reload mid-run, Then the running state and progress come back.
- Given the run finishes, Then the button area shows done: tick symbols + rows, daily sessions added, skipped symbols
  count, finish time and duration, e.g. "Xong 16:14 · 30 mã, 812.344 lệnh khớp · +6 phiên giá ngày · 2 mã bỏ qua · 3 phút 41 giây";
  the freshness chip updates without a reload.
- Given the run fails, Then the error names the cause and the path/source, e.g. writing `data/raw/ticks/2026-10-26` raises
  PermissionError → "Lỗi: không có quyền ghi data/raw/ticks/2026-10-26 (PermissionError)"; source blocked (F-011) →
  "Lỗi: nguồn KBS chặn (HTTP 403 ×3)". The failure is recorded in `crawl_runs` with that reason (never silent), and the
  button returns to idle so it can be pressed again.
- Given the app is installed, Then no timer, cron or boot job crawls by itself (test: no systemd unit / scheduler entry in
  the repo's install targets; `make` has no timer install step).

**F-033 No-broker audit test** · PR-130 · 1 pt · Ready · (split from F-032) · **S05**
- Given the Python and npm dependency trees, Then an audit test finds no broker SDK and no order-placement endpoint
  (a denylist of package names and URL patterns such as `/order`, `placeOrder`) and fails the build if one appears.

---

## R2 — What-if (L2)

### E4 What-if simulator

**F-040 Lump-sum buy: lots, fee, residual cash** · PR-030 · 3 pts · Ready · **S03 slice**
- Decision time: close of day N (default fill rule F-042); only data ≤ N is used for the buy (test: bars after N
  perturbed → same shares, same cash).
- Given N = Sat 2026-10-17, Then the buy happens at the close of Mon 2026-10-19 (next trading day, F-003) and the
  result shows "Ngày mua dời sang 19/10/2026 / Buy date moved to 19/10/2026". (Moved here from F-042.)
- Given N before the symbol's first stored bar, Then no result: "Dữ liệu sớm nhất / Earliest data: dd/mm/yyyy".
- Given the bars are source-adjusted (`bars_1d_src`), Then the result has `price_basis = source_adjusted`,
  `approximate = true`, `rules_version` (F-006) and `data_snapshot` (max `fetched_at` of the bars used).
- Given 10,000,000 VND into FPT on Mon 2026-10-12 at an illustrative close of 93,500, lot 100, buy fee 0.15 %,
  When simulated, Then shares = 100 (200 would need 18,728,050), cost 9,350,000 + fee 14,025 = 9,364,025,
  **cash left 635,975 VND**.
- Given 5,000,000 VND and price 93,500, Then 0 shares are bought and the result says "amount below one board lot (9,364,025 VND)".

**F-041 Value at end date: liquidation value, P/L, CAGR** · PR-030 · 2 pts · Ready · **S03 slice**
- Decision time: close of end date M (or, for "today", the latest stored bar ≤ today, shown as "as of dd/mm/yyyy").
  M is shifted back to the previous trading day if it is not one.
- Value = **liquidation value** = cash + shares × close(M) − sell fee − sell tax (what you would get by selling at
  that close). It is a valuation, not a trade, so no T+2 refusal here (the T+2 sale refusal moves to F-053).
- Given F-040's 100 shares and M at an illustrative 100,000: value 10,000,000, fee 15,000, tax 10,000, Then net
  9,975,000; final cash 635,975 + 9,975,000 = **10,610,975**; P/L **+610,975 VND = +6.11 %** of the 10,000,000 invested.
- Given a holding period of exactly 365 days, Then CAGR = total return; otherwise CAGR = (end/start)^(365/days) − 1, formula shown.

**F-042 Declared fill rule** · PR-031 · 2 pts · Backlog · (non-trading-day shift moved to F-040 for S03)
- Given fill rules close-of-N (default), next open, VWAP-of-N, limit-within-[low, high], Then the chosen rule is shown on the result.
- Given a limit price of 95,000 when that day's high is 94,800, Then it does not fill and says why (VN§4).

**F-043 Cash dividend event** · PR-032 · 3 pts · Backlog
- Given 100 shares held on the ex-date and a cash dividend of 2,000 VND/share, Then gross 200,000, tax 5 %
  10,000, **net 190,000 VND** credited on the pay date (not the ex-date).
- Given option "reinvest" and net cash 190,000 < one lot (100 × price), Then it stays as cash and the result says so.

**F-044 Stock dividend / bonus shares** · PR-032 · 3 pts · Backlog
- Given 100 shares, ratio 10:3, close before ex 93,500, Then 30 new shares count from the ex-date; adjusted
  reference = 93,500 × 10 / 13 = 71,923.08; value at ex reference = 130 × 71,923.08 ≈ 9,350,000 (continuity).
- Given 105 shares at 10:3 (31.5 new), Then fractional handling follows the rules module (default round down, `[verify]` VN§6).

**F-045 Rights issue: exercise or lapse** · PR-032, A10 · 3 pts · Backlog
- Given 100 shares, rights 10:2 at 10,000, close before ex 50,000, Then adjusted reference = (50,000 × 10 + 10,000 × 2) / 12 = 43,333.33.
- Given cash 635,975 ≥ 20 × 10,000 = 200,000 and default policy, Then exercise: cash 435,975, shares 120.
- Given cash 150,000 < 200,000, Then rights lapse and the result says so; the user can force "lapse" with enough cash.

**F-046 What-if vs adjusted-series agreement** · PR-032, G3 · 3 pts · Backlog
- Given 10 dividend-paying stocks over ≥ 3 years, When what-if total return (fractional, no lots/fees for this
  test) is compared with adjusted-series return, Then each differs by ≤ 0.05 %.

**F-047 Return breakdown: chart return vs real return** · PR-033 · 5 pts · Backlog
- Given F-040/F-041 (10,000,000 VND, 93,500 → 100,000), Then the breakdown shows, summing exactly to the real return:
  chart return 10,000,000 × 6,500 / 93,500 = **695,187.17** · lot/residual cash −45,187.17 · buy fee −14,025 ·
  sell fee −15,000 · sell tax −10,000 · dividends 0 · = **610,975 VND**.
- Given each term, Then "how computed" (F-051) shows formula and inputs.

**F-048 Benchmark on the same screen** · PR-034, A20 · 2 pts · Ready · **S03 slice** (dashboard first; F-053 reuses)
- Decision time: same dates and same cash-flow dates as the scenario.
- Given the same amount and dates, Then each scenario shows VN-Index (price-only, labelled "không đầu tư được /
  non-investable", no fees: amount × index(M) / index(N), each DCA contribution likewise) and E1VFVN30 (A20) run
  through the same engine (lots, fees, tax), with P/L % and the difference vs the scenario in percentage points.
- Given index 1,200.00 on N and 1,260.00 on M and 10,000,000 VND, Then VN-Index value 10,500,000, +5.00 %; a scenario
  at +6.11 % shows "+1,11 điểm % so với VN-Index / +1.11 pp vs VN-Index".
- Given E1VFVN30 has no bar on N (listed later or not back-filled), Then its cell reads "không có dữ liệu / n/a —
  data from dd/mm/yyyy"; never a zero. A gap inside N..M reads "n/a — thiếu dữ liệu ETF trong kỳ / n/a — ETF data missing in period" (S04-RW AI-2).

**F-049 Cash and share ledger** · PR-039, PR-134 · 3 pts · Backlog
- Given F-040/F-041, Then the ledger lists dated rows: buy −9,350,000; buy fee −14,025; shares +100 (arrive
  T+2); sale +10,000,000; sell fee −15,000; tax −10,000; cash settles T+2; final cash 10,610,975.
- Given "Export CSV", Then the file has the same rows and totals.

**F-050 Golden-case verification kit (≥ 20)** · PR-037, G3 · 5 pts · Backlog
- Given ≥ 20 hand-calculated cases (lots, fees, tax, T+2, cash dividend, bonus, rights, delisting), When tests
  run, Then each matches within 1 VND; F-040–F-045 examples are among them.
- Given the tester's independent calculator, Then it agrees with every case.

**F-051 "How computed" panel** · PR-110, G7 · 2 pts · Ready · **S03 slice** (dashboard figures; later screens inherit)
- Given any figure on an analysis screen, When expanded, Then it shows formula, inputs with values, data as-of
  time, rules version (F-006 in S03; F-023 later). A test asserts every figure has one.
- Given a result with `approximate = true`, Then the panel states: prices are source-adjusted, share counts are
  bought at adjusted prices, cash dividends are not modelled, and the flag clears once nominal prices and
  corporate actions are used (F-014, F-015, F-043, F-044).

**F-052 Glossary VN/EN** · PR-111 · 3 pts · Backlog
- Given a glossary term in the UI (trần, sàn, tham chiếu, GDKHQ, T+2, lô chẵn, phí, thuế, drawdown, Sharpe,
  walk-forward…), When clicked, Then the entry shows both languages regardless of UI language, citing VN§n or docs/04.

**F-053 What-if screen** · PR-030–034 · 5 pts · Backlog · UX spec written at R2 planning
- Given symbol, amount, date N, date M (default today), fill rule, dividend option, Then the result shows
  shares, cash, market value, total return (VND, %), CAGR, breakdown, benchmark, ledger, disclaimer.
- Given a symbol with no data on N, Then an empty/partial state explains the earliest available date.
- Given 100 shares bought Mon 2026-10-12 and a sale requested Tue 2026-10-13, Then it is refused ("shares arrive
  T+2: Wed 2026-10-14", VN§5). (Moved from F-041.)

**F-057 DCA in the what-if engine** · PR-070, PR-030 · 3 pts · Ready · **S03 slice**
- Decision time: each contribution buys at the close of its own date; only bars ≤ that date are used.
- Contribution day = day of month of the start date (day 31 in a 30-day month → last day; non-trading → next
  trading day). Contributions run from the start date to the end date inclusive. Each month all cash (contribution
  + carried residual) buys as many whole lots as it can incl. buy fee; the rest is carried.
- Given 2,000,000 VND monthly from 15/01/2026 at a constant illustrative 93,500, Then months 1–4 buy 0 shares
  (cash 2,000,000 … 8,000,000 < 9,364,025 for one lot incl. fee) and month 5 (cash 10,000,000) buys 100 shares,
  cash left 635,975. At an end close of 100,000: liquidation value 10,610,975; contributed 10,000,000;
  **P/L +610,975 VND = +6.11 %** (P/L % = P/L ÷ total contributed; stated on the panel).
- Given the same constant price, Then lump-sum and DCA numbers are reproducible on re-run (same snapshot → same numbers).

**F-055 Saved scenarios: create, edit, delete** · PR-072, PR-133 · 3 pts · Ready · **S03 slice**
- Given the form, Then a scenario has: name (optional, default "FPT · 10.000.000 ₫ · 12/10/2026"), symbol (from the
  symbol master, F-004), style lump-sum | DCA, amount VND (lump) or monthly amount (DCA), start date, end date or
  "hôm nay / today". It is saved in the local database and survives a restart.
- Given amount 0, a non-integer amount, an unknown symbol, end < start, or a start after the latest stored bar,
  Then save is refused with the field-level reason (EN/VI); nothing is stored.
- Given an edit, Then the scenario is recomputed; Given delete, Then a confirm step, then it is gone from the list.
- Given 20 saved scenarios of up to 10 years each, Then the dashboard computes all of them in < 2 s on the sponsor's machine.
- **RW-U4 (should, S03 rework)** Given FPT with a start date the engine refuses (e.g. 02/01/2020, before the first stored
  bar → `no_trading_day_near_buy`), When saving, Then `POST /scenarios` refuses it (422) with the reason "Không có dữ liệu FPT
  trước <first bar dd/MM/yyyy>" / "No FPT data before …" on the start-date field; nothing is stored. A scenario already
  saved with such a date shows that same reason on its card, not "Dữ liệu nhập không hợp lệ".

**F-056 Scenario dashboard** · PR-072, PR-030, PR-130 · 5 pts · Ready · **S03 slice** · UX: `ux/scenario-dashboard.md`
- Given saved scenarios, Then each is a card showing: name, symbol, style, dates, invested, value, P/L ₫ and %
  (sign + arrow, not colour only), vs VN-Index and E1VFVN30 (F-048), a mini equity curve (daily market value from
  N to M), "Dữ liệu đến / data as of", and the approximate flag when set.
- Given every scenario uses source-adjusted bars (S03), Then every card shows "≈ Gần đúng — giá điều chỉnh, chưa tính cổ tức / Approximate — adjusted prices, dividends not yet modelled"
  as icon + text; a test asserts no card with `approximate = true` renders without it.
- Given the toggle "Bảng / Table", Then the same scenarios render as one comparison table sortable by P/L %.
- Given no scenarios, the API down, a symbol with partial data, or stale bars, Then the states in the UX spec apply.
- Given the language switch, Then all labels change; numbers stay vi-VN (1.234.567 ₫, +6,11 %).
- **RW-U1 (must, S03 rework)** Given a saved scenario and a benchmark with `available: false, first_available: null`
  (VN-Index bars empty), When /scenarios opens (and on reload), Then the page renders, the card line reads
  "VN-Index — n/a" and the table cell "n/a"; no error boundary. The TS contract types `first_available` as
  `string | null`; a test feeds null to both card and table.
- **RW-U3 (must, S03 rework)** Given two FPT scenarios named "FPT 50tr 2025" and "FPT DCA thử", Then each card header shows
  its name as visible text (symbol · style below it); with no name, the default name from F-055 is shown.
- **RW-U5 (should, S03 rework)** Given EN and 1 missing session, Then "1 session missing"; 2 → "2 sessions missing" (plural
  rules via the i18n library, both languages; VI has no plural form).
- **RW-U6 (should, S03 rework)** Given the loading state, Then skeleton cards pass axe (no `aria-label` on a role-less div:
  e.g. `role="status"` + `aria-busy`, or a visually hidden "Đang tải…" text).
- **RW-U7 (should, S03 rework)** Given a negative ₫ or % anywhere (card, table, panel), Then the minus is U+2212 "−"
  (e.g. table "−19.847.507 ₫"), one shared formatter; a test scans card and table output for ASCII "-" before a digit.

### E8 Learning layer (R2 part)

**F-054 Exercise framework + L2 exercise** · PR-112 · 3 pts · Backlog
- Given the what-if screen, Then it offers the docs/04 L2 exercise ("chart return vs real return for 5
  high-dividend stocks") with a notes field saved locally and restored on reload.

---

## R3 — Price board (L1)

### E5 Board and charts

**F-060 Watchlist board** · PR-050 · 8 pts · Backlog
- Given the watchlist in session, Then each row shows reference/ceiling/floor, top-3 bid/ask with volumes, last
  price/volume, change and %, total volume/value, foreign buy/sell; median refresh ≤ 5 s (G6).
- Given HOSE reference 93,500 and last 100,000 (= ceiling), Then the price is purple **and** carries a "▲ CE" cue;
  floor cyan + "▼ FL"; reference yellow + "="; above green "▲"; below red "▼" (VN§3).

**F-061 Watchlist management** · PR-050, A5 · 2 pts · Backlog
- Given first start, Then the default watchlist has 30 symbols (A14/A15); the sponsor can add/remove up to 100; the 101st is refused with a message.
- Given the stored daily data, When the default is computed, Then it is the top 30 symbols by **average traded
  value** (shares × price, summed per session) over the last 20 sessions, all exchanges; e.g. a symbol trading
  2,000,000 shares/session at an illustrative 93,500 averages 187,000,000,000 VND/session. Decision time: close of
  the last of the 20 sessions.
- Given fewer than 20 sessions are stored, Then the average uses the sessions available and the screen says
  "based on N sessions"; with none stored, the VN30 basket is the stand-in.
- Given a week has passed since the last refresh, Then the default is recomputed weekly (as-of date shown);
  symbols the sponsor added or removed by hand stay as the sponsor set them.

**F-062 Freshness and session states** · PR-051 · 3 pts · Backlog
- Given a row older than 15 s during continuous session, Then a "stale" badge shows (100 %, G6); verified by cutting the source.
- Given phase from F-005, Then a banner shows ATO / continuous / break / ATC / closed / holiday; when closed it says "market closed, showing last session (date)".

**F-063 Indices panel** · PR-056 · 3 pts · Backlog
- Given VN-Index, VN30, HNX-Index, HNX30, UPCoM-Index, Then each shows level, change, breadth (up/down/unchanged, ceiling/floor counts) and total value.

**F-064 Daily candlestick chart** · PR-053 · 5 pts · Backlog
- Given a symbol, Then daily candles with volume, MA overlays, ex-date/corporate-event markers; a nominal/adjusted toggle explains the difference (F-015).

**F-065 1-minute chart with data boundary** · PR-053, C2 · 3 pts · Backlog
- Given 1m bars that start on date B, Then the chart marks "1-minute data from B" and does not draw earlier.

**F-066 1-minute bars: back-fill and daily crawl** · PR-014 · 3 pts · Backlog
- Given the source's 1m window, Then back-fill as far as allowed, then add each session (idempotent).

**F-067 1m vs tick reconciliation** · PR-014 · 2 pts · Backlog
- Given a session with ticks, Then 1m bars derived from ticks equal source 1m OHLCV; mismatches appear on the data-quality page.

**F-068 Order-book snapshots for the watchlist** · PR-015 · 3 pts · Backlog
- Given the session, Then top-3 bid/ask is sampled every 3–5 s for watchlist symbols only and stored with timestamps.

**F-069 Full-market snapshot board** · PR-052 · 5 pts · Backlog
- Given all symbols (A1), Then refresh every 30–60 s (A5) with sort/filter by exchange, sector, % change, volume, ceiling/floor hits, and add-to-watchlist.

**F-070 Session replay** · PR-054, C1 · 5 pts · Backlog
- Given a past session with ticks and snapshots, Then playback at 1×/10×/60×; sessions before crawl start or missed are listed as unavailable, not hidden.

**F-071 "Explain this row"** · PR-055 · 2 pts · Backlog
- Given reference 93,500 on HOSE, Then the overlay shows ceiling 100,000 / floor 87,000 with the inward rounding and "100 shares cost 9,350,000 + fee 14,025 = 9,364,025 VND".

**F-072 L1 exercise** · PR-112 · 1 pt · Backlog
- Given the board, Then the L1 exercise "explain the colour of 10 symbols" is offered with saved notes (F-054).

---

## R4 — Scenarios (L3, L4, L5)

### E6 Backtester

**F-080 One engine with `as_of` and a look-ahead test** · PR-071 · 5 pts · Backlog
- Decision time: a signal on day t uses only bars with timestamp ≤ close of t; fill at next open t+1 (default `[assumed]`) or same close.
- Given data after t is perturbed, Then the signal at t is unchanged (kernel test).
- Given the F-040/F-041 example run through the backtester, Then numbers equal the what-if (shared tests).

**F-081 Buy-and-hold and DCA as backtester strategies** · PR-070 · 1 pt · Backlog · (DCA logic moved to F-057)
- Given the F-080 engine, Then buy-and-hold and DCA reuse F-040/F-057 and reproduce the F-057 example exactly.
- Given each strategy page, Then its rule is stated in VI and EN.

**F-082 MA crossover and breakout** · PR-070 · 3 pts · Backlog
- Given fast/slow MA parameters, Then a buy signal at the close of t where fast crosses above slow is filled at t+1 open; breakout = close > N-day high of the prior N days (excludes t).

**F-083 Stop-loss / take-profit / trailing overlays** · PR-070 · 3 pts · Backlog
- Given a stop at −8 % from entry 93,500, Then the trigger level is 86,020 and the exit fills by the declared rule, never outside [low, high].

**F-084 Comparison screen** · PR-072 · 5 pts · Backlog
- Given N scenarios × M symbols × one period, Then a table of total return, CAGR, max drawdown, Sharpe, trades, fees+tax, win rate, exposure, overlaid equity curves and a benchmark row.

**F-085 Walk-forward ranking with OOS column** · PR-073, G5 · 5 pts · Backlog
- Decision time: the ranking uses window W ending at close of t; the OOS column uses W' starting t+1.
- Given "best of last 7 sessions", Then each row shows the next-7-session result and the statement "in-sample rank ≠ future rank"; a ranking without OOS is not rendered (test).

**F-086 Rolling windows and rank stability** · PR-073 · 3 pts · Backlog
- Given k rolling windows, Then Spearman rank correlation between consecutive in-sample and OOS ranks is shown per window; the R4 documented example uses "best of last 7 days".

**F-087 Survivorship-controlled universe** · PR-075 · 3 pts · Backlog
- Given a start date, Then the universe = symbols listed that day (F-004), including later-delisted; a delisting forces an exit at the last price with a warning.

**F-088 Scenario journal** · PR-078, PR-133 · 3 pts · Backlog
- Given a saved run with parameters, data snapshot and note, When re-run, Then numbers are identical.

**F-089 Portfolio what-if** · PR-035 · 5 pts · Backlog
- Given 10,000,000 split 50/50 across two symbols, Then each leg buys whole lots independently, residual cash is shown per leg, and per-symbol contribution, pairwise correlation and drawdown vs single holdings are shown.

**F-090 Risk metrics** · PR-036, A11 · 3 pts · Backlog
- Given daily returns, Then annualised volatility, max drawdown and duration, Sharpe and time under water are
  shown with formulas; the risk-free rate is editable and defaults to **5 %/year** (A13); e.g. annualised return 12 %,
  volatility 20 % → Sharpe (12 % − 5 %) / 20 % = 0.35.

**F-091 Parameter sensitivity** · PR-074 · 3 pts · Backlog
- Given a parameter grid, Then a heatmap/table shows results and flags an optimum whose neighbours are worse by a stated threshold.

**F-092 CSV export** · PR-134 · 2 pts · Backlog
- Given any table or ledger, Then "Export CSV" produces the same rows and totals.

**F-093 L3/L4/L5 exercises** · PR-112 · 2 pts · Backlog
- Given the scenario screens, Then the docs/04 L3, L4, L5 exercises are offered with saved notes.

---

## R5 — Why it moved (L6)

### E7 Evidence view

**F-100 Market-structure data** · PR-018 · 5 pts · Backlog
- Given each session, Then foreign net buy/sell per symbol and market, proprietary flow `[assumed free source]`,
  index constituents/weights and ETF rebalance dates (manual calendar if no source) are stored with source and fetched-at.

**F-101 Return decomposition** · PR-090 · 5 pts · Backlog
- Decision time: window ends at close of t; beta is estimated on a window that ends before the analysed window starts.
- Given a 7-session return of +10 %, index +4 %, beta 1.2, sector residual +2 %, Then market = 4.8 %, sector 2.0 %, idiosyncratic 3.2 %, method and estimation window shown.

**F-102 Evidence panel** · PR-091 · 5 pts · Backlog
- Given the window, Then dated, sourced items: volume vs 20-day average, ceiling/floor hits, foreign and proprietary flow, ex-dates/events, earnings proximity, rebalance dates, order-book imbalance where snapshots exist.

**F-103 Honesty rules** · PR-093 · 2 pts · Backlog
- Given the view, Then its title is "Các yếu tố đi kèm / Co-occurring factors", each factor shows contribution ± uncertainty, the disclaimer is present, and a wording test rejects causal verbs (list owned by PM).

**F-104 Event study** · PR-094 · 3 pts · Backlog
- Given an event type, Then the average symbol and sector reaction t−5…t+5 is shown with sample size n.

**F-105 Daily market digest** · PR-095 · 3 pts · Backlog
- Given a closed session, Then top movers, breadth, flows, ceiling/floor counts and the day's events are generated from data (no LLM, A4).

**F-106 L6 exercise** · PR-112 · 1 pt · Backlog
- Given the view, Then "explain the 3 strongest sessions of the month with evidence" is offered with saved notes.

---

## R6 — Later (Deferred, rough points, refine after the R5 retro)

### E9 Later

| Story | PR | Pts | One-line acceptance |
|---|---|---|---|
| F-120 News headlines | PR-019 (A9) | 5 | Headline, time, URL, tagged symbols from terms-allowed RSS; no body, no summary |
| F-121 Headline timeline | PR-092 | 3 | Headlines aligned on the price chart, link only |
| F-122 Financial statements and ratios | PR-021 | 8 | Quarterly P/E, P/B, ROE, growth per symbol with as-of |
| F-123 Rule builder | PR-077 | 8 | Composable conditions run through the F-080 engine and look-ahead test |
| F-124 Paper-trading journal | PR-113 | 5 | Entry/exit rules, monthly self-review |
| F-125 Learning progress | PR-114 | 3 | L1–L8 with completed exercises |
| F-126 Odd-lot and cash-advance toggles | PR-038 | 3 | Default off; odd lot buys 1–99 shares (VN§4) |
| F-127 Trade-sequence bootstrap | PR-076 | 3 | Drawdown distribution, not one path |
| F-128 Backup to another disk | PR-136 | 3 | Restore tested once per release; F-021 notice clears |

---

## Traceability PR → F

| PR | Stories | PR | Stories | PR | Stories |
|---|---|---|---|---|---|
| 001 | F-001, F-002, F-006 | 033 | F-047 | 074 | F-091 |
| 002 | F-003 | 034 | F-048 | 075 | F-087 |
| 003 | F-004 | 035 | F-089 | 076 | F-127 |
| 004 | F-005 | 036 | F-090 | 077 | F-123 |
| 010 | F-012, F-013 | 037 | F-050 | 078 | F-088 |
| 011 | F-014 | 038 | F-126 | 090 | F-101 |
| 012 | F-015, F-016 | 039 | F-049 | 091 | F-102 |
| 013 | F-017, F-018 | 050 | F-060, F-061 | 092 | F-121 |
| 014 | F-066, F-067 | 051 | F-062 | 093 | F-103 |
| 015 | F-068 | 052 | F-069 | 094 | F-104 |
| 016 | F-010 | 053 | F-064, F-065 | 095 | F-105 |
| 017 | F-021, F-022 | 054 | F-070 | 110 | F-051 |
| 018 | F-100 | 055 | F-071 | 111 | F-052 |
| 019 | F-120 | 056 | F-063 | 112 | F-054, F-072, F-093, F-106 |
| 020 | F-019, F-034 | 070 | F-057, F-081, F-082, F-083 | 113 | F-124 |
| 021 | F-122 | 071 | F-080 | 114 | F-125 |
| 030 | F-040, F-041, F-053, F-055–F-057 | 072 | F-055, F-056, F-084 | 130 | F-032, F-033, F-056 |
| 031 | F-042 | 073 | F-085, F-086 | 131 | F-030, F-034 |
| 032 | F-043–F-046 | | | 132 | F-020, F-021 |
| | | | | 133 | F-023, F-088 |
| | | | | 134 | F-049, F-092 |
| | | | | 135 | F-011 |
| | | | | 136 | F-021 (notice), F-128 |
| | | | | 137 | F-002, F-031 |

## Open questions for the sponsor

Answered: A13–A15 (2026-10-15) — A13 risk-free default 5 %/year, editable (F-090); A14+A15 default watchlist =
top 30 by average traded value (shares × price), last 20 sessions, refreshed weekly, not VN30 (F-061, F-018).
