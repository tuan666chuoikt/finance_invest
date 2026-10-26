# UX — Visual design (all screens)

Stories: F-129 (tokens + base stylesheet), F-130 (shell layout), F-131 (scenarios screen), F-132 (visual acceptance
check). Sponsor request A25 (2026-10-25). S05 additions (2026-10-26): 768–1023 top bar, DCA shift line, header labels, 768/800 shots. Owner: `fi-pm`. Behaviour, texts and states stay as in `ux/app-shell.md`
and `ux/scenario-dashboard.md`; this file defines only **how things look**. Where a screen spec and this file
disagree on appearance, this file wins.

Root cause (A25): no stylesheet exists in `apps/web`; the app renders with browser defaults (Times, grey buttons).
`var(--chart-line)`, `var(--chart-invested)`, `var(--color-error)` are referenced but never defined.

## 1. Principles
- **Calm, data-dense, readable.** A learning tool, not a trading terminal: neutral surfaces, colour reserved for
  meaning (up / down / reference / ceiling / floor / warning / error / focus / primary action).
- **Never colour only.** Every coloured value also has an icon or sign (▲ ▼ = ⚠ ✓ ✕) or text.
- **Numbers line up.** Money and percentages use tabular numerals and right alignment in tables.
- **Vietnamese first.** Layout must fit VI labels, which are ~20–30 % longer than EN ("Giá trị nếu bán",
  "Mua định kỳ hàng tháng"); no fixed widths on labels, text wraps rather than truncates (except table cells, §6.6).
- No new dependencies, no CSS framework, no web fonts (offline, local-first). Plain CSS files.

## 2. Implementation rules (for the FE owner)
- Files: `apps/web/src/styles/tokens.css` (custom properties only) and `apps/web/src/styles/app.css` (elements +
  components), both imported once in `src/main.tsx`. Optional per-feature file `features/scenarios/scenarios.css`.
- Use the class names that already exist (`tb`, `tb-nav`, `tb-menu`, `cb-spin`, `cb-label`, `sc-grid`, `sc-card`,
  `sc-tablewrap`, `scenario-panel`, `row`, `num`, `sticky`); add classes where an element has none. Inline `style=`
  for colour, spacing or font is removed (the Sparkline/ScenarioForm `var(--x, fallback)` stays valid once tokens exist).
- Every `var(--…)` used in `src/` is defined in `tokens.css` for light **and** dark (check in §9).
- Theme = `prefers-color-scheme` only (no toggle in S04). `color-scheme: light dark` on `:root` so native
  controls (date input, scrollbars, select) follow.

## 3. Design tokens

### 3.1 Colour — neutrals and roles
| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | `#f5f6f8` | `#111418` | page background |
| `--surface` | `#ffffff` | `#1a1e24` | cards, top bar, panel, table |
| `--surface-2` | `#eef0f3` | `#232831` | table header, hover row, skeleton, segmented off |
| `--border` | `#d8dce2` | `#343b46` | 1 px borders, dividers |
| `--text` | `#1a1d23` | `#e6e8eb` | body text, figures |
| `--text-muted` | `#5a6371` | `#9ba4b0` | labels ("Đã đầu tư"), dates, captions |
| `--primary` | `#1f5fbf` | `#6ea8ff` | primary button bg (light) / text+border (dark), links, active nav |
| `--on-primary` | `#ffffff` | `#0d1b33` | text on primary bg |
| `--focus` | `#1f5fbf` | `#8ab8ff` | focus ring |
| `--warn` / `--warn-bg` | `#8a5a00` / `#fff4d6` | `#f0c050` / `#3a2e10` | stale chip, approximate flag, disclaimer band |
| `--color-error` / `--error-bg` | `#b3261e` / `#fdecea` | `#ff8a80` / `#3b1a1a` | field errors, error states, crawl error line |
| `--ok` | `#0a7d38` | `#4cd07d` | crawl done ✓ |

### 3.2 Colour — VN board convention (VN§3)
| Token | Meaning | Light (text on `--surface`) | Dark | Non-colour cue |
|---|---|---|---|---|
| `--up` | price / P/L up | `#0a7d38` green | `#4cd07d` | ▲ and `+` sign |
| `--down` | price / P/L down | `#c62828` red | `#ff6b6b` | ▼ and `−` sign |
| `--ref` | unchanged / reference | `#8a6500` dark yellow | `#e6c229` yellow | `=` or "TC" |
| `--ceiling` | ceiling price (trần) | `#7b2fa8` purple | `#c792ff` | "Trần" label / ⤒ |
| `--floor` | floor price (sàn) | `#00727f` cyan | `#33d1e0` | "Sàn" label / ⤓ |
Light values are dark enough for text on white (target ≥ 4.5:1; the yellow and cyan are darkened on purpose, a pure
#ffd700 / #00bcd4 fails on white). Ceiling/floor are defined now for the board (R3) even though S04 screens use only
up/down/ref. P/L zero uses `--ref`.

### 3.3 Chart
| Token | Light | Dark | Use |
|---|---|---|---|
| `--chart-line` | `#1f5fbf` | `#6ea8ff` | equity curve (2 px) — neutral, not green/red, so it reads the same up or down |
| `--chart-invested` | `#8a93a0` | `#6b7480` | dashed invested line / DCA step line (1 px, `stroke-dasharray: 4 3`) |
| `--chart-point` | `--chart-line` | | hover/focus dot, 6 px |

### 3.4 Typography
- `--font-sans: system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", "Helvetica Neue", Arial, sans-serif`
  (all render Vietnamese diacritics; no Times anywhere). `--font-mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace`
  for commands like `make backfill`.
- `.num`, every money / % / date figure, and all table cells: `font-variant-numeric: tabular-nums;`.

| Token | Size / line-height / weight | Use |
|---|---|---|
| `--fs-xs` | 12 px / 16 / 400 | captions, shift notices, footer note, chip |
| `--fs-sm` | 13 px / 18 / 400 | labels, table body, status line, disclaimer |
| `--fs-md` | 14 px / 20 / 400 | body, inputs, buttons (base `html { font-size: 14px }` is not changed; use px tokens) |
| `--fs-lg` | 16 px / 22 / 600 | card title "FPT · Mua một lần", panel title |
| `--fs-xl` | 20 px / 28 / 600 | page title "Kịch bản đầu tư"; card headline value "Giá trị nếu bán" figure |
Weights: 400 body, 500 labels in tables/headers, 600 titles and headline figures. No italics for meaning.

### 3.5 Spacing, radius, shadow, motion
- Spacing scale (4 px base): `--sp-1 4px · --sp-2 8px · --sp-3 12px · --sp-4 16px · --sp-5 24px · --sp-6 32px · --sp-7 48px`.
  Card padding `--sp-4`; grid gap `--sp-4`; page gutter 16 px (< 768) / 24 px (≥ 768); content max-width 1280 px, centred.
- Radius: `--r-sm 4px` (inputs, chips, buttons), `--r-md 8px` (cards, panel, table wrap), `--r-pill 999px` (segmented control, freshness chip).
- Shadow: `--shadow-1: 0 1px 2px rgba(16,24,40,.06), 0 1px 3px rgba(16,24,40,.10)` (cards, light);
  `--shadow-2: 0 8px 24px rgba(16,24,40,.18)` (side panel, menu). Dark: shadows off, use `--border` instead.
- Motion: 120 ms ease for hover/focus; spinner 0.8 s linear; `@media (prefers-reduced-motion: reduce)` → no
  transitions, spinner replaced by a static ⟳.
- Hit targets ≥ 32 px high on desktop, ≥ 40 px at < 768 px.

### 3.6 Base elements
- `body`: `--bg`, `--text`, `--font-sans`, `--fs-md`, margin 0.
- Buttons: `.btn` (secondary: `--surface` bg, 1 px `--border`, `--text`), `.btn-primary` (light: `--primary` bg,
  `--on-primary` text; dark: transparent bg, `--primary` text + border), `.btn-danger` (Xoá: `--color-error` text +
  border), `.btn-icon` (32×32, for ⋯ and (i)). Height 32 px, padding 0 `--sp-3`, radius `--r-sm`. Disabled: 50 %
  opacity + `cursor: not-allowed`. No default grey OS buttons anywhere.
- Inputs/select/combobox: height 32 px (40 px mobile), 1 px `--border`, radius `--r-sm`, `--surface` bg; invalid =
  `--color-error` border + message below in `--fs-xs` `--color-error` with "✕ " prefix.
- Segmented control (VI | EN, Thẻ | Bảng): pill, `--surface-2` track; the active segment = `--surface` bg + 600 weight +
  2 px bottom underline in `--primary` (keeps the "bold + underlined" non-colour rule of app-shell.md).
- Links: `--primary`, underline on hover and always inside body text.
- **Focus ring** (all interactive elements): `outline: 2px solid var(--focus); outline-offset: 2px;` on `:focus-visible`;
  never `outline: none` without this replacement. Inside the table header buttons and card menu items the ring sits inset
  (`outline-offset: -2px`) so it is not clipped.

## 4. Top bar (F-130)
- Full width, height 52 px, `--surface`, bottom 1 px `--border`, sticky top 0, z-index above content.
- Inner row max-width 1280 px: **Finvest** (16 px / 700, `--text`) · nav links (`--fs-md`, `--text-muted`; active =
  `--text` + 2 px `--primary` underline + `aria-current="page"`) · flexible gap · freshness chip · crawl button ·
  VI | EN.
- Freshness chip: pill, `--fs-xs`, `--surface-2` bg, `--text-muted`; stale → `--warn-bg` bg, `--warn` text, "⚠ " prefix.
- Crawl button: `.btn` with ⟳ icon; running → spinner + "Đang cào…", disabled styling but full opacity text.
- < 768 px: nav collapses into the `tb-menu` button (☰, 40×40) that opens a dropdown sheet under the bar (`--shadow-2`);
  chip shows date only ("15/10 15:42"); crawl button icon-only ⟳ (accessible name unchanged); VI | EN stays visible.
  Nothing wraps to a second bar line; no horizontal scroll at 375 px.
- **768–1023 px (S05-RW, OBS-7):** nav links stay inline but the brand and links use `white-space: nowrap`; the
  freshness chip shows date only (as < 768) and the crawl button is icon-only ⟳ with the same accessible name, so the
  bar stays **one line** at 768 and 800. Any item label wraps inside itself = fail ("⟳ Cào dữ liệu" on 2 lines was OBS-7).

## 5. Disclaimer band and crawl status line (F-130)
- Disclaimer: full-width band under the top bar, `--warn-bg` bg, `--text` text (not `--warn`, for long-text
  readability), `--fs-sm`, padding `--sp-2` `--sp-4`, leading "ⓘ" icon. Two lines when they do not fit:
  "Mô phỏng để học, không phải lời khuyên đầu tư" / "Educational simulation, not investment advice" — VI first, VI in 500 weight.
  Not sticky (scrolls away), not dismissible.
- Crawl status line (`role="status"`): a slim row (min 36 px) under the band, `--surface` bg, bottom `--border`,
  `--fs-sm`. Running: spinner + text in `--text`, a 3 px progress bar under the text in `--primary` when the step has a
  count (12/30). Done: "✓" in `--ok` + text in `--text` + "Chi tiết" link + dismiss ✕ button at right. Error: `--error-bg` bg,
  "✕" + text in `--color-error`, path/cause in `--font-mono` `--fs-xs`; no auto-dismiss. Text wraps on mobile.

## 6. Scenarios screen (F-131)

### 6.1 Page header
- Row under the shell, padding `--sp-5` 0 `--sp-4`: title "Kịch bản đầu tư" (`--fs-xl`) · "Dữ liệu đến 23/10/2026 · nguồn VCI"
  (`--fs-xs`, `--text-muted`; stale → warn chip as §4) · right side: Thẻ | Bảng segmented · **+ Thêm kịch bản** (`.btn-primary`).
- < 768 px: title row, then a second row with toggle (left) and Add (right, full label kept).

### 6.2 Cards grid
| Viewport | Columns | Gap | Gutter |
|---|---|---|---|
| < 768 px (incl. 375) | 1 | 12 px | 16 px |
| 768–1023 px | 2 | 16 px | 24 px |
| ≥ 1024 px | 3 | 16 px | 24 px (content max 1280) |
`.sc-grid { display: grid; grid-template-columns: repeat(N, minmax(0, 1fr)); }` — equal-height cards per row (`align-items: stretch`).

### 6.3 Card
- `--surface`, 1 px `--border`, radius `--r-md`, `--shadow-1` (light), padding `--sp-4`, vertical rhythm `--sp-2`.
- Line 1: "FPT" 600 + " · Mua một lần" `--text-muted`, ⋯ `.btn-icon` at right. Line 2: dates `--fs-sm` `--text-muted`.
  Shift notice `--fs-xs` `--text-muted`. **DCA (S05-RW):** at most one shift line: "Ngày mua dời sang ngày giao dịch kế
  tiếp: 5 lần" / "Buy date moved to the next trading day: 5 times" with a "Xem" toggle that lists the dates; lump sum
  keeps its single line.
- Approximate flag: inline chip, `--warn-bg` bg, `--warn` text, `--fs-xs`, radius `--r-sm`, "⚠ ≈ Gần đúng — …"; wraps.
- Figures as a 2-column label/value list (label left `--text-muted` `--fs-sm`; value right, tabular, `--fs-md`):
  Đã đầu tư · **Giá trị nếu bán** (value `--fs-xl` 600, the card headline) · Lãi/Lỗ (₫ and %, each `▲ +` / `▼ −` / `=` in
  `--up` / `--down` / `--ref`) · Tiền mặt còn. (i) is a 24 px `.btn-icon` after the value, `--text-muted`.
- Sparkline: full card width × 48 px, top margin `--sp-2`; line `--chart-line`, invested `--chart-invested` dashed.
- Benchmarks: separated by a 1 px `--border` top divider; each row "VN-Index" `--fs-sm` muted · "▲ +5,00 %" coloured ·
  "(+1,11 điểm %)" `--fs-xs` muted. "n/a — thiếu dữ liệu ETF trong kỳ" in `--text-muted`, never coloured, never 0.
- Card error ("Không tính được: …"): card keeps its frame; body is an `--error-bg` block with ✕ + reason + **Sửa** `.btn`.
- Card menu (⋯): popover `--surface`, `--shadow-2`, radius `--r-md`, items 32 px; "Xoá" in `--color-error`.

### 6.4 Table view
- Inside `.sc-tablewrap`: `--surface`, 1 px `--border`, radius `--r-md`, `overflow-x: auto` (the page never scrolls sideways).
- `border-collapse: separate; border-spacing: 0`; header row `--surface-2`, `--fs-xs` 500 uppercase-free, `--text-muted`,
  sticky top inside the wrap; body rows 36 px, `--fs-sm`, 1 px `--border` bottom; hover row `--surface-2`; zebra off.
- Numeric columns (Invested, Value, P/L ₫, P/L %, vs … pp) right-aligned, tabular; text columns left. P/L cells use the
  ▲/▼/= + colour rule. Flag column: "⚠" in `--warn` with `title`/`aria-label` "Gần đúng".
- Sort: header is a button filling the cell; the active column shows ▲/▼ after the label and `aria-sort`; inactive shows a
  faint ↕ on hover/focus.
- Name column `.sticky` (left 0, `--surface` bg, right border) at < 1024 px. Footer note `--fs-xs` muted under the table.
- **Header labels ≤ 2 lines at 1280 (S05-RW):** the benchmark columns read "so với VN-Index" / "so với E1VFVN30" with
  the unit "(điểm %)" moved to a `title` + the footer note ("Cột so với: chênh lệch tính bằng điểm %").

### 6.5 Add / edit side panel form (`scenario-panel`)
- ≥ 768 px: right-side drawer, width 440 px (max 100 vw), full height under nothing (covers the top bar), `--surface`,
  `--shadow-2`, left `--border`; backdrop `rgba(0,0,0,.32)` over the page; slides in 160 ms (none if reduced motion).
  < 768 px: full screen sheet.
- Header: title "Thêm kịch bản" / "Sửa kịch bản" `--fs-lg` + close ✕ `.btn-icon`; sticky.
- Body: one column, field gap `--sp-4`; label above control (`--fs-sm` 500), hint/error below (`--fs-xs`). Amount input
  right-aligned tabular with "₫" suffix inside the field. Style radios as two stacked option rows with 16 px radio. "Hôm nay"
  checkbox inline after the End label. Below-one-lot hint: `--warn` text with ⚠.
- Footer sticky at bottom, top `--border`: **Lưu** `.btn-primary` · **Huỷ** `.btn` (right-aligned, Lưu last on desktop,
  full-width stacked on mobile with Lưu on top). Delete confirm uses the same panel footer pattern with `.btn-danger`.

### 6.6 How-computed panel (F-051)
- Same drawer as §6.5 (≥ 768 px) or a full-screen sheet; title = the figure name ("Giá trị nếu bán").
- Formula block: `--surface-2` bg, radius `--r-sm`, padding `--sp-3`, `--font-mono` `--fs-sm`, wraps (no sideways scroll at 375).
- Inputs list as label/value rows like the card; "as of", `rules_version`, price basis as `--fs-xs` muted rows at the end.
- Approximate note: `--warn-bg` block with ⚠ and the full explanation text.

### 6.7 States
| State | Look |
|---|---|
| Empty (no scenarios) | One centred card (max 480 px) in the grid area: text `--fs-md`, example line `--fs-sm` muted, **+ Thêm kịch bản** `.btn-primary`. No illustration. |
| No bars yet | Same card; command in `--font-mono` on `--surface-2` with radius `--r-sm`; Add button disabled style. |
| Loading | 3 (≥ 1024) / 2 / 1 skeleton cards: same size as a card, blocks in `--surface-2`, 1.2 s opacity pulse (static if reduced motion); `aria-busy` on the grid. Header renders at once. |
| Error (API down) | `ApiErrorState`: centred block max 560 px, `--error-bg`, ✕ icon, message `--fs-md`, command in mono, **Thử lại** `.btn`. |
| Error (one card) | §6.3. |
| Stale | Warn chip (§4) in header; cards unchanged. |
| Partial data | Card note `--fs-xs` `--warn` "⚠ thiếu 3 phiên dữ liệu" + (i). |

## 7. Content and tone
- Vietnamese is the default UI; labels short, sentence case ("Thêm kịch bản", not "THÊM KỊCH BẢN"); no uppercase transforms
  (they break diacritics readability).
- Numbers vi-VN as in `scenario-dashboard.md`; currency "₫" after the number with a space (10.610.975 ₫).

## 8. Accessibility
- Contrast ≥ 4.5:1 for text, ≥ 3:1 for borders of inputs and the focus ring, light and dark (axe `color-contrast` 0 violations).
- Focus ring visible on every interactive element (§3.6). Up/down/ref always paired with ▲/▼/= and sign.
- Zoom 200 % at 1280 px: no content lost, no overlap.

## 9. Visual acceptance check (F-132 — the tester runs it for every UI story)
1. **Screenshots** (Playwright/Chromium headless, already used by the FE tester): viewports **375×812** and **1280×800**,
   each in `colorScheme: 'light'` and `'dark'` → 4 shots per screen. Screens: (a) /scenarios with ≥ 2 cards (one lump sum,
   one DCA, one with a P/L down); (b) empty state; (c) table view; (d) add form open with one validation error;
   (e) how-computed open; (f) crawl status running and error (mocked); (g) API error state. Files:
   `sprint-NN/screens/<screen>-<375|1280>-<light|dark>.png`, listed in `4-test.fe.md`.
   **From S05 (retro S04 R2):** also **768×1024 light** and **800×900 light** for screens (a) and (f) →
   `<screen>-<768|800>-light.png`.
2. **Checklist per shot**, compared against this file — each line pass/fail in `4-test.fe.md`:
   - no serif font anywhere; no default grey OS button; page bg/surface match §3.1 for the scheme;
   - columns: 1 at 375, 3 at 1280 (2 checked once at 800 px); no horizontal page scroll at 375
     (`document.documentElement.scrollWidth <= 375`);
   - P/L shows ▲/▼/= + sign + the §3.2 colour; approximate flag is the warn chip; benchmarks n/a is muted text;
   - figures right-aligned/tabular in the table; Name column sticky at 375;
   - top bar is one line at 375 (menu button, icon crawl button, VI | EN visible); disclaimer band visible on /scenarios;
   - top bar and page header do not wrap at 768 and 800 (one bar line; no label broken over 2 lines); 2 card columns at 800;
   - table header labels ≤ 2 lines at 1280; a DCA card shows at most one shift line;
   - focus ring visible on Tab to: Add, view toggle, a card (i), a form field (one extra shot at 1280 light with focus).
3. **Automated guards** (in vitest or a script, they fail the build): every `var(--name)` in `apps/web/src/**/*.{ts,tsx,css}`
   is defined in `tokens.css` (and inside the dark block for colour tokens); `getComputedStyle(body).fontFamily` does not
   start with a serif family; axe on /scenarios, form and panel → 0 `color-contrast` violations in both schemes.
4. The PM review opens the 1280 light/dark and 375 light shots of each screen; a mismatch with this file = NOT DONE, stage = FE.
