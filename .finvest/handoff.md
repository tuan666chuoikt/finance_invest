# Finvest hand-off: read this first in a fresh session

Owner: the Scrum Master. Updated **2026-10-24 17:40**. Keep under ~6 KB: current state only. History lives in git,
`product/sponsor-answers.md` and the activity logs.

## 0. Start here
1. Run in FI_ROOT. fi-* agent types were not registered in session 815789d7, so the workflow ran with `portable:true`.
2. `CLAUDE.md` holds the rules. **Autopilot** (sponsor 2026-10-16): run plan/build/test/review/retro/merge-to-main
   yourself; ask only for scope, money, data loss, irreversible or no-safe-default product questions.
3. Stack: `make up` (web http://127.0.0.1:8080, api 127.0.0.1:**8001**; 8000 belongs to the sponsor's gateway).

## 1. Status
- Sprints 01–03 DONE, **main = bb3f588** (sprint-03 incl. sprint-02, fast-forward). Reviews tech/ai/product PASS, 30/30 pts.
- **A23 (2026-10-24): crawling is manual only** — "Cào dữ liệu" button (F-034, POST /api/jobs). The systemd timer
  is uninstalled. A press: ticks (≈1 500 KBS req, only on a trading day) + SSI full-board snapshot (3 req) + ≤40 V2 gaps.
  VCI V2 blocks the IP after ~1.5 min of heavy use (418 after a 30 s hold, about 1 h); the job then fails with
  "nguồn … đang chặn tạm, thử lại sau ~1 giờ". A cold catch-up may need 2 presses about 1 h apart.
- Ticks for 2026-10-19..23 are lost (timer PermissionError; data/raw was root-owned, fixed 10-24 by chown via docker).

## 2. Next
- **Sponsor decisions open:** A24-D1 (size limit counts production code only, not tests/i18n; SM recommends yes),
  A24-R2 (spike a free source's block behaviour before planning crawl speed; SM recommends yes). See `sprints/sprint-03/6-retro.md`.
- Clock milestone: sponsor presses the button Mon 2026-10-26 after 15:00 (first live tick path); SM checks the job by 23:00.
- Sprint-04 carry-overs: T5b (session status regresses complete→blocked, arch), T5c (orphan bars_1d 10-24 row),
  T6 (db test suite DSN/password), AI notes (i=-1 curve trap, ETF n/a wording, DCA holding_days), VNINDEX pre-2012
  ratio smoke, pin `sell_date` in e2e. Then `/fi-sprint-plan` for sprint-04 per roadmap.

## 3. Environment
- Linux; `flock`, `md5sum`; no `gh` (merges via `sm.sh merge`). SSH push works for tuan666chuoikt.
- Next free sponsor label: **A25** (A24 is in the retro, not yet answered).

## 4. Cost
- Session 815789d7 (10-24): workflows ≈ 3.1 M subagent tokens (rev6 1.27 M, rev9 0.47 M, batch 0.49 M, rev11 0.88 M)
  plus planning/test/review agents ≈ 1.4 M. `cost.py` finds no transcripts for this session (it ran from Learning/).
