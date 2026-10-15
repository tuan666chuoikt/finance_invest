# Finvest — phòng thí nghiệm đầu tư chứng khoán Việt Nam

Web app cá nhân để **học đầu tư bằng dữ liệu thật**:

- **Bảng điện tử** cho danh sách mã theo dõi, cập nhật gần realtime.
- **Bộ cào dữ liệu** lưu ở đơn vị thời gian nhỏ nhất lấy được miễn phí: tick, rồi nến 1 phút, rồi nến ngày.
- **Mô phỏng what-if**: "nếu đầu tư X đồng vào mã E ngày N thì giờ lời hay lỗ bao nhiêu", tính đủ phí,
  thuế, lô, T+2 và cổ tức.
- **So sánh nhiều kịch bản** đầu tư, có kiểm tra out-of-sample.
- **Phân tích "vì sao giá tăng"** trong một khoảng thời gian, dựa trên bằng chứng.

> Mô phỏng để học, **không phải lời khuyên đầu tư**. App không đặt lệnh thật.

Dự án được xây bởi một đội agent Claude Code theo Scrum. Bạn là sponsor; session chính là Scrum Master.

## Tài liệu

| File | Nội dung |
|---|---|
| [docs/00-kha-thi.md](docs/00-kha-thi.md) | Có khả thi không, giới hạn dữ liệu, giai đoạn, rủi ro |
| [docs/01-doi-ngu-va-quy-trinh.md](docs/01-doi-ngu-va-quy-trinh.md) | Đội agent, model, quy trình sprint, nhánh git, việc hằng ngày của bạn |
| [docs/02-tiet-kiem-token.md](docs/02-tiet-kiem-token.md) | Bộ quy tắc giảm token và nơi mỗi quy tắc được cài |
| [docs/03-kien-truc-de-xuat.md](docs/03-kien-truc-de-xuat.md) | Stack và mô hình dữ liệu đề xuất (architect chốt) |
| [docs/04-lo-trinh-hoc.md](docs/04-lo-trinh-hoc.md) | Lộ trình học đầu tư gắn với từng tính năng |
| [CLAUDE.md](CLAUDE.md) | Luật cho session chính (tiếng Anh, để tiết kiệm token) |
| [.finvest/](.finvest/) | Brief vai, script, artifact sprint, kiến thức thị trường |

## Bắt đầu

Yêu cầu: Claude Code ≥ 2.1.248, git, Python 3.12 + `uv`, Node 20 + `pnpm`, Docker (cho Postgres), `rg`.
Không bắt buộc: `gh` (để mở PR trên GitHub).

Trong Claude Code, mở thư mục này rồi gõ lần lượt:

```
/fi-prd draft          # PO viết PRD, kèm các câu hỏi cho bạn
/fi-prd <câu trả lời>  # rồi /fi-prd approve
/fi-backlog init
/fi-architect
/fi-sprint-plan
/fi-build              # workflow chạy cả sprint ở nền
/fi-status             # hỏi tiến độ bất cứ lúc nào
/fi-handoff            # cuối ngày
```

## Cấu trúc

```
CLAUDE.md                 luật cho Scrum Master (session chính)
.claude/agents/           10 agent: fi-po, fi-pm, fi-software-architect, fi-ai-architect,
                          fi-fe-dev, fi-be-dev, fi-ai-engineer, fi-tech-lead, fi-fe-tester, fi-be-tester
.claude/commands/         /fi-prd … /fi-handoff
.finvest/briefs/          luật theo vai (common, owner, dev, lead, tester)
.finvest/bin/             q.sh, task.sh, log.sh, sm.sh, wait-merged.sh, progress.py, cost.py,
                          finvest-sprint.workflow.js
.finvest/knowledge/       vn-market.md: luật thị trường VN
.finvest/product/         brief, sponsor-answers, (prd, backlog, roadmap, ux)
.finvest/templates/       dag.example.json
.finvest/handoff.md       điểm bắt đầu của mỗi session mới
docs/                     tài liệu tiếng Việt cho người đọc
apps/ services/ packages/ code (sẽ được tạo từ sprint 1)
```

## Chạy (backend)

```
uv sync
cp .env.example .env
make test-kernel                                  # offline: pytest + ruff + mypy + import-linter
uv run finvest-crawl ticks --date 2026-10-16      # thoát 3 "not implemented" cho tới BE-feed-ticks
uv run uvicorn finvest_api.main:app               # GET /health
```
