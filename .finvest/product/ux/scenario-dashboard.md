# UX — Scenario dashboard (S03 slice)

Stories: F-055 (form, save/edit/delete), F-056 (dashboard), F-048 (benchmarks), F-051 (how computed), F-032
(banner), F-031 (shell). Engine: F-040, F-041, F-057. Owner: `fi-pm`. Shell rules (language, number format,
focus, top bar) come from `ux/app-shell.md` and are not repeated here.

## Purpose
"Nếu tôi đã bỏ X đồng vào mã Y từ ngày A, đến nay / đến ngày B tôi có bao nhiêu?" — for many scenarios at once,
side by side, each honest about how exact it is.

## Layout (desktop ≥ 1024 px)
1. Top bar (shell) · disclaimer banner (both lines, not dismissible).
2. Page header: title **Kịch bản đầu tư / Investment scenarios** · button **+ Thêm kịch bản / Add scenario** ·
   view toggle **Thẻ / Cards | Bảng / Table** (segmented, `aria-pressed`) · "Dữ liệu đến 23/10/2026 · nguồn VCI" /
   "Data as of 23/10/2026 · source VCI".
3. Grid of cards, 3 per row (2 at 768–1023 px, 1 below), order = creation, newest first.

## Card (one scenario)
```
┌───────────────────────────────────────────────┐
│ FPT · Mua một lần / Lump sum           [⋯]    │  ⋯ = Sửa/Edit, Xoá/Delete
│ 12/10/2025 → hôm nay (23/10/2026)             │
│ ⚠ ≈ Gần đúng — giá điều chỉnh, chưa tính cổ tức│  approximate flag (icon + text)
│ Đã đầu tư      10.000.000 ₫                   │
│ Giá trị nếu bán 10.610.975 ₫          (i)     │  (i) opens "how computed"
│ Lãi/Lỗ   ▲ +610.975 ₫   ▲ +6,11 %      (i)    │
│ [mini equity curve 100 % wide × 48 px]        │
│ VN-Index      ▲ +5,00 %   (+1,11 điểm %)      │
│ E1VFVN30      ▲ +4,20 %   (+1,91 điểm %)      │
└───────────────────────────────────────────────┘
```
- P/L cue: ▲ / ▼ / = plus sign plus colour (green up, red down, amber/yellow zero — board convention VN§3);
  colour is never the only cue.
- DCA card line 1: "FPT · Mỗi tháng 2.000.000 ₫ / Monthly 2,000,000 ₫ (ngày 15)"; "Đã đầu tư" = sum of
  contributions to date; extra line "Tiền mặt còn / Cash left 635.975 ₫" (always shown for both styles).
- Shift notices (from F-040/F-041/F-057) show under the dates in small text: "Ngày mua dời sang 19/10/2025".
- Mini curve: daily market value (cash + shares × close) from N to M; a dashed horizontal line at the amount
  invested (DCA: a step line of cumulative contributions). Hover/focus shows date + value. No axes.
  Accessible name: "Đường giá trị FPT từ 12/10/2025 đến 23/10/2026, cao nhất …, thấp nhất …".
- Benchmarks: VN-Index labelled "(không đầu tư được / non-investable)" in its tooltip; "pp" difference vs the
  scenario. Missing: "E1VFVN30 — không có dữ liệu trước 06/10/2014 / n/a — data from 06/10/2014" (date illustrative).

## Table view (same data)
Columns: Name · Symbol · Style · Start · End · Invested · Value · P/L ₫ · P/L % · vs VN-Index (pp) · vs E1VFVN30
(pp) · Flag (⚠). Sortable by any numeric column (default P/L % desc), keyboard-sortable via header buttons.
Footer note: "Xếp hạng theo quá khứ không dự báo tương lai / Past ranking does not predict the future."

## Form (add / edit) — side panel on desktop, full screen on mobile
| Field | Control | Default | Validation (message EN/VI under the field) |
|---|---|---|---|
| Tên / Name | text, optional | "FPT · 10.000.000 ₫ · 12/10/2025" | ≤ 60 chars |
| Mã / Symbol | combobox from symbol master (type-ahead, shows exchange) | — | must exist |
| Kiểu / Style | radio: Mua một lần / Lump sum · Mua định kỳ hàng tháng / Monthly DCA | Lump sum | — |
| Số tiền / Amount (or Mỗi tháng / Monthly) | integer VND, grouped as typed (10.000.000) | 10.000.000 | > 0, integer, ≤ 100.000.000.000 |
| Từ ngày / Start | date dd/mm/yyyy | one year before latest bar | ≥ first stored bar of the symbol; ≤ latest bar |
| Đến ngày / End | date or checkbox "Hôm nay / Today" (checked) | Today | ≥ start |
Hint under Amount when below one lot at the start close: "Ít hơn 1 lô (≈ 9.364.025 ₫) — sẽ không mua được cổ phiếu
nào" (lump sum) or "sẽ tích luỹ đến khi đủ 1 lô" (DCA). Saving is still allowed. Buttons: **Lưu / Save**, **Huỷ /
Cancel**. Delete asks "Xoá kịch bản FPT …? / Delete scenario …?" with **Xoá / Delete** + **Huỷ**; no undo.

## How computed panel (F-051), opened from any (i)
Formula, inputs with values, data as of, `rules_version`, price basis. Example for "Giá trị nếu bán":
`cash 635.975 + 100 cp × 100.000 − phí bán 0,15 % 15.000 − thuế bán 0,1 % 10.000 = 10.610.975 ₫`.
When approximate: "Giá dùng là giá đã điều chỉnh của nguồn (VCI). Số cổ phiếu mua được tính theo giá điều chỉnh nên
có thể khác thực tế ngày đó; cổ tức tiền mặt chưa được tính. Cờ này mất khi có giá danh nghĩa và sự kiện doanh nghiệp."
(and the EN text). P/L % formula for DCA: P/L ÷ total contributed (not an annualised or money-weighted return).

## States
| State | Shown |
|---|---|
| Empty (no scenarios) | Illustration-free card: "Chưa có kịch bản nào. / No scenarios yet." + **Thêm kịch bản** + one example line "VD: FPT, 10.000.000 ₫, từ 12/10/2025 đến hôm nay" |
| No bars yet (back-fill not run) | "Chưa có dữ liệu giá ngày. Chạy back-fill: `make backfill`" (exact command from F-012); Add disabled |
| Loading | Card skeletons in the grid; header renders immediately |
| Error (API down) | Shell error state ("Cannot reach the local server…") + retry |
| Error (one scenario fails) | That card only: "Không tính được: <reason>" + Edit; others render |
| Stale data | Header "as of" chip amber + ⚠ "dữ liệu cũ: đến 16/10/2026" when the latest bar is older than the last trading session (F-003); cards still show values, labelled with that date |
| Market closed / holiday | Chip text "Thị trường nghỉ (Quốc khánh)"; "today" = last trading session |
| Partial data | Symbol with gaps inside N..M: card note "thiếu 3 phiên dữ liệu / 3 sessions missing" (i) lists dates; benchmark missing → "n/a" cell, never 0 |
| Delisted symbol | End value at the last stored close with note "huỷ niêm yết 05/03/2024 / delisted" |
| Approximate | Flag on every card and every table row while `approximate = true` (all of S03) |

## Number and date formats
vi-VN always: 10.610.975 ₫, +6,11 %, +1,11 điểm % (EN label "pp"), dates dd/mm/yyyy, Asia/Ho_Chi_Minh. Prices in the
how-computed panel in full VND (93.500), not thousand VND.

## Keyboard
Tab: Add → view toggle → cards in order; inside a card: (i) buttons → ⋯ menu (Enter opens, arrows move, Esc closes).
`N` opens the form when focus is not in a field. Form: Enter saves, Esc cancels and returns focus to the trigger.
Focus ring visible; contrast ≥ 4.5:1 light and dark.

## Mobile (≥ 360 px)
One card per row; table view scrolls horizontally inside its own container with Name column sticky; form full screen;
banner wraps to two lines.

## Out of scope (S03)
Several symbols per scenario (F-089), fill rules other than close-of-N (F-042), dividend options (F-043), ledger and
CSV (F-049), risk metrics (F-090), IRR, alerts.
