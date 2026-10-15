# Vietnamese stock market rules (domain truth for every agent)

Owner: `fi-ai-architect`. **Status: draft written 2026-10-14 from general knowledge — every rule marked
[verify] must be checked against the exchange / SSC / broker source and dated before code relies on it.**
Rules change (e.g. the trading-system migration, settlement changes); code reads them from one rules
module whose values come from this file, with an `effective_from` date per rule.

## 1. Venues and instruments
- Exchanges: **HOSE** (HSX, Ho Chi Minh City), **HNX** (Hanoi), **UPCoM** (unlisted public companies, run by HNX).
- Instruments in scope: common stocks, ETFs; indices VN-Index, VN30, HNX-Index, HNX30, UPCoM-Index.
  Out of scope v1: covered warrants, derivatives (VN30 futures), bonds.
- Symbols: 3 letters for stocks (FPT, VNM, HPG); ETFs like E1VFVN30, FUEVFVND.

## 2. Sessions (local time Asia/Ho_Chi_Minh, UTC+7, no DST) [verify]
| Venue | Sessions |
|---|---|
| HOSE | ATO 09:00–09:15 · continuous 09:15–11:30 · break 11:30–13:00 · continuous 13:00–14:30 · ATC 14:30–14:45 · put-through to 15:00 |
| HNX | continuous 09:00–11:30 · 13:00–14:30 · ATC 14:30–14:45 · post-close (PLO) 14:45–15:00 |
| UPCoM | continuous 09:00–11:30 · 13:00–15:00 (no ATO/ATC) |
Trading days Mon–Fri except public holidays (Tết Nguyên Đán ~5–9 days, Hùng Kings, 30/4, 1/5, 2/9 and
announced bridge days). Keep a **trading calendar table**; never infer holidays from missing data.

## 3. Prices
- **Reference price** (giá tham chiếu): HOSE/HNX = previous session close; UPCoM = previous session's
  volume-weighted average price. Adjusted on ex-rights days (§6).
- **Price band** (biên độ): HOSE ±7%, HNX ±10%, UPCoM ±15% of reference. First trading day of a new
  listing: HOSE ±20%, HNX ±30%, UPCoM ±40%. [verify]
- **Ceiling (trần)** / **floor (sàn)** = reference ± band, rounded **inward** to the tick size.
- **Tick size** (bước giá) [verify]: HOSE stocks < 10,000 → 10 VND; 10,000–49,950 → 50 VND; ≥ 50,000 →
  100 VND. ETFs on HOSE 10 VND. HNX and UPCoM stocks 100 VND.
- Board colours: purple = ceiling, cyan/blue = floor, yellow = reference, green = above, red = below.
- **Units**: many data sources quote prices in **thousand VND** (93.5 = 93,500 VND); volumes in shares
  (some boards show units of 10 shares). Each source adapter must document and convert its units.

## 4. Orders and lots [verify]
- Board lot (lô chẵn) **100 shares** on HOSE/HNX/UPCoM. Odd lots (lô lẻ, 1–99) trade on a separate
  odd-lot board with its own rules; the simulator supports `lot_mode = board | odd_lot_allowed`.
- Max quantity per order on HOSE 500,000 shares (irrelevant for a personal simulator, keep as a guard).
- Order types: LO (limit), ATO, ATC, MP/MTL/MOK/MAK (HOSE/HNX variants). The simulator fills at a
  declared rule (close, next open, VWAP, or a limit price inside the day's range), never at a price
  outside that day's [low, high].

## 5. Costs, taxes, settlement [verify]
- **Brokerage fee**: broker-specific, typically 0.10%–0.35% of trade value per side (some brokers 0%).
  Default in the simulator: **0.15% buy and sell**, user-configurable.
- **Sell tax**: **0.1% of sell value** (personal income tax on securities transfer), withheld at sale.
- **Cash dividend tax**: 5% withheld on cash dividends to individuals.
- **Stock dividends / bonus shares**: 5% tax applied when those shares are later sold (on par value 10,000 VND basis). [verify]
- **Settlement T+2**: shares bought on T arrive and are sellable from T+2 (afternoon session); sale
  proceeds are available T+2 (cash advance possible at a fee). The simulator must not allow selling
  before shares arrive, nor re-using sale cash before settlement unless `cash_advance` is enabled.

## 6. Corporate actions (the main source of wrong returns)
- **Cash dividend**: on the ex-date (ngày GDKHQ) the reference price drops by the dividend per share;
  the cash is paid later on the payment date. Total-return series add it back.
- **Stock dividend / bonus shares** ratio a:b (holder of a shares gets b new): adjusted reference =
  P × a / (a + b). Shares arrive weeks later but count from the ex-date for valuation.
- **Rights issue** ratio a:b at price S: adjusted reference = (P × a + S × b) / (a + b); exercising costs cash.
- **Adjusted price series** (giá điều chỉnh) back-adjust history by these factors. Rule: *charts and
  indicators* may use adjusted prices; *the what-if simulator* replays nominal prices plus the actual
  corporate-action events (cash in, shares in), and the two must agree on total return.
- Keep a `corporate_actions` table: symbol, type, ex_date, record_date, pay_date, ratio/amount, source.

## 7. Market structure signals used in "why it moved"
- Foreign investors: net buy/sell value per stock and per market; foreign ownership limit (FOL/room).
- Proprietary trading (tự doanh) net flow, published after the session by some sources.
- Index weights (VN30 constituents), sector classification (ICB), ETF rebalancing dates (quarterly
  review of VN30/VNDiamond/FTSE/MSCI-tracking ETFs move flows).
- Earnings season (quarterly reports due ~20–45 days after quarter end), AGM season (Mar–Jun),
  ex-dividend dates, margin-call cascades (large down days with high volume), regulatory news.

## 8. Data granularity actually available for free [verify per source]
| Grain | History available | Note |
|---|---|---|
| Tick (each matched trade: time, price, volume, side) | **current/last session only** from public endpoints | We must crawl it **every trading day after close** to build history; no free back-fill |
| Order book top 3 bid/ask | live snapshots only | Store sampled snapshots (e.g. every 3–5 s) for the watchlist only |
| 1-minute bars | limited recent window (varies by source) | Crawl daily; back-fill as far as the source allows |
| Daily OHLCV | many years | Back-fill once, then daily |
| Corporate actions, financial statements, company profile | years | Daily/weekly refresh |
| News headlines | source RSS/web | Store headline, time, url, symbols tagged; respect ToS |
