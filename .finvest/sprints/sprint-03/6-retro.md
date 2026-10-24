# 6-retro — Sprint 03

Author: `fi-pm`, 2026-10-24. Inputs: `5-review.product.md`, `5-review.tech.md`, `5-review.ai.md`, `4-test.{fe,be}.md`
(+ prev rounds), `activity.log`, `3-consult.*.md`, SM proposal D1.

## Velocity
- Committed **30 pts**: 25 at plan time, plus 5 for F-034 under A23. Accepted **30/30**, and all 7 rework items (U1–U7) passed.
- It took 9 days (Sat 10-17 → about Sun 10-25) against 7 planned. 42 tasks / 43 merges, 16 CHANGES rounds, 6 consults.
  There were 3 FE test rounds and 3 BE test rounds, and dag rev 11 (11 revisions of the task plan).
  Normalised to 7 days that is about 23 pts, within 25 % of 20.
- **Decision: keep 20 points per sprint** (data points: S01 20/20, S03 30/30 at +2 days). The extra 10 points were bought with the
  sprint extension and a rework round per lane. They are not spare capacity. roadmap.md velocity line updated.
- Sprint-02 (21 pts) has no measured velocity. Its tech review failed, and it is accepted only through this merge (5-review.product).

## What went well
- Money math held: golden 001 (635,975 / 10,610,975), DCA goldens and the VN-Index benchmark 14,753,846 all matched
  independent recomputation (tester oracle 8/8, AI review). No money bug reached a test round.
- The A23 scope change (timer → button) was replanned, built, retested and reviewed inside about 1 day.
- Testers found what fixtures could not: U1 (null `first_available` crashes the whole app), C1 (silent POST failure),
  and T4 (the source holds the connection 30 s and then returns 418, while our httpx timeout is 20 s, so blocks counted as timeouts).
- Leads enforced the S01 size and green-check rules: BE-jobs-crawl got CHANGES_REQUIRED for "size stop, no consult", and no task
  was merged without green checks.

## What did not go well
1. **Five tick tapes lost for good (C1–C5, 10-19…10-23).** The timer crawl failed every night with PermissionError because
   `data/raw` was root-owned. The C-row milestones (S01 R5) existed, but nobody ran the 21:00 check. A23 then removed the timer.
   Lesson: a clock milestone with no one awake to check it does not work.
2. **Crawl speed was planned before the source's block behaviour was known.** On round 2's press the crawl managed only
   about 1 symbol/min (67/1777 in 24 min). The V2 batch spike then found that multi-symbol calls return `200 []` or 418. Round 3 finished 97 %
   of the crawl in 79 s, then VCI blocked it with a retry window of about 1 h. Each finding cost a test round plus a dag revision (rev 9→11).
3. **Size stops fire on tests, not on scope.** FE-scenario-form: 442 vs 375 lines, of which 170 are tests + i18n (production 274,
   within plan). BE-jobs-crawl: 438 vs 360, of which 166 are tests. Both consults were answered "accept", and so were FE-web-scaffold,
   AI-whatif-lumpsum and AI-whatif-dca. The stop cost a round trip each time and changed no outcome. One caveat: BE-jobs-crawl's
   production code alone (232 vs 110) was also an underestimate.
4. The db test suite still cannot be run by the tester (T6; same as S02 B4). The lead covered it on a throwaway DB, which works but is fragile.
5. The live test numbers drift with every new bar (real-stack.mjs FPT 30.152.493 → 29.673.693), so tests need maintenance each round.

## Action items (≤ 5)

| # | Owner | File | Rule text / work | Sponsor |
|---|---|---|---|---|
| D1 | sa (proposal from sm) | `.finvest/briefs/owner.md` "Task block format" (replaces the "Size counts production + test + migration lines" part of S01 R3); `.finvest/briefs/lead.md` §3 | "`Size` and the 1.5× size stop count **production lines only** (incl. migrations). Tests and i18n catalogues are reported on a separate `Tests` line in the PR, and they never trigger a consult. The lead still flags tests that look padded." | **needs sponsor OK (A24-D1)**: it reverses part of A22-R3 |
| R2 | sa | `.finvest/briefs/owner.md` (live-source rule from S01 R3); `knowledge/` → `architecture/data.md` §1.2 per source | "Before any task plans crawl throughput, an S-spike probes the free source's **block behaviour**: the block signal (status / empty body / hold time), the request budget before a block, the retry window and the batch limit. It records these in data.md §1.2, all within ≤ 6 polite live calls. Throughput numbers in a plan cite that line, or the plan is not Ready." | needs sponsor OK (A24-R2) |
| R3 | sa | `sprint-04/2-tech-plan.md` (S04-RW rework tasks) | Carry: **T5b** status-rank guard on the ledger upsert (`complete > partial = blocked > missed`, + 1 db test, ~15 lines); **T5c** ops delete of the orphan `bars_1d 2026-10-24` row, logged in ops/README; **T6** one documented test DSN for the tester, together with S02 B4; pin `sell_date` in `real-stack.mjs`; add the VNINDEX `value / v` ratio query to the BE smoke | no (technical) |
| R4 | ai-arch + pm | `sprint-04/2-tech-plan.ai.md`; `product/backlog.md` F-048 | AI notes: (1) `whatif.py` curve loop: start at 0 or assert the first calendar day has a fill (latent `states[-1]` trap); (2) PM rewrites the ETF n/a wording for mid-range gaps ("n/a — thiếu dữ liệu ETF trong kỳ" rather than "since <date>"); (3) `holding_days` must not feed a future XIRR. The analytics.md §2.4 nullable mirror is already done (v1.2). | no |
| R5 | sm | `sprint-04/milestones.tsv` + handoff | Clock milestone **L1: Mon 2026-10-26, sponsor presses "Cào dữ liệu" after 15:00; sm confirms the 10-26 tick manifest + crawl_runs row by 23:00. Lost if missed: the 10-26 tape.** It is also F-034's live acceptance. The release note tells the sponsor that the first full catch-up may need 2 presses, about 1 h apart (VCI block). Each later trading day the board's stale chip is the reminder, since there is no timer now. | no |

## Câu hỏi cho sponsor — A24
- **A24-D1:** Giới hạn kích thước task (dừng ở 1,5×) chỉ tính code chạy thật, không tính test và file dịch i18n? Điều này sửa một phần A22-R3. Khuyến nghị: **đồng ý**. Hai lần dừng FE-scenario-form và BE-jobs-crawl đều do test, và cả hai lần đều được chấp nhận.
- **A24-R2:** Trước khi lên kế hoạch tốc độ cào, phải thăm dò trước cách nguồn miễn phí chặn (mã lỗi, số request trước khi bị chặn, thời gian chờ) và ghi vào data.md? Khuyến nghị: **đồng ý**.
