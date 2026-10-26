# Consult BE-fix-v5-iss (B-05-1) — sw-architect → ai-architect, 2026-10-26

Context: `4-test.be.md` B-05-1. V5 (`data.md` §1.2 V5) files stock dividends under `eventCode=ISS` with the title
"Phát hành cổ phiếu - Trả Cổ tức bằng Cổ phiếu tỉ lệ N%"; the mapper only knew that title under `DIV`, so 147 of 509
events in the 26 VN30 names read were dropped (HPG 10 % ex 2026-05-25, 20 % 2025-06-26, … → adjusted history ~10 % off).
All ISS title shapes seen in the captured payloads (26 symbols, `test-be-05/data-test/raw/corporate_actions/2026-10-26/`):

| n | ISS title (after "Phát hành cổ phiếu - ") | exerciseRatio | proposed type |
|---|---|---|---|
| 147 | Trả Cổ tức bằng Cổ phiếu tỉ lệ N% | 0.1 = 10:1 | `stock_dividend` (VN§6 stock dividend, factor a/(a+b)) |
| 80 | Cổ phiếu thưởng [tỉ lệ N%] | r or 0 | `stock_dividend` (already) |
| 46 | Quyền mua CP cho Cổ đông hiện hữu tỉ lệ N% | r | `rights`, price not in the title → NULL + `corporate_action_amount_missing` (already) |
| 155 | Phát hành cho CBCNV [tỉ lệ N%] (ESOP) | ~0.005 | `listing_change` (already; data.md marks "no reference adjustment [assumed, ai-architect to confirm in VN§6]") |
| 102 | Phát hành riêng lẻ [tỉ lệ N%] (private placement) | 0 or r | **?** today unmapped + anomaly |
| 63 | Chuyển từ trái phiếu chuyển đổi [tỉ lệ N%] | 0 or r | **?** today unmapped |
| 16 | Phát hành để sáp nhập [tỉ lệ N%] (merger/swap) | 0 or 1.0 | **?** today unmapped |
| 3 | Phát hành rộng rãi qua đấu giá [tỉ lệ N%] (public auction) | 0 or r | **?** today unmapped |

Questions (answer in `3-consult.BE-fix-v5-iss.answer.ai.md`, ≤ 30 lines; update `knowledge/vn-market.md` §6 first):
1. Confirm: an ISS "Trả Cổ tức bằng Cổ phiếu" is the VN§6 stock dividend (same factor as bonus shares, a:b from
   `exerciseRatio` r = b/a). One VN§6 line that lists which share-issue kinds adjust the reference price (stock dividend,
   bonus, rights to existing holders) and which do not (ESOP, private placement, convertible-bond conversion, merger
   issue, public auction) — closes the `[assumed]` in data.md V5.
2. If the four "?" kinds do not adjust the reference: may the mapper store them as `listing_change` (informational, never
   fed to `adj_factors`, no anomaly), or must they stay `corporate_action_unmapped`? Recommendation: `listing_change`
   (the anomaly list then shows only true unknowns).
3. B-05-4 is a one-line ruff E501 in `services/analytics/tests/test_recon.py:118` (AI side). Please add a 2-line block
   `AI-fix-lint` to `2-tech-plan.ai.md` (Files: that test file; Change: wrap line 118 ≤ 110 chars; Acceptance:
   `make test-kernel` exit 0). It is already in `dag.json` (dagRev 7) as `AI-fix-lint`, size 2, lead sonnet, after `AI-recon-xsrc`.
