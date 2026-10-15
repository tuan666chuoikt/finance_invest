# 00 — Đánh giá tính khả thi

**Kết luận: khả thi**, chạy được trên một máy cá nhân với chi phí dữ liệu 0 đồng. Có ba giới hạn
bạn cần biết ngay từ đầu, vì chúng ảnh hưởng thẳng tới việc thiết kế:

1. **Dữ liệu tick (từng lệnh khớp) chỉ lấy miễn phí được cho phiên hiện tại.** Lịch sử tick chỉ có
   từ ngày bạn bắt đầu tự cào. Cào càng sớm thì kho dữ liệu càng dày. Việc cào tick là **cố gắng tối đa**
   (A7): chỉ chạy khi máy bật, phiên bị lỡ được ghi rõ là lỗ hổng; mô phỏng dựa trên nến ngày và nến 1 phút.
2. **Câu hỏi "7 ngày qua kịch bản nào tốt nhất" rất dễ thành nhìn lại quá khứ rồi chọn cái đẹp nhất.**
   App phải luôn kiểm tra kịch bản đó trên giai đoạn kế tiếp (out-of-sample), nếu không nó dạy bạn
   bài học sai.
3. **"Tại sao nó tăng" chỉ đưa ra được bằng chứng, không đưa ra được sự chắc chắn.** App sẽ liệt kê
   các yếu tố đi kèm, ví dụ thị trường chung, ngành, dòng tiền khối ngoại hay sự kiện doanh nghiệp
   (tin tức để giai đoạn sau, R6, A9), và đo mức đóng góp của từng yếu tố.

## 1. Từng yêu cầu: làm được gì

| Yêu cầu | Khả thi? | Ghi chú |
|---|---|---|
| Bảng điện tử | ✅ gần realtime | Nguồn miễn phí cho phép hỏi lại vài giây một lần cho danh sách theo dõi (khoảng 20–100 mã). Muốn đủ khoảng 1.600 mã realtime thì cần kênh streaming chính thức. Kênh này thường miễn phí khi có tài khoản ở công ty chứng khoán (SSI FastConnect, DNSE); dùng hay không là quyết định của bạn |
| Cào data ở đơn vị nhỏ nhất | ✅ có điều kiện | Tick: cào mỗi ngày sau 15:00 khi máy bật (cố gắng tối đa, phiên lỡ được ghi lại). Nến 1 phút: lấy ngược về được một khoảng ngắn tuỳ nguồn. Nến ngày: lấy được nhiều năm |
| "Đầu tư X đồng ngày N vào mã E" | ✅ chắc chắn | Phải tính đúng lô 100 cổ, phí môi giới, thuế bán 0,1%, T+2, cổ tức tiền mặt, cổ tức cổ phiếu và quyền mua. Đây là chỗ hay sai nhất |
| Thử nhiều kịch bản | ✅ | Mua một lần, DCA, MA cross, breakout, cắt lỗ/chốt lời, so với VN-Index |
| "7 ngày qua kịch bản nào tốt nhất" | ✅ có cảnh báo | Xếp hạng kèm kiểm tra walk-forward và độ ổn định của thứ hạng |
| "Tại sao tăng giá" | ⚠️ ở mức bằng chứng | Tách phần đến từ thị trường, ngành và riêng mã; kèm khối lượng, khối ngoại, tự doanh, sự kiện (tin tức: R6) |
| Trở thành nhà đầu tư chuyên nghiệp | ✅ nếu app dạy đúng | Xem lộ trình học ở [04-lo-trinh-hoc.md](04-lo-trinh-hoc.md) |

## 2. Nguồn dữ liệu miễn phí (cần architect xác minh lại khi thiết kế)

- **Thư viện `vnstock`** (Python, mã nguồn mở): bọc các endpoint công khai của một số công ty chứng
  khoán. Có nến ngày nhiều năm, nến phút trong khoảng gần đây, khớp lệnh trong ngày, bảng giá, báo cáo
  tài chính, sự kiện và tin tức. Cần đọc giấy phép (dùng cá nhân) và giới hạn tốc độ.
- **API chính thức miễn phí khi có tài khoản**: SSI FastConnect Data, DNSE. Ổn định hơn endpoint công
  khai và có streaming. Tạm thời chưa dùng (A2).
- **Tin tức** (để giai đoạn sau, R6, A9): RSS hoặc trang của các báo tài chính. Chỉ lưu tiêu đề, thời gian, link và mã liên quan,
  và tôn trọng điều khoản của trang.
- **Rủi ro**: endpoint không chính thức có thể đổi định dạng hoặc chặn bất cứ lúc nào. Vì vậy kiến
  trúc đặt mọi nguồn sau một cổng `MarketDataSource` để thay nguồn mà không phải sửa phần lõi.

## 3. Ước lượng dung lượng

- Tick: một ngày toàn thị trường khoảng vài trăm nghìn đến vài triệu bản ghi. Sau khi nén
  (TimescaleDB/Parquet) chỉ khoảng vài chục MB mỗi ngày, nên một năm vẫn vừa ổ cứng cá nhân.
- Nến ngày toàn thị trường 20 năm chỉ vài trăm MB, không đáng kể.

## 4. Những gì app **không** làm

- Không đặt lệnh thật và không lưu mật khẩu tài khoản chứng khoán.
- Không đưa ra khuyến nghị mua hay bán. Mọi màn phân tích đều ghi rõ "mô phỏng để học, không phải lời
  khuyên đầu tư". Giao diện chuyển được tiếng Việt / tiếng Anh (A8).
- Không dùng API trả phí, kể cả API LLM. Phần giải thích chạy bằng quy tắc và thống kê. Tạm thời không
  dùng cả LLM chạy trên máy (A4).

## 5. Chia giai đoạn (đã chốt trong PRD v2; chi tiết ở `.finvest/product/roadmap.md`)

| Giai đoạn | Nội dung | Kết quả học được |
|---|---|---|
| R1 – Nền dữ liệu | Cào nến ngày, sự kiện doanh nghiệp, tick hằng ngày, lịch giao dịch | Hiểu dữ liệu thô, giá điều chỉnh |
| R2 – What-if | Mô phỏng X đồng / ngày N / mã E, có phí, thuế, cổ tức | Hiểu lợi nhuận thật khác lợi nhuận "nhìn chart" |
| R3 – Bảng điện | Bảng giá cho danh sách theo dõi, biểu đồ nến | Đọc bảng điện, cung cầu |
| R4 – Kịch bản | Backtest nhiều chiến lược, so sánh, walk-forward | Hiểu rủi ro, drawdown, overfitting |
| R5 – Phân tích "vì sao" | Phân rã biến động, dòng tiền, sự kiện | Tư duy phân tích bằng bằng chứng |
| R6 – Để sau | Tin tức, dữ liệu tài chính, nhật ký giao dịch giả lập | Cơ bản doanh nghiệp, kỷ luật |

## 6. Rủi ro chính và cách giảm

| Rủi ro | Cách giảm |
|---|---|
| Nguồn dữ liệu đổi hoặc chặn | Adapter tách riêng, có fixture test, cảnh báo "dữ liệu cũ" trên UI, có nguồn dự phòng |
| Tính sai lợi nhuận (cổ tức, chia tách) | Golden test tính tay; tester viết bộ tính độc lập; lead dùng opus cho PR liên quan tới tiền |
| Học sai do look-ahead hoặc overfitting | Mọi hàm phân tích đều nhận `as_of`; xếp hạng kịch bản bắt buộc có out-of-sample |
| Tốn token khi xây | Áp dụng bộ quy tắc trong [02-tiet-kiem-token.md](02-tiet-kiem-token.md) |
