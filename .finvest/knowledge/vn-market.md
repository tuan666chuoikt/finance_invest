# Vietnamese stock market rules (domain truth for every agent)

Owner: `fi-ai-architect`. **Status: v1 verified 2026-10-15** (draft 2026-10-14 from general knowledge; every rule now
carries a tag). Tags: **[verified src, date]** = read in a primary or official-derived source on that date;
**[practice]** = consistent market practice, no single legal text; **[verify]** = still unconfirmed, code must flag it
(`verified=false` in `packages/market_rules`, shown on the rules page, C7). Rules change (KRX system 05/05/2025,
settlement 2022, tax law 2026); code reads them from one rules module whose values come from this file, with an
`effective_from` date per rule.

Sources used (S#): S1 = "Quy định giao dịch chứng khoán tại HSX" (broker summary of the VNX/HOSE rules under the
new KRX system, PDF dated 15/08/2025, cts.vn → vbse.vn); S2 = "Quy định giao dịch chứng khoán tại HNX" (same series,
HNX + UPCoM); S3 = VSD Decision 109/QĐ-VSD (clearing & settlement regulation, effective 29/08/2022, via lsvn.vn,
thitruongtaichinhtiente.vn); S4 = Law 109/2025/QH15 on PIT + Decree 253/2026/NĐ-CP (effective 01/07/2026) via
thuvienphapluat.vn, PwC, Forvis Mazars summaries; S5 = Circular 102/2021/TT-BTC (securities service price caps, effective
01/01/2022) via thuvienphapluat.vn; S6 = DSC broker comparison 2026 + company ex-right notices (stockbiz.vn).
Primary texts on hsx.vn / hnx.vn / vsd.vn were not reachable from this machine (404/empty); S1–S2 are broker reprints of
the exchange rules, so §2–§4 count as **verified (secondary)**; re-check against hsx.vn/hnx.vn at R1.

## 1. Venues and instruments
- Exchanges: **HOSE** (HSX, Ho Chi Minh City), **HNX** (Hanoi), **UPCoM** (unlisted public companies, run by HNX).
- Instruments in scope: common stocks, ETFs; indices VN-Index, VN30, HNX-Index, HNX30, UPCoM-Index.
  Out of scope v1: covered warrants, derivatives (VN30 futures), bonds.
- Symbols: 3 letters for stocks (FPT, VNM, HPG); ETFs like E1VFVN30, FUEVFVND.

## 2. Sessions (local time Asia/Ho_Chi_Minh, UTC+7, no DST) [verified S1, S2, 2026-10-15]
| Venue | Sessions |
|---|---|
| HOSE | ATO 09:00–09:15 (ATO, LO) · continuous 09:15–11:30 (LO, MTL) · break 11:30–13:00 · continuous 13:00–14:30 · ATC 14:30–14:45 (ATC, LO) · put-through only 14:45–15:00 |
| HNX | continuous 09:00–11:30 (LO, MTL, MOK, MAK) · break · continuous 13:00–14:30 · ATC 14:30–14:45 · **PLO** 14:45–15:00 (14:45–14:55 periodic, 14:55–15:00 continuous at the closing price; no cancel/amend) |
| UPCoM | continuous 09:00–11:30 · 13:00–15:00 · put-through 09:00–15:00 · **no ATO/ATC** (S1/S2 Aug-2025; one broker sheet of Jul-2025 shows 14:30 — [verify] end time on hnx.vn at R1) |
- Odd-lot matching on HOSE: 09:15–11:30 and 13:00–14:30 only [verified S1].
- No order amend/cancel during periodic (ATO/ATC) sessions [verified S1].
- Trading days Mon–Fri except public holidays (Tết Nguyên Đán, Hùng Kings, 30/4, 1/5, 2/9, 1/1 and announced bridge
  days). Saturday make-up working days are **not** exchange trading days (VSDC did no settlement on Sat 10/01/2026;
  treat Sat 22/08/2026 as closed unless HOSE announces otherwise) [practice; verify each year on hsx.vn].
  Keep a **trading calendar table** (data.md §1.3); never infer holidays from missing data.

## 3. Prices
- **Reference price** (giá tham chiếu) [verified S1, S2]: HOSE/HNX = closing price of the latest trading day (= last
  matched price of that day). **UPCoM = volume-weighted average of board-lot continuous-matching prices of the latest
  day that had continuous matching.** New listings: proposed by the issuer/adviser for day 1. Adjusted on ex-rights
  days (§6); **not** adjusted for convertible-bond issues or share issues priced above the pre-ex average.
- **Price band** (biên độ) [verified S1, S2]: HOSE ±7 %, HNX ±10 %, UPCoM ±15 % of reference. First trading day of a
  new listing / first day back after ≥ 25 sessions suspended: HOSE ±20 %, HNX ±30 %, UPCoM ±40 %. If reference ±
  band rounds back to the reference, ceiling = ref + 1 tick, floor = ref − 1 tick (UPCoM ref 100 đ: floor = ref).
- **Ceiling (trần)** / **floor (sàn)** = reference × (1 ± band), rounded to the tick: ceiling rounded **down**, floor
  rounded **up** (inward) [practice; S1 gives the formula but not the rounding direction — verify against a live
  board in R1 (F-00x golden row)].
- **Tick size** (bước giá, matching sessions) [verified S1, S2]: HOSE stocks < 10,000 → 10 đ; 10,000–49,950 → 50 đ;
  ≥ 50,000 → 100 đ. **ETFs and covered warrants on HOSE: 10 đ at all prices.** HNX stocks 100 đ; **HNX-listed ETFs
  1 đ**; UPCoM stocks and ETFs 100 đ. Put-through: 1 đ (HOSE, HNX), 100 đ (UPCoM).
- Board colours: purple = ceiling, cyan/blue = floor, yellow = reference, green = above, red = below [practice].
- **Units**: many data sources quote prices in **thousand VND** (93.5 = 93,500 VND); volumes in shares
  (some boards show units of 10 shares). Each source adapter must document and convert its units (data.md §1.2:
  KBS/VCI VND, SSI history thousand VND).

## 4. Orders and lots [verified S1, S2, 2026-10-15]
- Board lot (lô chẵn) **100 shares / fund units** on HOSE, HNX and UPCoM. Odd lots (lô lẻ, 1–99) trade by
  continuous matching or put-through (not on a new listing's first day until a reference is set); the simulator
  supports `lot_mode = board | odd_lot_allowed` (PR-038, default `board`).
- Max quantity per board-lot order: **500,000** on HOSE (S1); HNX/UPCoM not stated in S2 [verify] (guard only).
- Put-through minimum: 20,000 units HOSE; 5,000 HNX [verified S1, S2] (not used by the simulator).
- Order types: HOSE LO, ATO, ATC, MTL; HNX LO, ATC, MTL, MOK, MAK, PLO. The simulator fills at a **declared
  rule** (close, next open, VWAP, or a limit price inside the day's range), never at a price outside that day's
  [low, high].

## 5. Costs, taxes, settlement
- **Brokerage fee**: capped by law at **0.45 %** of trade value per side (S5, since 01/01/2022) [verified];
  brokers publish 0.03 %–0.30 % in 2026, zero-fee promotions exist (S6) [secondary, changes often]. Default in the
  simulator: **0.15 % buy and sell**, user-configurable (sponsor A6). Fee rounded half-up to 1 VND (ADR-S-005).
- **Sell tax**: **0.1 % of sell value** (PIT on securities transfer, per transaction, profit or loss), withheld at
  sale [verified S4: Law 109/2025/QH15 keeps the rule; Decree 253/2026 from 01/07/2026].
- **Cash dividend tax**: **5 %** withheld on cash dividends to individuals (capital-investment income, per payment)
  [verified S4, Art. 52 Decree 253/2026].
- **Stock dividends / bonus shares**: no tax on receipt; 5 % PIT falls due **when those shares are sold** (S4 keeps
  the principle; the 2025 proposal to tax on receipt was withdrawn) [verified]. Tax base: par value 10,000 đ per
  share when the sale price ≥ par, else the sale price; the broker withholds together with the 0.1 % [practice per
  Decree 126/2020 Art. 7 — **[verify]** that Decree 253/2026 / Circular 87/2026 keep this base]. Simulator default:
  apply 5 % × 10,000 đ × bonus shares sold (sponsor question A19).
- **Settlement T+2** [verified S3]: securities and cash reach the investor's account **before 13:00 on T+2**; shares
  bought on T are sellable from the **afternoon session of T+2**; sale proceeds usable from T+2 (cash advance earlier
  at a fee). No change found as of 2026-10-15 (CCP/T+1 under study for 2027). The simulator must not allow selling
  before shares arrive, nor re-using sale cash before settlement unless `cash_advance` is enabled.
- Depository fee 0.27 đ/share/month (VSDC) [secondary S6] — ignored in v1 (≪ 1 VND/day on a 100-share lot; stated
  in "how computed").

## 6. Corporate actions (the main source of wrong returns)
- **Cash dividend**: on the ex-date (ngày GDKHQ) the reference price drops by the dividend per share [verified S1];
  the cash is paid later on the payment date. Total-return series add it back.
- **Stock dividend / bonus shares** ratio a:b (holder of a shares gets b new): adjusted reference = P × a / (a + b)
  [verified S1 principle "điều chỉnh theo giá trị các quyền"; formula is the exchange practice]. Shares arrive weeks
  later but count from the ex-date for valuation. **Fractional shares: rounded down to a whole share; the fraction is
  cancelled (most issuers) or paid in cash per the issuer's notice** [practice S6: PVS, NTP, DTP notices 2025–26];
  simulator default `round_down_cancel`, overridable per event.
- **Rights issue** ratio a:b at price S: adjusted reference = (P × a + S × b) / (a + b); exercising costs cash;
  no adjustment when S ≥ pre-ex average price [verified S1].
- **Adjusted price series** (giá điều chỉnh) back-adjust history by these factors. Rule: *charts and
  indicators* may use adjusted prices; *the what-if simulator* replays nominal prices plus the actual
  corporate-action events (cash in, shares in), and the two must agree on total return (F-046, ADR-A-001).
- Keep a `corporate_actions` table: symbol, type, ex_date, record_date, pay_date, ratio/amount, source (data.md §3).

## 7. Market structure signals used in "why it moved"
- Foreign investors: net buy/sell value per stock and per market; foreign ownership limit (FOL/room) — free from
  crawl start (data.md §1.3).
- Proprietary trading (tự doanh) net flow — **no free source found** (A17); the design treats it as optional evidence.
- Index weights (VN30 constituents), sector classification (ICB level 2 from VCI), ETF rebalancing dates (quarterly
  review of VN30/VNDiamond/FTSE/MSCI-tracking ETFs move flows) — manual calendar.
- Earnings season (quarterly reports due ~20–45 days after quarter end), AGM season (Mar–Jun),
  ex-dividend dates, margin-call cascades (large down days with high volume), regulatory news.

## 8. Data granularity actually available for free
Superseded by `architecture/data.md` §1.3 (probed 2026-10-15): ticks current session only; 1m ~3 years (VCI);
daily adjusted since 2006; nominal daily observed from crawl start, reconstructed before (A18); foreign flow from
crawl start; proprietary flow none; corporate actions ≥ 10 years.

## Verification ledger (2026-10-15)
| Rule | Status |
|---|---|
| §2 HOSE sessions | verified S1 |
| §2 HNX sessions incl. PLO | verified S2 |
| §2 UPCoM sessions | verified S2; end time 15:00 vs 14:30 conflict between broker sheets → [verify] |
| §2 Saturday make-up days closed | practice → [verify] per year |
| §3 reference price HOSE/HNX/UPCoM | verified S1, S2 (**UPCoM VWAP confirmed**) |
| §3 bands normal + first day | verified S1, S2 |
| §3 ceiling/floor rounding direction | [verify] (formula verified, direction not stated) |
| §3 tick sizes | verified S1, S2 — **changed: HNX ETF tick = 1 đ** (was 100) |
| §4 lot 100, odd lot 1–99, HOSE max 500,000 | verified S1, S2; HNX/UPCoM max [verify] |
| §4 order types | verified S1, S2 (MTL/MOK/MAK/PLO added) |
| §5 fee cap 0.45 %, broker range | verified S5; range secondary S6 |
| §5 sell tax 0.1 % | verified S4 |
| §5 cash dividend tax 5 % | verified S4 |
| §5 stock-dividend tax at sale | timing verified S4; **base (par value) [verify]** |
| §5 T+2, before 13:00, sell afternoon T+2 | verified S3 |
| §6 fractional bonus shares round down | practice S6 (issuer-specific) |
| §6 CA formulas | principle verified S1; formulas practice |
Totals: 13 verified (incl. secondary), 2 practice, 5 still [verify] (UPCoM end time, Saturday make-up, rounding
direction, HNX/UPCoM max order, stock-dividend tax base). One value changed (HNX ETF tick 100 → 1 đ); one addition
(UPCoM no ATC confirmed; PLO phases).
