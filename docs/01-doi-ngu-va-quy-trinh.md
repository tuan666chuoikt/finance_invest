# 01 — Đội agent và quy trình làm việc

Bạn là **sponsor**: bạn đưa yêu cầu, trả lời câu hỏi, duyệt ở các cổng và là người duy nhất merge vào
`dev`/`main`. Session chính của Claude Code là **Scrum Master**: điều phối, không tự làm thay agent.

## 1. Đội

| Nhóm | Agent | Model | Việc chính | Cấm làm |
|---|---|---|---|---|
| Sản phẩm | PO `fi-po` | fable | Viết PRD: làm cái gì, vì sao | story, thiết kế, code |
| | PM `fi-pm` | opus | Backlog, tiêu chí chấp nhận, UX spec, mục tiêu sprint, nghiệm thu | quyết phạm vi sản phẩm, code |
| Kiến trúc | Software architect `fi-software-architect` | fable | Stack, DDD, contract, chia task, lập `dag.json`, review kỹ thuật | code production |
| | AI/Quant architect `fi-ai-architect` | fable | Thiết kế mô phỏng, backtest, phân tích "vì sao", tin tức, eval, review AI | code production |
| Làm code | FE dev `fi-fe-dev` | sonnet | `apps/web` | sửa contract, làm vượt phạm vi |
| | BE dev `fi-be-dev` | sonnet | `apps/api`, `services/crawler`, `packages/*` | như trên |
| | AI engineer `fi-ai-engineer` | sonnet | `services/analytics` | như trên |
| Kiểm soát | Tech lead `fi-tech-lead` (mỗi phía một agent) | sonnet; opus cho PR về contract, tính tiền/lợi nhuận, đăng nhập, ops | Review, gộp xung đột, merge vào `sprint-NN` | viết tính năng, merge vào `dev` |
| | FE tester / BE tester | sonnet | e2e, độ chính xác số liệu, bảo mật, realtime, accessibility | sửa code đang test |
| Điều phối | Session chính (Scrum Master) | model của phiên | Chạy các bước sprint, giao việc, chuyển câu hỏi, báo sponsor | làm thay việc của agent |
| Phụ | helper trong workflow | haiku | Theo dõi merge (10 phút một lần), commit `.finvest/`, gửi thông báo | mọi việc khác |

Quy tắc chọn model: việc cần suy nghĩ sâu nhưng ít lượt gọi (PO, architect) dùng **fable**. PM dùng
**opus**. Việc nhiều và lặp lại (dev, tester, phần lớn lead) dùng **sonnet**. Việc chỉ theo dõi dùng
**haiku**.

## 2. Vòng đời

```
/fi-prd draft ──► (bạn trả lời) ──► /fi-prd approve
      ▼
/fi-backlog init ──► /fi-architect ──► /fi-sprint-plan ──► (bạn: "go")
      ▼
/fi-build  →  workflow chạy nền theo dag.json:
              task đủ điều kiện + còn chỗ  →  dev mới  →  lead
                                             ↑            │ CHANGES_REQUIRED
                                             └─ dev mới sửa ◄┘
              dừng và báo Scrum Master khi: consult, vòng review thứ 3,
              cần sponsor quyết, agent chết, xong milestone
      ▼
/fi-test  ──►  /fi-review  ──►  (bạn thử app, merge sprint → dev)  ──►  /fi-retro
```

Mỗi bước đều dừng ở một **cổng** để bạn đọc và sửa. Sửa càng sớm càng rẻ, rẻ nhất là ở PRD.

## 3. Nhánh git

`main` ← `dev` ← `sprint-NN` ← `task/sprint-NN/<TASK>`

- Dev tự commit, tự push và tự mở PR. Nếu máy có `gh` thì PR được mở trên GitHub; nếu chưa có thì lead
  review thẳng trên nhánh.
- Lead merge task vào `sprint-NN` bằng `sm.sh merge` (merge `--no-ff` dưới khoá `flock`, từ chối nếu
  head đã đổi sau khi review hoặc nếu chưa có APPROVE).
- Chỉ bạn merge `sprint-NN` vào `dev` và `dev` vào `main`.

## 4. Hằng ngày bạn làm gì

1. Sáng: mở session mới rồi gõ *"đọc .finvest/handoff.md rồi chạy /fi-status"*.
2. Trả lời câu hỏi mà Scrum Master chuyển tới (phạm vi, tiền, rủi ro).
3. Hỏi tiến độ thì gõ `/fi-status` (tóm tắt từ activity log, gần như không tốn token).
4. Tối: gõ `/fi-handoff` để lưu trạng thái, rồi đóng session.

## 5. Bảng file (mỗi file chỉ một người viết)

Danh sách đầy đủ nằm trong [`.finvest/briefs/owner.md`](../.finvest/briefs/owner.md). Tóm tắt:

- `.finvest/product/`: brief (bạn), PRD (PO), backlog, roadmap, UX (PM), sponsor-answers (Scrum Master ghi nguyên văn lời bạn)
- `.finvest/architecture/`: system, codebase, data, contracts (software architect); analytics (AI architect); ADR
- `.finvest/sprints/sprint-NN/`: plan, tech-plan, `dag.json`, build/PR/test/review/retro reports, `activity.log`
- `.finvest/knowledge/vn-market.md`: luật thị trường VN (AI architect chịu trách nhiệm xác minh)

## 6. Definition of Done (tóm tắt)

Task đã merge và không có lệch contract nào bị giấu. Mỗi tiêu chí chấp nhận có một test sẽ fail nếu bỏ
tính năng đi. **Số tiền và lợi nhuận được đối chiếu với một cách tính độc lập.** Review kỹ thuật PASS,
PM nghiệm thu, và tài liệu liên quan đã được cập nhật.
