# 02 — Bộ quy tắc tiết kiệm token và chỗ chúng được cài

Rút từ kinh nghiệm dự án Harbor: session điều phối chiếm khoảng **98%** token (3,56 tỷ token đọc
cache qua 7.196 bước với context khoảng 500k), trong khi 567 agent con cộng lại chỉ khoảng 96 triệu.
Vì vậy ưu tiên số 1 là giữ session chính nhỏ và ngắn.

| # | Quy tắc | Cài ở đâu |
|---|---|---|
| **1. Chọn model theo việc** | | |
| 1a | Dev, tester, phần lớn lead dùng sonnet; PM dùng opus; PO và architect dùng fable (ít gọi) | frontmatter `model:` trong `.claude/agents/*.md` |
| 1b | Lead dùng opus chỉ cho PR về contract, tính tiền/lợi nhuận, đăng nhập, ops | `leadModel` của từng task trong `dag.json`; workflow đọc trường này |
| 1c | Helper chỉ theo dõi dùng haiku | `model: 'haiku'` trong `finvest-sprint.workflow.js` (notify, wait, commit) |
| **2. Cắt gọn session điều phối** | | |
| 2a | Mỗi ngày một session mới, khởi động từ handoff | `/fi-handoff`, `.finvest/handoff.md` (giới hạn khoảng 6 KB) |
| 2b | Workflow chạy cả sprint ở nền; session chính không theo dõi từng agent | `/fi-build` → `finvest-sprint.workflow.js` |
| 2c | Activity log: mỗi agent ghi một dòng; hỏi tiến độ thì đọc log | `bin/log.sh`, `bin/progress.py`, `/fi-status` |
| 2d | Agent tự làm git (push, PR, merge) | `bin/sm.sh push / pr / merge`; Scrum Master chỉ chạy `sm.sh finvest` |
| 2e | Tắt MCP không dùng; dùng context chuẩn, không dùng loại lớn | Làm tay: `/mcp` tắt server không cần cho dự án này; `/model` chọn bản context chuẩn |
| 2f | CLAUDE.md gọn (dưới khoảng 10 KB), luật code và review nằm trong brief từng vai | `CLAUDE.md` + `.finvest/briefs/*.md` |
| 2g | Theo dõi merge 10 phút một lần thay vì 90 giây | `bin/wait-merged.sh` (mặc định 570 giây) |
| **3. Agent đọc ít, nói ít** | | |
| 3a | Mỗi task một agent mới; vòng sửa cũng là agent mới | workflow gọi `agent()` mới cho mỗi build, fix và review |
| 3b | Báo cáo trả về tối đa 5 dòng, chi tiết ghi ra file | `briefs/common.md` + schema `note` trong workflow |
| 3c | Brief giao việc 3–5 dòng, kèm "làm theo briefs/<vai>.md" | `briefs/README.md`, các prompt trong workflow |
| 3d | Task card chỉ in đúng khối kế hoạch của task | `bin/task.sh <TASK>` |
| 3e | Đọc theo đoạn: không `cat` file trên khoảng 300 dòng; `rg` rồi `sed -n`; mọi lệnh tìm đều có giới hạn | `briefs/common.md`, `briefs/dev.md` bước 0 |
| 3f | Bọc lệnh test bằng `q.sh`: chỉ in mã thoát, dòng tóm tắt và lỗi đầu; log đầy đủ ở `/tmp/fi-q` | `bin/q.sh` |
| 3g | `omitClaudeMd: true` cho mọi agent con | frontmatter agent |
| 3h | `maxTurns`: dev 100, tester 150, lead 60 (PO/PM/architect 40–60) | frontmatter agent |
| **4. Bớt chạy test lặp** | | |
| 4a | Dev chạy test liên quan và e2e của tính năng mình một lần, sau đó chỉ chạy lại test đỏ | `briefs/dev.md` bước 5 |
| 4b | Hành trình e2e chính (`@key`) chỉ do lead chạy, trên nhánh đã sync | `briefs/lead.md` bước 4 |
| 4c | Nhánh nền đổi thì chỉ chạy lại test bị ảnh hưởng; bộ đầy đủ chạy theo milestone | `briefs/lead.md`, thông báo milestone của workflow |
| **5. Mức suy nghĩ và độ lớn task** | | |
| 5a | Effort theo task (`high`/`medium`) do architect gắn sẵn | `effort` trong `dag.json`; workflow truyền vào `agent()` |
| 5b | "Think briefly" cho bước thường lệ | `briefs/common.md` |
| 5c | Diff vượt 1,5 lần `size` thì dừng, xin chia nhỏ | `briefs/dev.md` bước 3, `size` trong `dag.json` |
| 5d | Vòng sửa gọn: chỉ đọc danh sách must-fix và file liên quan | `briefs/dev.md` bước 9 |
| **6. Cache và đo đạc** | | |
| 6a | `cacheTtl: "1h"` cho agent con | `experimental.cacheTtl` trong frontmatter (cần Claude Code ≥ 2.1.248) |
| 6b | Đo chi phí quy ra USD từ transcript | `bin/cost.py [--by-part]`; ghi con số vào handoff và retro |

Kiểm tra phiên bản: `claude --version` (bản trong VS Code và bản terminal có thể khác nhau).
