# UX — Data-quality page (R1)

Stories: F-021 (PR-017, PR-132, PR-136), F-022 (PR-017), F-016 (reconciliation list), F-019 (manual
re-run). This page is the sponsor's G1/G2 check. Owner: `fi-pm`.

## Layout (top → bottom)
1. **Summary row** (cards): Daily coverage `99,7 %` (target ≥ 99,5 %) · Tick completeness `85,0 %`
   (17/20 sessions, reported not targeted) · Adjusted mismatches `3` · Anomalies `12` · Storage `4,2 GB`
   · Backup `⚠ No backup configured`.
2. **Feeds table**, one row per feed (Symbols, Daily OHLCV, Corporate actions, Ticks; later 1m, order book,
   flows): Last success (dd/MM/yyyy HH:mm) · Status (✓ OK / ⚠ Partial / ✕ Failed / ⏸ Source blocked) ·
   Sessions covered · Completeness % · Storage on disk · Action "Re-run date…".
3. **Tick sessions calendar**: month grid of trading days; each day = ✓ complete / ◐ partial (n skipped
   symbols) / ✕ missed with reason; holidays and weekends greyed with name, never counted as gaps (F-003).
   Click a day → manifest (symbols fetched, rows, checksum, skipped symbols with reason).
4. **Gaps list** (G1 "0 silent gaps"): date · feed · reason ("machine off", "source no longer serves",
   "source blocked", "partial: rate limit") · action.
5. **Adjusted-series mismatches** (> 0,1 %): symbol · date · ours · source · diff % (e.g. FPT · 49.000 ·
   48.900 · 0,204 %).
6. **Anomalies**: symbol · date · rule (outside band / zero volume on trading day / duplicate tick) · value.

## Re-run dialog (F-019)
- Date picker limited to trading days; warns "Ticks for dates before the last session are usually no longer
  served" `[assumed]`. Confirm → job queued; row shows "Running…" then result.

## States
| State | Shown |
|---|---|
| Empty (never crawled) | "No crawl yet" + the one command (F-030); summary cards show "—" |
| Loading | Card and table skeletons |
| Error | "Cannot read data store" + path `finance_invest/data/` + retry |
| Stale data | Summary banner "⚠ Last successful crawl 13/10/2026; 2 trading sessions since" |
| Market closed / holiday | Today's cell labelled "Holiday" or "Market open — crawl at 15:30" |
| Partial | Feed status "⚠ Partial" with the count of skipped symbols; never shown as OK |
| Source blocked | Feed row "⏸ Source blocked since 14:02 — stopped to respect limits (PR-135)" |

## Formats and accessibility
- vi-VN numbers (99,7 %, 4,2 GB, 49.000). Status uses icon + text + colour, never colour alone.
- Tables sortable by keyboard (Enter on header); calendar cells are buttons with an aria-label
  "14/10/2026, missed: machine off".

## Mobile width
- Summary cards wrap 2 per row; tables become stacked cards; calendar shows one week per row.

## Copy
- No disclaimer banner (data page, not analysis). Show "Data source: <adapter name>" per feed.
