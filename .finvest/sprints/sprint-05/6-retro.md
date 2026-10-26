# 6-retro — Sprint 05

Author: `fi-pm`, 2026-10-26. Inputs: `5-review.product.md`, `4-test.{be,fe}.md` (+ prev-1), `activity.log`, `2-tech-plan.md` v1.4 / dag rev 7,
consult answers in this folder, sprint-04 retro.

## Velocity
- Committed **19 pts**. Accepted **16 unconditional + 3 conditional (F-016, C1 live recon 30/30)** → 19/19 if C1 holds, else 16/19.
- Elapsed: 11:41 plan → 16:10 FE retest = about 4.5 h for a 4-day sprint. 26 merges, 1 red test round per lane (BE 1 high + 1 medium + 4 low,
  FE 1), dag rev 1 → 7 (+7 fix tasks in rework R1). Clock milestones L1–L3 (live presses 27–29/10) are still ahead; review closes on them.
- **Velocity stays 20.** The money-math sprint landed on time; the one gap was data, not capacity.

## What went well
- The test-side oracle (Fractions, written from the plan table) found B-05-1: ISS stock dividends were unmapped, so reconstructed prices
  matched the source only because the event was missing on both sides (a tautological green). After the fix: 292,577 rows, 0 > 1 VND.
- The recon CLI refused a false green: 26/30 → exit 1, names listed.
- The migration rehearsal on a fresh live dump (1.0 s up, 0.6 s down, row counts identical) removes the deploy risk before it is taken.

## What did not go well
1. **Mid-run dag changes were not picked up by the running workflow.** sa wrote dag revs 5–7 while tasks ran; the running workflow kept the
   old dag, so SM had to re-run it twice to pick up AI-recon-xsrc and the fix tasks.
2. **sa and ai gave conflicting consult answers** on BE-recon-s2 (sa: `slack_vnd=10`; ai: no slack, `self_check=` flag). The dev blocked until
   sa withdrew in round 2. Reconciliation math is the AI lane's domain; that owner should have decided first.
3. **The source's ~30-call limit was learned in the test round, not the spike.** V5 blocks after ~30 ok calls for ~1 h; the plan's B = 40
   ended in a block (B-05-2), and the BE tester's own replays spent ~59 more calls. M0 recorded "block behaviour" but not a measured budget.
4. **Environment data gap (B-05-8):** 4 VN30 names had no V2 history on the live copy; no one checked VN30 bar coverage before committing "30/30".

## Action items (≤ 5)

| # | Owner | File | Rule / work | Sponsor |
|---|---|---|---|---|
| R1 | sm | `.finvest/briefs/sm.md` (workflow section) | **A dag change does not reach a running workflow.** After sa bumps `dagRev`, SM stops and re-launches the workflow once (not per change); sa batches mid-run dag edits into one rev when possible. | no |
| R2 | sa | `.finvest/briefs/architect.md` (consult rules) | **One consult, one decider: the domain owner answers** (money/analytics math → ai-arch; schema, adapters, infra → sa). The other may comment; a card is re-emitted only from the decider's answer. | no |
| R3 | sa + dev | `architecture/data.md` §1.2; spike template | A spike records a **measured call budget per source** (calls until block, hold window) and the plan's per-press budget cites it with margin (V5: ~30 → B = 28). Testers count their own calls against it. | no |
| R4 | pm | `.finvest/agents/fi-pm.md` plan step; sprint plan template | Any "N/N names" criterion gets a **coverage pre-check** at planning (bars per name ≥ 1 year on live), or the gap becomes a backfill task in the sprint. | no |
| R5 | sm | live, after deploy | C1: backfill `VNM,VPB,VPL,VRE` bars, recompute, `crawl recon` → 30/30; log it. | no |

## Câu hỏi cho sponsor
- **A24-D1 (vẫn mở):** Giới hạn kích thước task (dừng ở 1,5×) có tính test không? Khuyến nghị SM: **vẫn tính test, chỉ bỏ file dịch i18n**. Đến khi trả lời, giữ luật hiện tại.
- **Thông tin (không cần trả lời):** nút "Cào dữ liệu" sẽ có gợi ý "bấm lại sau ~1 giờ" khi còn mã chờ lượt sau — nguồn sự kiện quyền chặn sau ~30 lượt gọi. Sprint 06 thêm vào.
