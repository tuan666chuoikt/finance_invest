# 4-test FE — sprint-03, retest (fi-fe-tester)

**Verdict: FAIL (minor)** — RW-U1..U7 all verified fixed; F-034 has 1 major + 2 minor bugs. Branch `test/sprint-03/fe` = origin/sprint-03 (a2c9bc4) merged in (a3c0bad + test edits). Previous report: `4-test.fe.prev-1.md`.
Numbers: Vitest 13 files / 78 tests green (the 4 `it.fails` flipped to `it`; U5 test body fixed: `getByText` throws, now `queryByText`). Real stack 127.0.0.1:8080 (Playwright 1.47 + axe 4.10 in /tmp/pw): `real-stack.mjs` **40/40 pass** (was 33/7). `crawl-button.mjs` 45 pass / 4 fail (below). Test scenarios were all "E2E …" and removed.

## RW-U1..U7 retest
| Id | Result |
|---|---|
| RW-U1 | PASS real stack: scenario with VN-Index `first_available:null` saved, page survives, card shows "VN-Index — n/a"; vitest flipped green |
| RW-U2 | PASS vitest (inside `main`) and axe 0 violations on empty page, cards, table, how-panel, EN, 375 px |
| RW-U3 | PASS card heading shows the user-given name (e2e locator now by heading; `aria-label` on the card is gone) |
| RW-U4 | BE half PASS per 4-test.be.md (422 NO_DATA); FE: pre-2025 date on the real stack gives no crash and a message |
| RW-U5 | PASS "1 session missing" (en), vitest |
| RW-U6 | PASS skeleton: axe clean while loading |
| RW-U7 | PASS table P/L uses U+2212 |

## F-034 crawl button (app-shell.md §Crawl button)
Method: idle uses the real stack; `/api/jobs*` is mocked for every other state (a real crawl takes hours and writes data; no real crawl was started). Job shapes taken from runner.py and the BE test report (incl. the real `interrupted` error). Note: at test time the real `/jobs/current` returned 200 (a BE job), so "real idle" only proves a finished/old job leaves no status line.
| State / criterion | Result |
|---|---|
| Idle: label, enabled, aria-busy=false, no status line, tooltip "Lần cuối: … · xong" (also EN), tab order chip → crawl → lang | PASS |
| Running: disabled, aria-busy, "Đang cào…", "Bước 1/2 — lệnh khớp 26/10: 12/30 mã", elapsed, then step 2 "giá ngày 3/6 phiên" by polling; role=status aria-live=polite | PASS |
| Reload while running | PASS (state read from the job) |
| Refused (POST → 409 JOB_RUNNING): "Đang có một lượt cào chạy (bắt đầu HH:mm) — chờ xong", running progress shown, one POST, clears on finish | PASS |
| Done: back to idle, exact line "✓ Xong HH:mm · 30 mã, 812.344 lệnh khớp · +6 phiên giá ngày · 2 mã bỏ qua · 3 phút 41 giây"; no-session variant; partial "(một phần, đến 10:30)"; dismissible; bars-status (freshness chip) refetched; reload after done = idle + tooltip | PASS |
| Error (job failed): cause + path, "đã lưu 12/30 mã", not auto-dismissed (5 s), survives reload, retry sends POST; real `interrupted` shape readable | PASS |
| GET /jobs/current 500: page alive, button usable | PASS |
| 375 px / EN: icon-only with accessible name, status wraps, no horizontal scroll; axe 0 violations in idle/running/done/refused/error/375 | PASS |

## Bugs
| Id | Sev | Owner | What |
|---|---|---|---|
| C1 | **major** | build (FE-crawl-button) | Starting a crawl when the POST fails (500, or the server unreachable) shows **nothing**: no status line, no message, button silently returns to idle. Spec §Error: "always the cause ... 'không kết nối được máy chủ'". `useCrawlJob.start.onError` handles only 409. Repro: block/500 `POST /api/jobs`, press the button. Test: crawl-button.mjs "POST 500 INTERNAL" / "POST network down". |
| C2 | minor | build | A quick double-click sends 2 POSTs (the pending state reaches the DOM after a tick). The server guard turns the 2nd into a 409 so no second job, but the user then sees the "already running (started …)" message for their own click. |
| S1 | minor (a11y, shell-wide) | build (FE-shell-bar) | Top-bar targets are 21 px high (Menu, VI, EN, crawl 27x21), below the 24x24 px minimum of WCAG 2.2 AA 2.5.8; axe does not flag it. Not specific to F-034. |
Not checked: real done/failed job from a real crawl (BE: 3 h run; mocked here), visual review of /tmp/pw/crawl375.png, dark mode, "Chi tiết" link (not built, noted by the builder), chip text change after done beyond the bars-status refetch.

## Files
`apps/web/e2e/crawl-button.mjs` (new; run `PW_DIR=/tmp/pw node apps/web/e2e/crawl-button.mjs`), `apps/web/e2e/real-stack.mjs` (patch route removed, card locator by heading), `apps/web/src/features/scenarios/fe-tester.gaps.test.tsx` (it.fails → it).
