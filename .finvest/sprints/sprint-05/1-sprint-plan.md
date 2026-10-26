# Sprint 05 — Plan

Owner: `fi-pm`, 2026-10-26. **Mon 2026-10-26 → Thu 2026-10-29 18:00.** Branch `sprint-05` from `main` 0de35b7.
Inputs: `product/roadmap.md` (old "S04" row, slipped when sprint-04 became the A25 visual-design sprint),
`product/backlog.md` (Sprint-05 slice), `sprints/sprint-04/6-retro.md`, `sprints/sprint-03/6-retro.md` R2,
`architecture/data.md` §1.2–§1.4, `product/sponsor-answers.md` A18-A, A23, A25.

## Goal
**Prices are right.** After a press of "Cào dữ liệu" on a trading day: the day's bar is stored for every listed stock
(observed nominal from the SSI board) and both indices; corporate actions are in a table with a diff log (new crawl
step 3); we compute our own adjustment factors, the adjusted series and the reconstructed nominal history before crawl
start (flagged, A18-A); a reconciliation run covers all 30 VN30 names; every result's `data_snapshot` means "max
fetched-at of its inputs" and recomputes identically.

Not in this sprint: the scenario engine still uses source-adjusted prices, so the **"≈ Gần đúng" flag stays on cards**
until F-043/F-044 (R2, S07) replay nominal prices + events. The mismatch list gets its page with F-021 (S06).

## Re-check against A23 and the block rule
- **A23 (manual only):** no after-close or 17:00 job. Every "daily" criterion now means "on each press". F-013 is mostly
  delivered by F-034 + BE-ssi-snapshot (S03) → 2 → 1 pt (acceptance + missed-press case). Corporate actions become
  **step 3** of the press; the "Sunday full pass" becomes a deferred queue drained over presses (VN30 + scenario
  symbols first).
- **Retro S03 R2 (spike block behaviour first):** V5 (`iq.vietcap.com.vn`, corporate events) and S2 (SSI history,
  VN30 cross-check for F-016) have **no recorded block behaviour** in data.md §1.2 (only V2: ~60–70 calls then 418).
  → spike task first (milestone M0, ≤ 6 polite calls per source): block signal, budget before a block, hold/retry
  window, page/batch limit, plus V5 pay-date / cash-per-share field names. F-014's per-press budget cites that line.
  (A24-R2 is not formally answered; the rule is applied as planning practice since it only adds a few calls.)
- F-023 is mostly delivered (S03 returns `data_snapshot` + `rules_version`; drawer shows them) → 3 → 2 pts.

## Capacity
Velocity **20** (S04 18/18 was CSS-only; not a capacity signal). Committed **19 pts**, 1 pt buffer.
First to slip: **F-016's S2 cross-check** (keep the local recon on V2), then **S05-RW header/DCA lines**. Never slipped: F-014, F-015.

## Committed stories

| Story | Pts | Title | Order / depends on |
|---|---|---|---|
| F-014 | 5 | Corporate-actions table + diff log, crawl step 3 | after the M0 spike; first build |
| F-013 | 1 | Daily bar on each press: acceptance + missed-press case | parallel (BE) |
| F-033 | 1 | No-broker audit test | parallel, any time |
| S05-RW | 2 | OBS-7 768 top bar, 768/800 shots, header ≤ 2 lines, DCA one shift line | parallel (FE) |
| F-015 | 5 | Adjustment factors, adjusted series, reconstructed nominal (A18-A) | after F-014's table (money math) |
| F-023 | 2 | `data_snapshot` = max fetched-at of inputs, reproducibility test, /health `rules_version` | after F-014 (CA fetched-at is an input) |
| F-016 | 3 | Reconciliation vs source, VN30 30/30, `crawl recon` CLI | after F-015 |
| **Total** | **19** | | |

Acceptance criteria and worked examples: `product/backlog.md` (F-015: cash 0.98, bonus 10/13 → 71,923.08, rights
10:2 at 10,000 → 43,333.33; reconstructed 49,000 / 0.98 = 50,000; F-016: 0.204 % listed, 0.041 % not).
Decision time: F-014 = `publicDate` (stored for R2 look-ahead tests); F-015 retroactive by design, charts only;
F-013, F-016, F-023, F-033 n/a.

## UX
- `ux/app-shell.md` §Crawl button: steps 1/3–3/3 ("Bước 3/3 — sự kiện quyền: 18/40 mã"), done line "+3 sự kiện quyền
  (1 thay đổi)", "· 12 mã chờ lượt sau" for deferred names.
- `ux/visual-design.md` §4 (768–1023 px one-line bar), §6.3 (DCA single shift line + "Xem"), §6.4 (headers ≤ 2 lines),
  §9.1/§9.2 (768×1024 and 800×900 light shots of screens a and f + checklist lines).
- Screenshot DoD (retro S04 R1) applies to F-014's UI part and S05-RW. Tester copies `4-test.*.md` and `shots/` into
  FI_ROOT's SPRINT_DIR (retro S04 R5, sa updates `tester.md`).

## Milestones

| Id | Name | Due (VN time) | Owner |
|---|---|---|---|
| M0 | Spike V5 + S2 block behaviour and V5 fields recorded in data.md §1.2 | 2026-10-27 10:00 | sa / dev |
| L1 | Press after 15:00; confirm 27/10 tick manifest + SSI board bar + `crawl_runs` row | 2026-10-27 23:00 | sm |
| M1 | F-013, F-014 (table + step 3), F-033, S05-RW merged | 2026-10-28 12:00 | — |
| L2 | Press after 15:00 with step 3 live; confirm 28/10 manifest, board bar, VN30 `corporate_actions` rows | 2026-10-28 23:00 | sm |
| M2 | F-015, F-016, F-023 merged; VN30 recon 30/30 | 2026-10-29 12:00 | — |
| L3 | Press after 15:00; confirm 29/10 manifest + a recon run before review | 2026-10-29 16:30 | sm |
| M3 | Tests + screenshots (incl. 768/800), review, merge | 2026-10-29 18:00 | — |

**Clock milestones (retro S01 R5, A23: no timer).** KBS ticks and the SSI board serve **the current session only**
(data.md §1.2 K1, S1). sm reminds the sponsor at 15:00 on each trading day. **Lost if missed:** that day's tick tape and
its observed nominal bar, for good (the bar is later filled from V2 as source-adjusted → `reconstructed`). L2 is also the
live acceptance of F-013/F-014; missed → it moves to L3 and review keeps F-014 at risk. Today's 26/10 press is
sprint-04's L1 (due 23:00 tonight).

## Risks
1. **V5 block budget unknown.** If it is as small as V2 (~60 calls), full-market corporate actions take many presses.
   Response: VN30 + saved-scenario symbols first (enough for F-015/F-016 acceptance); the rest drains, counted on screen.
2. **V5 lacks pay-date / cash fields** (data.md §5): parse `eventTitleVi`; unparsed → NULL + anomaly, never guessed.
3. **Short observed-nominal overlap** (crawl start mid-Oct): reconciliation on observed days covers ~2 weeks; earlier dates
   are self-consistency only (data.md §1.4 (3)). Not a fail; stated in the run report.
4. **S2 block behaviour unknown** (30 calls for VN30): covered by M0; if S2 blocks, F-016's S2 cross-check slips (first to slip).
5. **Sponsor presses on 3 days** (L1–L3); a missed day loses that tape (does not block the goal except L2 → L3).
6. Money math in F-015 (factors, rights rule) — `Effort: high`, `Lead: opus`; golden cases above to 0.01 VND.
7. Open sponsor item **A24-D1** (size stop counts tests?) — until answered, production + tests count.

## Sponsor questions
None new. **A24-D1** stays open (SM recommendation: keep counting tests, exclude i18n catalogues). Next free label: **A26**.
