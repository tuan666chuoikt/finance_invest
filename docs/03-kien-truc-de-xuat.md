# 03 — Kiến trúc đề xuất ban đầu

> Đây là **điểm xuất phát** cho software architect và AI architect. Họ sẽ chốt bằng ADR ở bước
> `/fi-architect` và có thể thay đổi đề xuất này nếu có lý do.

## 1. Nguyên tắc

- Một máy, một người dùng, chi phí 0. Ưu tiên công cụ miễn phí, phổ biến, dễ bảo trì.
- **Tính đúng tiền là ưu tiên số một**: Decimal hoặc số nguyên VND, luật thị trường đặt ở một module
  duy nhất, golden test.
- **Không nhìn trước tương lai**: mọi phép phân tích nhận `as_of`.
- Nguồn dữ liệu có thể thay được: cổng `MarketDataSource`.

## 2. Thành phần

```
             ┌──────────────── apps/web (React + Vite + TS) ────────────────┐
             │ Bảng điện · Biểu đồ nến · What-if · So sánh kịch bản · "Vì sao" │
             └───────────────▲──────────────────────────▲───────────────────┘
                     REST (OpenAPI)              WebSocket/SSE (giá realtime)
             ┌───────────────┴────────── apps/api (FastAPI) ──────────────────┐
             │ market-data · portfolio-sim · backtest · analytics · news       │
             └───────▲───────────────────────────────▲────────────────────────┘
                     │ SQL                          │ gọi nội bộ (Python package)
   ┌─────────────────┴─────────┐        ┌───────────┴───────────────┐
   │ PostgreSQL + TimescaleDB  │◄───────│ services/analytics        │
   │ ticks · bars_1m · bars_1d │        │ mô phỏng · backtest ·     │
   │ corp_actions · calendar   │        │ chỉ số · phân rã biến động│
   │ news · runs               │        └───────────────────────────┘
   └─────────────────▲─────────┘
                     │ upsert idempotent
   ┌─────────────────┴──────────────────────────────────────────────┐
   │ services/crawler (Python, APScheduler)                          │
   │ adapters: vnstock / SSI / DNSE / RSS  →  MarketDataSource port   │
   │ jobs: board poll (giờ giao dịch) · tick sau 15:05 · daily · CA   │
   └─────────────────────────────────────────────────────────────────┘
```

| Phần | Đề xuất | Lý do |
|---|---|---|
| Ngôn ngữ backend | Python 3.12 + `uv` | Hệ sinh thái dữ liệu (pandas/polars, vnstock) |
| API | FastAPI + Pydantic | Tự sinh OpenAPI rồi sinh type cho FE (`packages/contracts`) |
| DB | PostgreSQL 16 + TimescaleDB (docker compose) | Hypertable và nén cho tick; vẫn là SQL thường |
| Phân tích nghiên cứu | Xuất Parquet + DuckDB / Jupyter | Thử nghiệm nhanh, không đụng DB chính |
| Lập lịch cào | APScheduler trong `services/crawler` | Đơn giản, không cần hạ tầng thêm |
| Realtime | WebSocket từ API, nguồn là Postgres LISTEN/NOTIFY | Không cần Redis ở v1 |
| Frontend | React + Vite + TypeScript, TanStack Query, `lightweight-charts`, bảng ảo hoá | Biểu đồ nến miễn phí, bảng điện mượt |
| Test | pytest, Hypothesis (property test cho tính tiền), Vitest, Playwright, axe | |
| LLM (tuỳ chọn) | Ollama chạy trên máy, chỉ để tóm tắt bằng chứng | Không tốn tiền; không bao giờ là nguồn của con số |

## 3. Mô hình dữ liệu (phác thảo)

- `symbols(symbol, exchange, name, icb_sector, listed_at, delisted_at)`
- `trading_calendar(date, exchange, is_open, sessions)`
- `ticks(symbol, ts, seq, price, volume, side, source)`: hypertable, khoá tự nhiên `(symbol, ts, seq)`
- `bars_1m`, `bars_1d(symbol, ts, o, h, l, c, v, value, source)`, giá **danh nghĩa**
- `corporate_actions(symbol, type, ex_date, record_date, pay_date, ratio, amount, source)`
- `adj_factors(symbol, ex_date, factor)`: dùng để tính giá điều chỉnh khi đọc
- `flows_1d(symbol, date, foreign_buy, foreign_sell, prop_buy, prop_sell)`
- `news(id, ts, title, url, source, symbols[])`
- `sim_runs / backtest_runs(id, params_json, as_of, engine_version, result_json)`: để chạy lại ra đúng kết quả cũ

## 4. Cấu trúc repo

```
finance_invest/
  CLAUDE.md  README.md  docs/  .claude/  .finvest/
  apps/web/            FE
  apps/api/            FastAPI (BE)
  services/crawler/    cào dữ liệu (BE)
  services/analytics/  mô phỏng, backtest, phân tích (AI engineer)
  packages/contracts/  OpenAPI → TS types (BE)
  packages/market-rules/  luật thị trường VN, một nơi duy nhất (BE, AI architect duyệt)
  docker-compose.yml
```

## 5. Ngữ cảnh nghiệp vụ (bounded context, DDD)

| Context | Trách nhiệm |
|---|---|
| market-data | nguồn, lịch giao dịch, tick/bar, sự kiện doanh nghiệp, giá điều chỉnh |
| portfolio-sim | lệnh giả lập, khớp, phí, thuế, T+2, cổ tức → dòng tiền và danh mục |
| backtest | chiến lược, chạy nhiều kịch bản, walk-forward, chỉ số hiệu quả |
| analytics | phân rã biến động, dòng tiền, liên kết tin tức, xếp hạng có kiểm định |
| news | thu thập, gắn mã, loại trùng |
| board-ui | trình bày (chỉ FE) |
