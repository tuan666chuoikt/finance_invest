# Sponsor brief — Finvest

Owner: the sponsor (the user). Date: 2026-10-14. The original words (Vietnamese) are quoted; the English
below is the Scrum Master's faithful restatement for the agents. Only the sponsor changes this file.

## Original request
> "có khả thi không khi tôi muốn build 1 web có bảng điện tử, cào data chứng khoán để giả lập 'nếu tôi
> đầu tư X đồng vào ngày N cổ phiếu E thì có lời như nào'
> - data crawl chính xác ở đơn vị thời gian thấp nhất có thể
> mục tiêu là tôi muốn trở thành 1 nhà đầu tư chuyên nghiệp với kiến thức đầy đủ
> có thể thử nghiệm nhiều kịch bản đầu tư
> - có cách phân tích chuyên sâu như trong 7 ngày qua thì đầu tư kịch bản nào là tốt nhất, tại sao nó tăng giá"

## What the sponsor wants
1. **Price board** (bảng điện tử) for the Vietnamese market, as close to live as free data allows.
2. **Crawler** that stores market data at the **finest time grain available** (tick where possible),
   accurately, with history growing every trading day.
3. **What-if simulator**: "if I had invested X VND in stock E on day N, what would it be worth now /
   on day M?", with realistic fees, taxes, lots, settlement and dividends.
4. **Multiple scenarios**: compare strategies (lump sum, DCA, rules) on the same stock/period.
5. **Deep analysis**: e.g. over the last 7 days, which scenario did best and **why the price rose**
   (evidence: market, sector, flows, news, events).
6. **Learning goal**: the sponsor wants to become a professional investor with complete knowledge; the
   app should teach, not just compute.

## Constraints known now
- Personal use, one user, runs on the sponsor's Linux machine (Ubuntu, 6.8 kernel).
- **No budget for paid APIs or data**; free sources only. Claude Code subscription is used for building,
  not inside the app.
- Not an order-placing tool; no broker credentials stored; analysis is educational, not advice.
- Built by the agent team defined in `CLAUDE.md`, with the token-saving rules in `docs/02-tiet-kiem-token.md`.

## Sponsor questions (label A#; answers verbatim in sponsor-answers.md 2026-10-14 21:57)
- **A1** Which exchanges first? → **all exchanges we can crawl** (HOSE, HNX, UPCoM).
- **A2** Open a broker account to use an official free data API? → **not now**: public free endpoints only.
- **A3** Margin (vay ký quỹ) in the simulator? → **no**.
- **A4** Local LLM for news summaries? → **not for now**: rules and statistics only.
- Still open for the PO to propose: how many symbols on the live board (watchlist size vs all).
