# UX — App shell, language switch, disclaimer (R1)

Stories: F-031 (PR-137), F-032 (PR-130). Owner: `fi-pm`.

## Layout
- Top bar (left → right): product name "Finvest" · nav (R1: **Data quality**, **Market rules**; later
  releases add What-if, Board, Scenarios, Why it moved) · data freshness chip · language switch `VI | EN`.
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
| Empty (first run) | Body: "No data yet. Run the first crawl:" + the one command (F-030) |

## Keyboard and accessibility
- Tab order: nav → freshness chip → language switch → page. `Alt+L` toggles language.
- Visible focus ring; contrast ≥ 4.5:1 in both light and dark.

## Mobile width (≥ 360 px)
- Nav collapses into a menu button; language switch stays visible; banner wraps to two lines.
