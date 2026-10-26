# Finvest hand-off: read this first in a fresh session

Owner: the Scrum Master. Updated **2026-10-26 16:20**. Keep under ~6 KB: current state only. History lives in git,
`product/sponsor-answers.md` and the activity logs.

## 0. Start here
1. Run in FI_ROOT. fi-* agent types were not registered in session 815789d7, so the workflow ran with `portable:true`.
2. `CLAUDE.md` holds the rules. **Autopilot** (sponsor 2026-10-16): run plan/build/test/review/retro/merge-to-main
   yourself; ask only for scope, money, data loss, irreversible or no-safe-default product questions.
3. Stack: `make up` (web http://127.0.0.1:8080, api 127.0.0.1:**8001**; 8000 belongs to the sponsor's gateway).

## 1. Status
- Sprints 01–05 DONE and on **main (f548323)**. S04 = visual design (A25), S05 = prices right (CA table, factors,
  adjusted + reconstructed nominal, recon). Reviews PASS. Live recon VN30 30/30, 0 mismatches (2026-10-26 16:17).
- **Live = gateways** (compose project `finvest-live`, own DB gateways/data/finance_invest, auto-deploy from main via
  gw-poll). Dev checkout = project `finance_invest`; both bind 8080/8001, so dev/test stacks use other ports
  (tester.md §8: 18080/18001/15433). Never stop gw-app@finance_invest. Pre-0010 backup: gateways/backups/.
- Crawl is manual (A23). VCI V5 blocks after ~30 calls/h: ca_budget=28, so CA coverage grows ~25 names per press.

## 2. Next
- Sponsor presses on live after 15:00 on 10-27, 10-28, 10-29 (L1–L3; ticks lost if missed). SM checks the job.
- Sprint-06 per roadmap.md (R2 rest: F-043/F-044/F-050 clear the approximate flag) + carry-overs: B-05-9
  (insert_anomaly_once), recompute skips listing_change, "bấm lại sau ~1 giờ" hint (ux/app-shell.md), tests_be05 lint.
- Sponsor decision open: **A24-D1** (SM recommends: keep counting tests, exclude i18n). Next free label A26.

## 3. Environment
- Linux; `flock`, `md5sum`; no `gh` (merges via `sm.sh merge`). SSH push works for tuan666chuoikt.
- Next free sponsor label: **A25** (A24 is in the retro, not yet answered).

## 4. Cost
- Session 815789d7 (10-24): workflows ≈ 3.1 M subagent tokens (rev6 1.27 M, rev9 0.47 M, batch 0.49 M, rev11 0.88 M)
  plus planning/test/review agents ≈ 1.4 M. `cost.py` finds no transcripts for this session (it ran from Learning/).
