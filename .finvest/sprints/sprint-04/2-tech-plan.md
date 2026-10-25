# Sprint 04 — Tech plan (FE / BE / ops; AI blocks merged into dag.json)

Owner: `fi-software-architect`, 2026-10-25, plan v1.0. Inputs: `1-sprint-plan.md`, `product/ux/visual-design.md` (wins on
appearance), `product/ux/app-shell.md`, `product/ux/scenario-dashboard.md`, `2-tech-plan.ai.md` (2 blocks, merged here),
`sprints/sprint-03/5-review.tech.md` T5b/T5c/T6 + smoke note, `6-retro.md` R3/R4, branch `sprint-04` head `50ce8d5`
(= main after the sprint-03 merge; 63 vitest `test(` lines in 13 files, 81 cases).

## Decisions for this sprint

- **CSS = plain CSS files, no library, no new dependency** (visual-design.md §1). `apps/web/src/styles/tokens.css`
  (custom properties only, `:root` light + `@media (prefers-color-scheme: dark)` dark, `color-scheme: light dark`) and
  `apps/web/src/styles/app.css` (elements, `.btn*`, inputs, `.seg`, focus ring, `.num`, motion), both imported in
  `src/main.tsx`. Per-area sheets with **disjoint file sets** so tasks run in parallel: `styles/shell.css` (F-130),
  `features/scenarios/scenarios.css` (page/grid/card/states), `features/scenarios/table.css`, `features/scenarios/panel.css`
  (form + how-computed). No CSS modules (class names already exist and tests query by role/testid, not class). Every
  inline `<style>{CSS}</style>` string and every `style={{…}}` for colour/spacing/font goes away; `style=` stays only
  for computed geometry (sparkline `height`, combobox/menu `position: relative`) — the spec allows it.
- **Token names = visual-design.md §3 verbatim**; the three already referenced (`--color-error`, `--chart-line`,
  `--chart-invested`) are defined there. Existing P/L classes `.up/.down/.zero` keep their names and move to
  `scenarios.css` on `--up/--down/--ref`.
- **Tests see the CSS**: vitest replaces `.css` imports with empty modules, so `src/test/setup.ts` imports every sheet with
  `?raw` and appends one `<style>` to `document.head`. jsdom resolves `getComputedStyle` from `<style>` rules (the TopBar
  24 px test already relies on that); media queries never match in jsdom, so only base rules are testable there.
- **Guards** (F-132 §9.3): vitest `src/styles/guards.test.ts` — (a) every `var(--x)` in `src/**/*.{ts,tsx,css}` is declared
  in `tokens.css` `:root`, and every colour token (value `#…`/`rgb…`) is declared again in the dark block; (b)
  `getComputedStyle(document.body).fontFamily` starts with `system-ui`. **axe contrast in both schemes needs a real browser**
  → the tester's Playwright script (`apps/web/e2e/screens.mjs`), same as the screenshots.
- **Browser for F-132**: Playwright's bundled Chromium is already on the host (`~/.cache/ms-playwright/chromium-1134`,
  installed by the FE tester in S03 from `/tmp/pw`; `/tmp/pw` itself is gone). The tester re-creates the outside-repo install
  (`mkdir /tmp/pw && cd /tmp/pw && npm i playwright@1.47 axe-core@4.10`, no sudo, no download if the cache matches, else
  `npx playwright install chromium` — free). Playwright stays **out of `apps/web/package.json`** (S03 decision; offline build).
- **Crawl status line under the disclaimer band** (§5): `useCrawlJob` holds local state (`refused`, `startError`), so it
  cannot be called twice. Smallest change: `TopBar` returns a fragment `<header class="tb">…</header>` + `<Disclaimer/>` (on
  analysis routes, via `useLocation`) + `<CrawlStatus/>`; `routes.tsx` `Layout` drops its own `<Disclaimer/>`. DOM order
  changes, behaviour and texts do not; `disclaimer.test.tsx` renders the router, so it keeps passing.
- **Hit targets**: spec §3.5 says ≥ 32 px desktop; the TopBar test currently pins `min-height/min-width = 24px` → the shell
  task updates it to `32px` (it is the same WCAG 2.5.8 check with the new value).
- **S04-RW split**: T5b = code (`BE-rw-ledger-rank`); T5c + T6 + VNINDEX smoke = one ops task (`OPS-rw-smoke-dsn`, lead opus
  per owner.md "ops"); the `sell_date` pin lives in the tester's own script, which only exists on `test/sprint-03/fe`
  (`apps/web/e2e/real-stack.mjs`, never merged) → done inside `FE-shots` when the tester brings `e2e/` into `sprint-04`.
  AI-1/AI-3 and AI-2 are the two blocks of `2-tech-plan.ai.md`, unchanged.
- **Sizes** count prod + tests (A22-R3 until A24-D1 is answered); CSS lines count as production; i18n lines are cheap and are
  not what stops a task. FE seats = 2, so tasks are kept ≤ ~230 lines and ordered only where files overlap.

## Order and lanes

```
FE-1  FE-tokens → FE-base → FE-sc-cards (after AI-rw-bench-na too) → FE-shots (tester, manual, after every FE task)
FE-2  AI-rw-bench-na (ai plan, side fe) → FE-guards → FE-shell
FE-3  FE-sc-table → FE-sc-panel                       (both after FE-base)
BE-1  BE-rw-ledger-rank        BE-2  OPS-rw-smoke-dsn        AI-1  AI-rw-curve        (no dependencies)
```
Milestones: M1 = FE-tokens, FE-base, FE-guards, AI-rw-bench-na · M2 = FE-shell, FE-sc-*, AI-rw-curve, BE/OPS · M3 = FE-shots.
L1 (live crawl) is an sm/sponsor clock milestone, not a dag task.

## Tasks

#### FE-tokens — F-129: design tokens (light + dark) and the stylesheet entry points
- Story: F-129 ; Side: fe ; Effort: medium ; Size: ~95 lines ; Lead: sonnet
- Files: `apps/web/src/styles/tokens.css` (new), `apps/web/src/styles/app.css` (new, body/base only — the rest comes in FE-base),
  `apps/web/src/main.tsx`, `apps/web/src/test/setup.ts`
- Change:
  - `tokens.css`: `:root { color-scheme: light dark; … }` with every token of visual-design.md §3.1–§3.5 under its exact name:
    neutrals/roles (`--bg --surface --surface-2 --border --text --text-muted --primary --on-primary --focus --warn --warn-bg
    --color-error --error-bg --ok`), board (`--up --down --ref --ceiling --floor`), chart (`--chart-line --chart-invested
    --chart-point`), type (`--font-sans --font-mono --fs-xs … --fs-xl` as `font-size` px values plus `--lh-xs … --lh-xl`),
    spacing `--sp-1…--sp-7`, radius `--r-sm --r-md --r-pill`, shadows `--shadow-1 --shadow-2`, `--dur: 120ms`.
  - `@media (prefers-color-scheme: dark) { :root { … } }` redefines **every colour token** with the §3 dark values and sets
    `--shadow-1`/`--shadow-2` to `none` (dark uses `--border`).
  - `app.css` (this task only): `body { margin:0; background: var(--bg); color: var(--text); font: 400 var(--fs-md)/var(--lh-md)
    var(--font-sans); }`, `.num, td, th { font-variant-numeric: tabular-nums; }`, `code, pre, .mono { font-family: var(--font-mono); }`.
  - `main.tsx`: `import "./styles/tokens.css"; import "./styles/app.css";` before `./i18n`.
  - `setup.ts`: import the two sheets with `?raw` and append their text in one `<style data-testid="app-css">` to
    `document.head` (feature sheets are added by the tasks that create them, same pattern).
- Contract: product/ux/visual-design.md §2, §3 (names and values are normative; no new names).
- Acceptance: `npm test` + `npm run typecheck` green (81 cases unchanged); `rg -o 'var\(--[a-z0-9-]+' apps/web/src | sort -u`
  lists only names declared in `tokens.css`; `rg -c '^\s*--' tokens.css` ≥ 45 in the light block and every `#`-valued token
  appears twice in the file (light + dark); in a browser at `prefers-color-scheme: dark` the page background is `#111418`.
- Out of scope: buttons, inputs, focus ring, any component edit (FE-base and later tasks), a theme toggle.

#### FE-base — F-129: base elements — buttons, inputs, segmented control, links, focus ring, motion
- Story: F-129 ; Side: fe ; Effort: medium ; Size: ~170 lines ; Lead: sonnet
- Files: `apps/web/src/styles/app.css`, `apps/web/src/styles/app.test.ts` (new)
- Change (visual-design.md §3.5–§3.6, selectors only — components are reclassed in FE-shell / FE-sc-*):
  - `button, .btn`: height 32 px, padding `0 var(--sp-3)`, radius `--r-sm`, `--surface` bg, 1 px `--border`, `--text`, `--fs-md`,
    `font: inherit`, `cursor: pointer`, `transition: background var(--dur), border-color var(--dur)`; `:disabled { opacity:.5;
    cursor: not-allowed }`. `.btn-primary` (light `--primary`/`--on-primary`; dark: transparent bg, `--primary` text + border —
    inside the dark media block), `.btn-danger` (`--color-error` text + border), `.btn-icon` (32×32, padding 0, no border,
    transparent; `.btn-icon.sm` 24×24). Default `button` gets the secondary look, so **no OS grey button survives anywhere**.
  - `input, select, textarea, [role=combobox]`: height 32 px, 1 px `--border`, radius `--r-sm`, `--surface` bg, `--text`, padding
    `0 var(--sp-2)`, `font: inherit`; `[aria-invalid=true] { border-color: var(--color-error) }`; `input[type=radio], [type=checkbox]`
    16 px, `accent-color: var(--primary)`. `.field-error` = `--fs-xs` `--color-error`, `"✕ "` via `::before`.
  - `.seg` (segmented control: `[role=group]` wrappers get this class in later tasks): pill track `--surface-2`, radius `--r-pill`,
    padding 2 px; `.seg button` transparent, radius `--r-pill`, `[aria-pressed=true]` = `--surface` bg, 600 weight, 2 px `--primary`
    bottom border (keeps the non-colour rule).
  - `a { color: var(--primary) }`, underline on hover; `p a, li a { text-decoration: underline }`.
  - `:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px }`; `th button:focus-visible, [role=menuitem]:focus-visible
    { outline-offset: -2px }`; never `outline: none` alone.
  - `@media (max-width: 767px) { button, .btn, input, select, [role=combobox] { min-height: 40px } }`;
    `@media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition: none !important; animation: none !important } }`.
  - `.chip` (pill, `--fs-xs`, `--surface-2`/`--text-muted`; `.chip-warn` = `--warn-bg`/`--warn`), `.visually-hidden` (replaces the
    inline clip style in `states.tsx` later).
  - `app.test.ts`: mounts `app.css` text, asserts `getComputedStyle(button).height === "32px"` and that a `.btn-primary` resolves
    `background-color` to `var(--primary)`'s light value (`rgb(31, 95, 191)`), and `:focus-visible` rule text exists in the sheet
    (jsdom cannot focus-visible; assert the rule via `document.styleSheets`).
- Contract: product/ux/visual-design.md §3.5, §3.6, §8 (focus ring, contrast).
- Acceptance: tests above green; the existing TopBar "24x24" test still passes (its inline rule stays until FE-shell); in the browser
  every `<button>` on /scenarios renders with the §3.6 secondary look without any class.
- Out of scope: component class changes, layout, dark-mode screenshots (tester).

#### FE-guards — F-132: build guards — undefined `var(--x)`, missing dark value, serif body font
- Story: F-132 ; Side: fe ; Effort: medium ; Size: ~55 lines ; Lead: sonnet
- Files: `apps/web/src/styles/guards.test.ts` (new)
- Change:
  - Load sources with `import.meta.glob("/src/**/*.{ts,tsx,css}", { query: "?raw", import: "default", eager: true })` (skip
    `*.test.*` and `tokens.css` itself). Collect `var\(--([a-z0-9-]+)` names; parse `tokens.css` into the light block (before
    `@media (prefers-color-scheme: dark)`) and the dark block; assert every used name is declared in light; assert every light token
    whose value matches `/^(#|rgb)/` is declared in dark too. Failure message lists the offending names and files.
  - Serif guard: with the `setup.ts` sheet mounted, `getComputedStyle(document.body).fontFamily` starts with `system-ui`; also
    assert no `font-family` declaration in any `src/**/*.css` contains `serif` outside `sans-serif`.
  - Prove once (in `3-build.FE-guards.md`): delete `--chart-line` locally → the test fails naming `Sparkline.tsx`; restore.
- Contract: product/ux/visual-design.md §9.3; backlog F-132 "fails when broken (proved once by removing one token)".
- Acceptance: `npm test` green; the proof paragraph is in the build report with the failing assertion text.
- Out of scope: axe (browser-only → FE-shots), screenshots.

#### FE-shell — F-130: top bar, mobile menu, freshness chip, crawl button, disclaimer band, crawl status line
- Story: F-130 ; Side: fe ; Effort: medium ; Size: ~210 lines ; Lead: sonnet
- Files: `apps/web/src/styles/shell.css` (new), `apps/web/src/components/TopBar.tsx`, `apps/web/src/components/TopBar.test.tsx`,
  `apps/web/src/components/CrawlButton.tsx`, `apps/web/src/components/CrawlStatus.tsx`, `apps/web/src/components/Disclaimer.tsx`,
  `apps/web/src/components/FreshnessChip.tsx`, `apps/web/src/components/LangSwitch.tsx`, `apps/web/src/app/routes.tsx`,
  `apps/web/src/test/setup.ts` (add `shell.css?raw`)
- Change (visual-design.md §4–§5):
  - Delete the inline `CSS` strings in `TopBar.tsx` and `CrawlButton.tsx` and every `style=` in these files; `shell.css` holds
    `.tb` (52 px, sticky, `--surface`, bottom `--border`, z-index 20; inner `.tb-inner` max-width 1280, gutter 16/24), `.tb-brand`
    (16 px/700), `.tb-nav a` (`--text-muted`; `[aria-current=page]` = `--text` + 2 px `--primary` underline), `.tb-menu` (hidden ≥ 768,
    40×40 `.btn-icon` below), `.tb-nav[data-open=true]` dropdown sheet under the bar with `--shadow-2`, `.cb-spin` keyframes
    (0.8 s), `.cb-label` hidden < 768 (was 479), `.tb button, .tb a { min-height: 32px; min-width: 32px }` (40 below 768).
  - `FreshnessChip`: `className={"chip" + (stale ? " chip-warn" : "")}`, `"⚠ "` prefix when stale (text, not CSS); below 768 the
    date-only text is a CSS-only concern → render both spans, `.chip-long` hidden < 768 (`title` keeps the full text).
  - `LangSwitch` and the crawl button: `role=group` gets `className="seg"`; the active-language inline bold/underline is now the
    `.seg [aria-pressed=true]` rule. `CrawlButton` keeps `aria-label`; add `className="btn"`.
  - `TopBar` returns a fragment: `<header class="tb">…</header>`, then `<Disclaimer/>` when
    `ROUTES.find(r => r.path === useLocation().pathname)?.analysis`, then `<CrawlStatus …/>`; `routes.tsx` `Layout` no longer
    renders `<Disclaimer/>`. `main` gets `className="page"` (`shell.css`: max-width 1280, centred, gutter 16/24).
  - `Disclaimer`: `className="band"` (`--warn-bg`, `--text`, `--fs-sm`, padding `--sp-2 --sp-4`, leading "ⓘ" span `aria-hidden`), VI
    span 500 weight; texts unchanged (never translated, never dismissible).
  - `CrawlStatus`: `className="status"` + modifier from `job.status` (`status-running | status-done | status-error`); running shows
    the `.cb-spin` glyph and, when `p.total`, a 3 px `.status-bar` whose width is `done/total` (`style={{width}}` is computed geometry,
    allowed); done = "✓" span in `--ok` + dismiss `.btn-icon` at right; error = `--error-bg` row, "✕" + text `--color-error`, the
    `path/source/http` parts wrapped in `<code>` (mono, `--fs-xs`). Texts and i18n keys unchanged.
  - `TopBar.test.tsx`: the 2.5.8 test expects `["32px", "32px"]`; add one assertion that the status line, when a job is running, is
    rendered **after** the disclaimer in document order (`compareDocumentPosition`).
- Contract: product/ux/visual-design.md §4, §5; product/ux/app-shell.md (texts, roles, keyboard — unchanged).
- Acceptance: vitest green incl. `disclaimer.test.tsx` (every analysis route still has exactly one `role=note`), `CrawlButton.test.tsx`
  (accessible name unchanged, icon-only below 768 is CSS); in Chromium at 375 px the bar is one row and
  `document.documentElement.scrollWidth <= 375` (tester, FE-shots).
- Out of scope: a theme toggle, the data-quality page, any scenarios file.

#### FE-sc-cards — F-131: scenarios page header, cards grid, card, card menu, sparkline, states
- Story: F-131 ; Side: fe ; Effort: medium ; Size: ~230 lines ; Lead: sonnet
- Files: `apps/web/src/features/scenarios/scenarios.css` (new), `apps/web/src/features/scenarios/ScenariosPage.tsx`,
  `apps/web/src/features/scenarios/ScenarioCard.tsx`, `apps/web/src/features/scenarios/ScenarioCard.test.tsx`,
  `apps/web/src/features/scenarios/states.tsx`, `apps/web/src/features/scenarios/CardMenu.tsx`,
  `apps/web/src/features/scenarios/Sparkline.tsx`, `apps/web/src/features/scenarios/ViewToggle.tsx`,
  `apps/web/src/components/ApiErrorState.tsx`, `apps/web/src/test/setup.ts` (add `scenarios.css?raw`)
- Change (visual-design.md §6.1–§6.3, §6.7):
  - Move `GRID_CSS`/`CSS` out of `ScenarioCard.tsx` into `scenarios.css` (drop the export and the `<style>` in `ScenariosPage`); grid
    `repeat(1|2|3, minmax(0,1fr))`, gaps 12/16, `align-items: stretch`. `.up/.down/.zero` → `var(--up|--down|--ref)` (names kept).
  - Page header `.sc-head`: title `--fs-xl`; as-of line `--fs-xs` muted (stale → `chip chip-warn`, reuse `isStale` from
    `FreshnessChip.tsx` — import only); right group = `ViewToggle` (`className="seg"`) + Add button `className="btn btn-primary"`;
    < 768 the header wraps into two rows (CSS).
  - Card: `.sc-card` frame (`--surface`, `--border`, `--r-md`, `--shadow-1`, padding `--sp-4`, gap `--sp-2`); head row = name 600 +
    " · style" muted, `CardMenu` trigger `className="btn-icon"`; dates `.muted .fs-sm`; approximate flag `className="chip chip-warn"`;
    figures `dl` rows `.row` (dt muted `--fs-sm`, dd right-aligned `.num`), value row `.headline` (`--fs-xl` 600); P/L spans keep
    `▲/▼/=` + sign; `InfoButton` → `className="btn-icon sm"` muted (edit in `HowComputed.tsx` is **FE-sc-panel's** — pass nothing; style
    it via `.sc-card dd .btn-icon` selector here instead); sparkline block `.spark` (height 48, margin-top `--sp-2`; keep `height` prop);
    benchmarks `ul.bench` with top `--border` divider, rows `.row`, n/a text `.muted` (never coloured); missing-sessions note `.note-warn`
    (`--fs-xs` `--warn`); card error = `.card-error` block (`--error-bg`, "✕", **Sửa** `className="btn"`).
  - `CardMenu`: popover `.menu` (`--surface`, `--shadow-2`, `--r-md`, items 32 px full-width `[role=menuitem]`, "Xoá" `.danger`);
    delete `<dialog>` gets `className="confirm"` with footer buttons `.btn-danger` / `.btn`. Inline `position`/`background`/`border`
    styles removed (keep `position: relative` on the wrapper, geometry).
  - `states.tsx`: Empty/NoBars = one `.sc-card.sc-center` (max 480 px, centred in the grid area), command in `<code>` on `--surface-2`,
    Add `btn btn-primary` (disabled look for NoBars); `Skeleton` = `.sc-card.skeleton` with 4 `.sk` blocks and a 1.2 s opacity
    `@keyframes pulse` (off under reduced motion), `aria-busy` stays; visually-hidden text uses `.visually-hidden`.
  - `ApiErrorState`: `.api-error` block (max 560 px, `--error-bg`, "✕", message, **Thử lại** `className="btn"`); `ScenariosPage`'s generic
    `role=alert` branch gets the same class.
  - `ScenarioCard.test.tsx`: the tests from AI-rw-bench-na stay; add one assertion that the approximate flag element has class `chip-warn`
    and that the value `dd` has class `headline` (presentation hooks the tester's checklist relies on).
- Contract: product/ux/visual-design.md §6.1–§6.3, §6.7; product/ux/scenario-dashboard.md (texts, order, states — unchanged).
- Acceptance: vitest green (`ScenariosPage.test`, `ScenarioCard.test`, `Sparkline.test` unchanged in behaviour); in Chromium 1 / 2 / 3
  columns at 375 / 800 / 1280 (tester); no `style=` left in these files except `position: relative` wrappers and the sparkline height.
- Out of scope: table, form, how-computed (FE-sc-table, FE-sc-panel), benchmark wording (AI-rw-bench-na, merged before this).

#### FE-sc-table — F-131: table view look
- Story: F-131 ; Side: fe ; Effort: medium ; Size: ~110 lines ; Lead: sonnet
- Files: `apps/web/src/features/scenarios/table.css` (new), `apps/web/src/features/scenarios/ScenarioTable.tsx`,
  `apps/web/src/features/scenarios/ScenarioTable.test.tsx`, `apps/web/src/test/setup.ts` (add `table.css?raw`)
- Change (visual-design.md §6.4):
  - Move the inline `CSS` string to `table.css`: `.sc-tablewrap` (`--surface`, 1 px `--border`, `--r-md`, `overflow-x: auto`),
    `border-collapse: separate; border-spacing: 0`, header `--surface-2` `--fs-xs` 500 muted sticky top inside the wrap, body rows
    36 px `--fs-sm` bottom `--border`, hover `--surface-2`, `.num` right/tabular, `.sticky` (left 0, `--surface`, right border) only
    `@media (max-width: 1023px)`.
  - Header sort buttons: `className="th-btn"` filling the cell (no border, inherits), active column shows ▲/▼ (already), inactive shows
    a faint "↕" span `.sort-hint` visible on hover/focus-within (`aria-hidden`).
  - P/L ₫ and % cells: add the `▲/▼/=` + sign + `.up/.down/.zero` rule by reusing the card's `arrow`/`cls` logic (copy the two one-liners
    locally; do not import from `ScenarioCard.tsx`, FE-sc-cards edits it). Flag cell: "⚠" with `title`/`aria-label` "Gần đúng"
    (`t("table.approximate")` already exists) in `--warn`. Footer note `.muted .fs-xs`.
  - Test: the P/L ₫ cell of a losing row contains "▼ −" and class `down`; sort behaviour tests unchanged.
- Contract: product/ux/visual-design.md §6.4; product/ux/scenario-dashboard.md "Table view" (columns, sort, sticky — unchanged).
- Acceptance: `ScenarioTable.test.tsx` green with the new assertion; only `.sc-tablewrap` scrolls sideways at 375 (tester).
- Out of scope: the benchmark cell wording (stays bare `n/a`, AI plan decision), column set, TanStack Table.

#### FE-sc-panel — F-131: add/edit side panel, symbol combobox, how-computed drawer
- Story: F-131 ; Side: fe ; Effort: medium ; Size: ~190 lines ; Lead: sonnet
- Files: `apps/web/src/features/scenarios/panel.css` (new), `apps/web/src/features/scenarios/ScenarioForm.tsx`,
  `apps/web/src/features/scenarios/ScenarioForm.test.tsx`, `apps/web/src/features/scenarios/SymbolCombobox.tsx`,
  `apps/web/src/features/scenarios/HowComputed.tsx`, `apps/web/src/test/setup.ts` (add `panel.css?raw`)
- Change (visual-design.md §6.5–§6.6):
  - `panel.css`: `.scenario-panel` = right drawer **from 768 px** (was 1024; spec §6.5), width 440 px max 100 vw, full height,
    `--surface`, `--shadow-2`, left `--border`, `::backdrop`/`.backdrop` `rgba(0,0,0,.32)`, 160 ms slide-in (none under reduced
    motion); < 768 full-screen sheet. `.panel-head` sticky (title `--fs-lg` + close `.btn-icon`), `.panel-body` one column gap
    `--sp-4`, `.field` (label above, `--fs-sm` 500; hint/error below `--fs-xs`), `.amount` right-aligned tabular with "₫" suffix
    (`.suffix` span inside a `.input-wrap`), `.radio-row` (two stacked option rows, 16 px radio), `.panel-foot` sticky bottom with
    top `--border`, buttons right-aligned (Lưu `.btn-primary` last; stacked full-width, Lưu on top, < 768).
  - `ScenarioForm.tsx`: delete the inline `<style>`; error `<p>` → `className="field-error"` (the `var(--color-error, crimson)` inline
    style goes); markup gains `div.field` wrappers and the head/foot sections; a close ✕ `.btn-icon` in the head (`aria-label` =
    `t("form.cancel")`), the existing Huỷ button stays in the footer. Below-one-lot hint stays out (shortcut comment unchanged).
  - `SymbolCombobox.tsx`: listbox `.combo-list` (`--surface`, `--border`, `--shadow-2`, `--r-sm`, max-height 240, `z-index 1`),
    `[aria-selected=true]` row = `--surface-2` + 600 (replaces `Highlight/HighlightText` inline); keep `position: relative` wrapper.
  - `HowComputed.tsx`: `className="scenario-panel how"` (same drawer; `showModal()` kept), head/body/foot sections as the form, formula
    `<code>` → `.formula` block (`--surface-2`, `--r-sm`, padding `--sp-3`, mono `--fs-sm`, `white-space: pre-wrap; overflow-wrap:
    anywhere`), inputs table → `dl.rows` like the card, as-of/rules/basis rows `.muted .fs-xs`, approximate note `.note-warn-block`
    (`--warn-bg`, ⚠). `InfoButton` → `className="btn-icon sm"` with text "(i)" unchanged.
  - Tests: `ScenarioForm.test.tsx` — the error paragraph has class `field-error` and `role=alert` (existing lookups by role keep working);
    `HowComputed.test.tsx` unchanged (role/text based).
- Contract: product/ux/visual-design.md §6.5, §6.6; product/ux/scenario-dashboard.md "Add / edit form", "How computed" (fields, errors,
  keyboard — unchanged; the drawer breakpoint 1024 → 768 is the spec's appearance rule and wins).
- Acceptance: vitest green; at 1280 the drawer is 440 px with a backdrop, at 375 full screen with stacked buttons, the formula block
  wraps without sideways scroll (tester).
- Out of scope: form validation rules, new fields, the live below-one-lot hint.

#### FE-shots — F-132: screenshot + axe script, 28 shots, §9.2 checklist, e2e scripts carried into sprint-04 (incl. `sell_date` pin)
- Story: F-132 ; Side: fe ; Effort: medium ; Size: ~220 lines ; Lead: sonnet ; **manual: true (fi-fe-tester, /fi-test)**
- Files: `apps/web/e2e/screens.mjs` (new), `apps/web/e2e/real-stack.mjs` + `apps/web/e2e/crawl-button.mjs` (copied from
  `origin/test/sprint-03/fe`, first time on a sprint branch), `.finvest/sprints/sprint-04/screens/*.png` (28 + 1 focus shot),
  `.finvest/sprints/sprint-04/4-test.fe.md`
- Change:
  - `screens.mjs` (run `PW_DIR=/tmp/pw node apps/web/e2e/screens.mjs`, stack on `127.0.0.1:8080`, `flock /tmp/fi-e2e.lock`): for
    viewports 375×812 and 1280×800 × `colorScheme` light/dark, screens (a)–(g) of visual-design.md §9.1 with `page.route('**/api/**')`
    mocks for empty / API-down / crawl running / crawl error / one P/L-down card; one extra 1280-light shot with focus on Add; files
    `<screen>-<375|1280>-<light|dark>.png`. Same run: `axe-core` (`/tmp/pw/node_modules/axe-core/axe.min.js` injected) on /scenarios, the
    open form and the how-computed drawer, both schemes, `rules: color-contrast` → 0 violations asserted; `scrollWidth <= 375` asserted
    on every 375 shot; `getComputedStyle(body).fontFamily` starts with `system-ui`.
  - `real-stack.mjs`: FPT lump-sum case sends an explicit `sell_date` (a pinned past bar day) so its expected numbers stop drifting
    (S04-RW "E2E pin"; retro S03 #5). Expected values recomputed once from `/api/whatif` and written next to the case with the date.
  - `4-test.fe.md`: the §9.2 checklist, one pass/fail line per shot, and the files list; browser install line (Chromium 1134 from the
    Playwright cache, no download when present).
- Contract: product/ux/visual-design.md §9 (files, checklist, guards); 1-sprint-plan.md "Definition of Done — addition for UI stories".
- Acceptance: 28 png files present and listed; every §9.2 line marked; axe 0 `color-contrast` in both schemes; `real-stack.mjs` passes
  twice on different days with the same expected numbers (the pin works); nothing added to `apps/web/package.json`.
- Out of scope: visual-regression diffs (pixel compare), CI wiring of Playwright (the vitest guards are the CI part).

#### BE-rw-ledger-rank — S04-RW T5b: `crawl_sessions` upsert never lowers the status rank
- Story: S04-RW ; Side: be ; Effort: high ; Size: ~25 lines ; Lead: sonnet
- Files: `packages/market_data/finvest_market_data/infrastructure/repositories.py`, `packages/market_data/tests/test_repositories_db.py`
- Change:
  - In `upsert_crawl_session` the `where` becomes `rows >= stored AND rank(EXCLUDED.status) >= rank(stored.status)` with
    rank `complete=3, partial=2, blocked=2, missed=1` (any other value 0), expressed as a SQLAlchemy `case()` on both sides — no
    schema change, no migration.
  - One `-m db` test: upsert `complete` (rows 4_949) then `blocked` (rows 10_357) for the same `(feed, trading_date)` → the row stays
    `complete` with rows 4_949; then `complete` with rows 5_000 → updated (rank equal, rows higher); `partial` with fewer rows → unchanged.
- Contract: architecture/data.md §3 `crawl_sessions` (ledger semantics "richest replay wins"; this adds the status ordering noted in
  sprint-03/5-review.tech.md T5b).
- Acceptance: `make test` db suite green with the new test (run on a `*_test` DB, see OPS-rw-smoke-dsn's DSN); kernel unchanged.
- Out of scope: repairing existing rows (the 10-23 row is fixed by the next complete press), readers of the ledger.

#### OPS-rw-smoke-dsn — S04-RW T5c + T6 + VNINDEX smoke: one test DSN for the tester, a `make smoke`, the orphan row deleted
- Story: S04-RW ; Side: be ; Effort: medium ; Size: ~70 lines ; Lead: opus
- Files: `Makefile`, `docker-compose.yml`, `.env.example`, `ops/smoke.sql` (new), `ops/README.md`, `README.md` (run section, 2 lines)
- Change:
  - **T6 / S02 B4**: publish the compose db on loopback only (`127.0.0.1:55432:5432`); new target `make test-db` that
    `createdb`s `finvest_test` (idempotent: `|| true`) and runs `FINVEST_DATABASE_URL=postgresql+psycopg://finvest:$(POSTGRES_PASSWORD)
    @127.0.0.1:55432/finvest_test uv run pytest -m db -q` with `POSTGRES_PASSWORD` read from `.env`. `ops/README.md` documents the DSN,
    the per-branch variant (`FINVEST_TEST_DB=finvest_test_<branch>`, honoured by the target) and the one-time repair when the role password
    drifted from `.env`: `make db-shell` → `ALTER ROLE finvest PASSWORD '<.env value>';` (the T6 root cause).
  - **Smoke**: `ops/smoke.sql` = (1) VNINDEX unit check `SELECT trading_date, value, v, value / NULLIF(v,0) AS ratio FROM index_1d WHERE
    index_code='VNINDEX' AND (value / NULLIF(v,0) NOT BETWEEN 100 AND 1e7 OR v IS NULL) ORDER BY 1 LIMIT 20` (expected 0 rows;
    sprint-03 review "ratio query"; columns per `tables.py`: `index_code, trading_date, o, h, l, c, v, value`), (2) weekend ledger rows `SELECT * FROM crawl_sessions WHERE extract(isodow FROM trading_date) > 5`
    (expected 0 rows), (3) last `crawl_runs` row and the last 3 `crawl_sessions` per feed. `make smoke` runs it through
    `docker compose exec -T db psql -U finvest finvest -f -`. No new columns.
  - **T5c**: run `DELETE FROM crawl_sessions WHERE feed='bars_1d' AND trading_date='2026-10-24'` once on the live db via `make db-shell`
    (expect `DELETE 1`), log the command, the date and the result in `ops/README.md` "Manual fixes" (new, dated list).
- Contract: ops/README.md (owner: ops); architecture/data.md §3 (names only); no API or schema change.
- Acceptance: `make test-db` runs the 26+1 db tests green on this host as `fi-be-tester` (log line in `4-test.be.md`); `make smoke`
  prints 0 rows for checks (1) and (2) after T5c; `README.md` run section mentions `make test-db` and `make smoke`.
- Out of scope: a CI pipeline, test fixtures with real data, any crawler code.

#### AI-rw-curve — S04-RW AI-1 + AI-3 (see `2-tech-plan.ai.md`)
- Story: S04-RW ; Side: ai ; Effort: medium ; Size: ~25 lines ; Lead: sonnet — block text and acceptance are in `2-tech-plan.ai.md`
  (`task.sh AI-rw-curve` reads that file). Files: `services/analytics/finvest_analytics/sim/whatif.py`,
  `services/analytics/tests/test_whatif_lumpsum.py`. No dependency.

#### AI-rw-bench-na — S04-RW AI-2, F-048 wording (see `2-tech-plan.ai.md`)
- Story: S04-RW ; Side: fe ; Effort: medium ; Size: ~40 lines ; Lead: sonnet — block in `2-tech-plan.ai.md`. Files:
  `ScenarioCard.tsx`, `ScenarioCard.test.tsx`, `i18n/vi.json`, `i18n/en.json`. Runs **first** in FE-2 (priority 1, no `after`);
  `FE-sc-cards` lists it in `after` because both edit `ScenarioCard.tsx` / `ScenarioCard.test.tsx`.

## Risks seen from the plan
1. jsdom + CSS: if `?raw` injection does not drive `getComputedStyle` for a property, the affected assertion moves to the Playwright
   script (FE-shots) and the vitest guard keeps the static checks — no task is blocked.
2. `TopBar` now owns the disclaimer band: the per-route rule stays in `ROUTES[].analysis`; `disclaimer.test.tsx` is the regression net.
3. Drawer breakpoint 1024 → 768 and status line position are appearance changes mandated by visual-design.md; the PM review sees them in
   the 800 px shot.
4. Contrast of `--ref`/`--floor` in dark: values are the spec's; axe in FE-shots is the proof, a failure is `backlog` (spec), not `build`.
