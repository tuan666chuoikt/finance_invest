# Sprint 05 — FE test report (fi-fe-tester, 2026-10-26)
Head: `origin/sprint-05` aedaf0c (worktree `test-fe-05`, branch `test/sprint-05/fe`). Stack: BE tester's `finvest-test-be` (web :18080, api :18001); not started/stopped by me. Crawl calls mocked (no real press).
**Verdict: FAIL** — one FE bug (F-05-1, DCA card shift lines). Everything else PASS.

## Runs
| Run | Result |
|---|---|
| vitest (apps/web, incl. guards.test.ts, app.test.ts) | 14 files / 93 tests pass |
| tsc --noEmit | exit 0 |
| e2e/screens.mjs (375+1280, light+dark, axe color-contrast + all-rules on cards, focus rings, mocks) | 138 pass / 0 fail |
| e2e/fe05-widths.mjs (new, 768/800/375/1280 x light/dark: top bar, header, columns, th lines, DCA lines, crawl running+done, axe) | 80 pass / 8 fail (all = F-05-1) |
| e2e/real-stack.mjs (real api) | 40 pass / 0 fail |
| e2e/crawl-button.mjs | ALL PASS |

## Coverage map
| Item | Test | Result |
|---|---|---|
| FE-crawl-step3: running "Bước 3/3 — sự kiện quyền: 18/40 mã" | widths + screens (8 viewport/scheme combos) | PASS |
| done line: "+3 sự kiện quyền (1 thay đổi) · 2 mã bỏ qua · 12 mã chờ lượt sau · 3 phút 41 giây" (deferred 5+7) | widths mock sequence running->done, 8 combos | PASS (text = app-shell.md) |
| failed at step 3, VCI IQ, "đã lưu 891/39 mã" | screens + real failed job on stack | PASS |
| FE-rw OBS-7: top bar one line (h=53, no label wrapped) at 768 and 800, light+dark | widths | PASS |
| table header labels <=2 lines at 1280 (all 12 headers 1 line) | widths | PASS |
| table "so với VN-Index / so với E1VFVN30" + footer note | shot FE-rw-table-1280 | PASS |
| DCA card shows one shift line | widths + real api | **FAIL F-05-1** |

## visual-design.md §9 checklist (375 / 768 / 800 / 1280, light + dark)
| Line | Result |
|---|---|
| no serif, no default grey button, bg matches scheme | PASS |
| columns 1 @375, 2 @800 (and 768), 3 @1280; no hscroll @375 (scrollWidth 375) | PASS |
| P/L ▲/▼/= + sign + colour; approx chip; benchmarks muted; table figures right-aligned | PASS |
| top bar one line 375/768/800/1280; disclaimer band visible; page header single line | PASS |
| table headers <=2 lines @1280 | PASS |
| **DCA card at most one shift line** | **FAIL (5 lines)** |
| focus ring on Add / toggle / card (i) / form field | PASS |
| guards: var(--x) defined, body font not serif, axe color-contrast 0 (cards, form, how, table, empty, crawl, api-error, nobars, both schemes) | PASS |
Shots: `shots/FE-test/` (cards, FE-rw-table, FE-rw-dca-details, crawl-running, crawl-done at 375/768/800/1280 x light/dark; plus screens.mjs set; metrics.json).

## Bugs
### F-05-1 (medium, owner stage: build, FE-rw) — DCA card prints one line per contribution shift, labelled "Ngày bán dời sang"
Steps: create DCA scenario HPG, 2.000.000 monthly, buy 2025-03-03, sell 2026-10-16; open /scenarios (any width).
Expected (visual-design §9, FE-rw): one line "Ngày mua dời sang ngày giao dịch kế tiếp: 5 lần" with `<details>`.
Actual: 5 lines "Ngày bán dời sang 05/05/2025 ..." (see `shots/FE-test/cards-800-light.png`).
Cause: the API emits DCA shifts as `field: "contribution"` (analytics `sim/dca.py`, `sim/whatif.py`); `ScenarioCard.tsx` (line ~44) only aggregates `field === "buy_date"` and sends every other field to `card.shift_sell`. Vitest fixture used `buy_date` so it passed. Two defects: not aggregated, and mislabelled as sell-date shifts (misleading). Fix: treat `contribution` as the DCA buy shift (count, `from -> to` details) and add a vitest using the real API shape.

## Notes
- B-05-1 (BE adjusted prices) numbers not re-reported; cards show "Gần đúng" chips as expected.
- Build note question (sell_date shift on DCA = own second line): acceptable by spec ("at most one shift line" is about the buy shift); not tested because API gives `contribution` for DCA sell shifts too only when none exist.
- Test added: `apps/web/e2e/fe05-widths.mjs` (768/800 + done-state + th/DCA metrics).
