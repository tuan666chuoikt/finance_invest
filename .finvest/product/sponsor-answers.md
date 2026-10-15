# Sponsor answers (verbatim, append-only)

Owner: the Scrum Master. Append the sponsor's words exactly, with date/time and the question they answer.
Never paraphrase, never delete. Agents cite entries by date.

## 2026-10-14 — project kickoff
> (see product/brief.md, "Original request")

## 2026-10-14 21:57 — answers to A1–A4 (product/brief.md)
> nhớ thêm label với mỗi câu hỏi như A1 Bắt đầu với sàn nào?
> Bắt đầu với sàn nào? - tất cả sàn mà bạn có thể crawl data ve dc
> Có chấp nhận mở tài khoản chứng khoán để dùng API miễn phí không? chưa phải lúc
> Có tính margin (vay ký quỹ) không? không
> tạm thời thì không Có dùng LLM chạy trên máy không

Mapping: A1 = all crawlable exchanges · A2 = not now · A3 = no · A4 = not for now.
Rule from the sponsor: every question to the sponsor carries a label (A1, A2, …), kept across files and replies.

## 2026-10-15 18:15 — answers to A5–A12 (product/prd.md, Open questions)
> A5 approve
> A6 approve
> A7 tôi cào data để mô phỏng các kịch bản không phải để yêu dỗi hoặc giao dịch
> A8 tuỳ chọn tiếng anh, tiếng việt
> A9 các vấn đề về tin tức sẽ phát triển sau
> A10 duyệt
> A11 duyệt
> A12 Duyệt lưu ở /home/stein/Desktop/Learning/finance_invest và git ignore nó

Mapping (SM reading, PO to confirm in the PRD): A5 = as proposed · A6 = 0.15% as proposed · A7 = data is for
scenario simulation, not live trading/monitoring (no always-on guarantee needed) · A8 = UI switchable EN/VI ·
A9 = news deferred to a later release · A10, A11 = as proposed · A12 = keep all ticks, stored inside the repo
folder (e.g. finance_invest/data/), git-ignored.

## 2026-10-15 18:21 — PRD approval
> approve PRD

## 2026-10-15 18:36 — answer to A14 (backlog.md); question on A13
> Lãi xuát phi rủi ro là gì vậy
> 30 mặc định là 30 mã có volume lớn nhất

Mapping: A14 = default watchlist = top 30 symbols by volume (SM asked A15: shares vs value, window). A13 still open.

## 2026-10-15 18:46 — answer to A15
> A15-A

Mapping: default watchlist = top 30 by average traded value (shares x price), last 20 sessions, refreshed weekly.

## 2026-10-15 20:47 — answer to A13, backlog approval
> A13 5%, approve backlog

Mapping: risk-free default 5%/year, editable. Backlog approved.

## 2026-10-15 21:31 — answers to A16–A21, architecture approval
> approve tất cả

Mapping: A16-A (own adapters on public KBS/VCI/SSI endpoints), A17-A (no proprietary flows in v1), A18-A (reconstructed nominal prices, flagged), A19-A (5% x min(sale price, 10,000)), A20-A (E1VFVN30 benchmark), A21-A (cash dividends kept as cash by default). Architecture approved.
