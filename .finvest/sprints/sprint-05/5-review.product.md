# Sprint 05 — Product review (fi-pm, 2026-10-26)

Evidence (FI_ROOT only, retro S04 R5): `4-test.be.md` round 2 **PASS** (B-05-1..7 fixed, B-05-8 open), `4-test.fe.md` round 2 **PASS**
(F-05-1 fixed, §9 checklist all PASS at 375/768/800/1280 light+dark), shots opened in `shots/FE-test/` (crawl-running/done/failed, cards, FE-rw-table
768/800, FE-rw-dca-details). Sprint goal: **Prices are right.**

**Open condition:** `5-review.tech.md` (sa) and the AI review run in parallel and are **not on disk** at writing time. Merge to main waits for both PASS;
a must-fix from either reopens the story it touches.

## Per story

| Story | Pts | Verdict | Evidence / failing criterion | Stage at fault |
|---|---|---|---|---|
| F-013 | 1 | **DONE** (live check at L1) | board bar per press, idempotent, missed press: fixture tests; B-05-5 (press 15:00–15:05 targets the day before) fixed, unit-tested. Not exercised in a real press yet → L1 (27/10 after 15:00) confirms the observed bar. | — |
| F-014 | 5 | **DONE** (live check at L2) | V5 rows incl. ISS stock dividends (B-05-1 fixed: HPG 10:1 on 2026-05-25 stored); diff log one row per changed field; VN30-first order + budget 28 (B-05-2); unmapped amount → NULL + anomaly. UI step 3/3 + "chờ lượt sau" shots match app-shell.md. | — |
| F-015 | 5 | **DONE** | Oracle (Fractions) over 1,346 stored factors: 1,303 exact, 43 ≤ 1 VND inversion rounding; reconstructed × G vs V2: 292,577 rows, 0 > 1 VND; HPG 2026-05-22 nominal 26,350 (= 23,955 × 1.1 rounded). Golden cases G1–G13b pass. Recompute idempotent (md5 equal). | — |
| F-016 | 3 | **DONE, conditional** | G10 rows (0.204 % listed / 0.041 % not), `crawl recon` CLI, S2 rows stored as `ssi_s2`, exit 1 on missing names: pass. **"VN30 30/30" not met on the test copy: 26/30** (VNM, VPB, VPL, VRE). | data (B-05-8), not build |
| F-023 | 2 | **DONE** | `data_snapshot` = max fetched-at of served rows, what-if reproducible, `/health` rules_version 2026.10.28 (E tests + live-stack repeat calls). | — |
| F-033 | 1 | **DONE** | no-broker audit 6 tests; B-05-3 (js/mjs/jsx blind spot) fixed, probe XPASSes. | — |
| S05-RW | 2 | **DONE** | OBS-7 top bar one line (h=53) at all widths; 768/800 shots present; headers 1 line; DCA one shift line "…: 5 lần" + "Xem" (F-05-1 fixed). | — |

## F-016 judgment (26/30)
The 4 names have **1** `vci` bar each in the live copy (FPT has 9,893): their V2 history was never backfilled, so no number of CA presses
can reconcile them. The code did the right thing: it reported the 4 by name and exited 1 instead of a false green. The failing part is a data
gap in the environment, not the story's logic. **Accepted on condition C1:** after the live deploy, SM runs `crawl bars --only VNM,VPB,VPL,VRE`
(≤ 30 calls, one window), then `crawl corporate-actions` + `recompute` + `crawl recon` → **30/30**, logged in activity.log.
If C1 is not 30/30 by the sprint close (2026-10-29 18:00), F-016 goes back to NOT DONE and its 3 pts move to S06.

## Conditions before close
- C0: `5-review.tech.md` and the AI review PASS (open).
- C1: F-016 live recon 30/30 after backfill (above).
- C2: L1/L2 presses confirm F-013's observed board bar and F-014's VN30 `corporate_actions` rows on live.

## UX change from this review
`product/ux/app-shell.md` §Crawl button, Done row: the "· N mã chờ lượt sau" segment gets a hint "Nguồn tạm chặn sau ~30 lượt gọi; bấm lại sau
~1 giờ để lấy tiếp" (title + screen-reader text). Needed: without it the sponsor sees "4 mã chờ lượt sau" and presses again at once, which hits
the ~1 h block. Small FE task for S06; not blocking this sprint.

## Notes carried
- B-05-9 info: `corporate_action_unmapped` anomalies append per run; the Data quality page (F-021, S06) must count distinct (symbol, source_event_id).
- "≈ Gần đúng" stays on cards until F-043/F-044 (planned).
