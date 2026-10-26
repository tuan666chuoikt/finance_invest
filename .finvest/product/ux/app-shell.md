# UX — App shell, language switch, disclaimer (R1)

Stories: F-031 (PR-137), F-032 (PR-130), F-034 (PR-020, A23 — crawl button). Owner: `fi-pm`.

## Layout
- Top bar (left → right): product name "Finvest" · nav (R1: **Data quality**, **Market rules**; later
  releases add What-if, Board, Scenarios, Why it moved) · data freshness chip · **crawl button** (F-034) · language switch `VI | EN`.
- Freshness chip: "Dữ liệu đến 15/10/2026 15:42" (VI) / "Data as of 15/10/2026 15:42" (EN), same
  dd/MM/yyyy HH:mm format in both languages, Asia/Ho_Chi_Minh time. Click → Data quality page.
- Disclaimer banner under the top bar on **analysis routes** (none in R1 except as a component tested by
  F-032; rendered from R2): both lines always, regardless of UI language:
  "Mô phỏng để học, không phải lời khuyên đầu tư · Educational simulation, not investment advice".
  Not dismissible.

## Language switch
- Default VI on first start `[assumed]`; choice saved in local storage; applied without a page reload.
- Segmented control with `aria-pressed`; the active language is bold + underlined (not colour only).
- Numbers are always vi-VN (1.234.567 ₫, dates dd/MM/yyyy) in both languages, so a figure never changes
  meaning when switching. Prices on boards in thousand VND as exchanges show (93,5), elsewhere full VND.
- Glossary terms keep both languages (PR-111) from R2.

## States
| State | Shown |
|---|---|
| Loading | Top bar renders immediately; page body skeleton |
| Error (API down) | Full-width message "Cannot reach the local server. Is `docker compose` running?" + retry button |
| Stale data | Freshness chip turns amber with "⚠" and "stale: last success 14/10/2026" when the last crawl is older than the last trading session |
| Market closed / holiday | Chip text "Market closed (holiday: Quốc khánh)" from F-003/F-005 |
| Empty (first run) | Body: "Chưa có dữ liệu. Bấm **Cào dữ liệu** để lấy lần đầu" / "No data yet. Press **Crawl data**" (F-034); the command (F-030) as a secondary line |

## Crawl button (F-034, A23; step 3 and "chờ lượt sau" added S05 for F-014/F-013)
Manual only: nothing crawls unless this button (or the CLI) is used. Placement: top bar, left of the language switch.
One job at a time, enforced by the server (`POST /jobs` → 409), not only by disabling the button.

| State | Button | Status line (under the top bar, `role="status"`, `aria-live="polite"`) |
|---|---|---|
| Idle | "⟳ Cào dữ liệu" / "⟳ Crawl data"; tooltip shows the last run, e.g. "Lần cuối: 26/10/2026 16:14 · xong" | none |
| Running | disabled, spinner + "Đang cào…" / "Crawling…", `aria-busy="true"` | step + progress: "Bước 1/3 — lệnh khớp 26/10: 12/30 mã" then "Bước 2/3 — giá ngày: 3/6 phiên" then (S05, F-014) "Bước 3/3 — sự kiện quyền: 18/40 mã"; elapsed time. Survives reload (state read from the job). |
| Refused (already running) | stays running | "Đang có một lượt cào chạy (bắt đầu 16:10) — chờ xong" / "A crawl is already running (started 16:10)"; no second job |
| Done | back to idle | "✓ Xong 16:14 · 30 mã, 812.344 lệnh khớp · +6 phiên giá ngày · +3 sự kiện quyền (1 thay đổi) · 2 mã bỏ qua · 3 phút 41 giây"; names left for a later press (block budget) add "· 12 mã chờ lượt sau" / "· 12 names left for the next press" (S05, F-013/F-014) ("Chi tiết" → Data quality page / manifest); no session today → "✓ Xong 09:02 · Hôm nay không có phiên — +1 phiên giá ngày · 18 giây"; session open → adds "(một phần, đến 10:30)". Dismissible; the freshness chip refreshes. |
| Error | back to idle (press again to retry) | "✕ Lỗi: không có quyền ghi data/raw/ticks/2026-10-26 (PermissionError)" — always the cause + the path or source (HTTP code, "nguồn KBS chặn", "không kết nối được máy chủ"); partial results already written are stated ("đã lưu 12/30 mã"). Not auto-dismissed. |

Non-colour cues: ⟳ / spinner / ✓ / ✕ icons plus text. Keyboard: in the Tab order after the freshness chip; Enter/Space
presses it. Mobile ≥ 360 px: icon-only button with the same accessible name; status line wraps.

## Keyboard and accessibility
- Tab order: nav → freshness chip → crawl button → language switch → page. `Alt+L` toggles language.
- Visible focus ring; contrast ≥ 4.5:1 in both light and dark.

## Mobile width (≥ 360 px)
- Nav collapses into a menu button; language switch stays visible; banner wraps to two lines.
