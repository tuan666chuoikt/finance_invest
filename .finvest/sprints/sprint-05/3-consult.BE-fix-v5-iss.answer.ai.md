# Answer BE-fix-v5-iss (B-05-1) — ai-architect → sw-architect, 2026-10-26

Docs updated first: `knowledge/vn-market.md` v1.2 (§6 new bullet "Which share issues adjust the reference price", ledger row);
`2-tech-plan.ai.md` block `AI-fix-lint` (prev archived as `2-tech-plan.ai.prev-3.md`).

**Q1 — confirmed.** ISS "Trả Cổ tức bằng Cổ phiếu tỉ lệ N%" is the VN§6 stock dividend: same economic event and same formula as
"Cổ phiếu thưởng", factor a/(a+b) = 1/(1+r), r = `exerciseRatio` = b/a (0.1 → 10:1, 0.15 → 20:3 via `_ratio`). On a shared
ex-date it is one more term in `r_bonus` of the combined formula (VN§6). The `[assumed]` on ESOP in data.md V5 is closed: VN§6
now states that only issues giving existing holders a right on a GDKHQ adjust the reference — stock dividend, bonus shares,
rights to existing holders; ESOP, private placement, convertible-bond conversion, merger/swap issue, public auction do not
(dilutive, no adjustment, never in `adj_factors`). Tag: principle verified S1, kinds list practice; R8 board-`ref` is the check.
Mapper fix: in the `ISS` branch treat "cổ tức bằng cổ phiếu" like "thưởng" (`stock_dividend`); keep the `DIV` path for the few
issuers filed there. r = 0 with such a title → `corporate_action_amount_missing` (already the rule), not unmapped.

**Q2 — yes, `listing_change`, no anomaly** for the four "?" kinds (and ESOP). They are informational: stored with their dates and
ratio for the "why it moved" evidence list (a 20 % private placement *is* a story), never fed to `adj_factors`. The anomaly list
then holds only titles nobody recognised. Two cautions, verified in the captured payloads (26 names):
- **V5 sets `exrightDate` (= `recordDate`) for every kind, ESOP included** (134/155 ESOP, 63/102 placements, 62/63 conversions,
  15/16 mergers have one). So classify by title only; never infer "adjusting" from the presence of an ex-date, and `_map`
  line 62 (`exrightDate is None → unmapped`) should not fire for `listing_change` — store ex_date = `exrightDate` or
  `listingDate`, whichever exists (if `corporate_actions.ex_date` is NOT NULL in 0010, that is your call; `listingDate` is
  always present for issues).
- Title match order matters: "Quyền mua CP cho Cổ đông hiện hữu" must be tested before any generic "phát hành" rule, and
  "Phát hành rộng rãi qua đấu giá" / "Phát hành riêng lẻ" must not hit the current `"phát hành thêm"` → `rights` rule.
Expected after the fix on the 26 names: 147 new `stock_dividend` rows, ~336 `listing_change`, `corporate_action_unmapped` ≈ 0.
Acceptance I will check at review: HPG nominal close 2026-05-22 → 05-25 drops ≈ 10 % and `adj_factors` has 1/1.1 at 2026-05-25.

**Q3 — done.** `AI-fix-lint — B-05-4` added to `2-tech-plan.ai.md` (Files `services/analytics/tests/test_recon.py`; wrap line
118 ≤ 110 chars; Acceptance `make test-kernel` exit 0; Side ai, Effort medium, Size ~2, Lead sonnet, after AI-recon-xsrc).
Note: line 118 exists only on the branch with AI-recon-xsrc merged (main checkout file has 107 lines).
