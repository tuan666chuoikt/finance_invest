# Answer BE-recon-s2 consult (AI side) — fi-ai-architect, 2026-10-26

**Decision: none of options 1–3. No VND slack; the exact rule at `G = 1` stays. The real cause is a different branch.**

## Why the premise does not hold
- When `G_v = 1` the source row is **nominal**, and a nominal close sits on the tick (VN§3: 10/50/100 đ on HOSE, 100 đ HNX/UPCoM;
  only HNX ETFs tick at 1 đ, not in VN30). S2's 2-decimal thousand VND (10-VND resolution) represents every such close
  **exactly**, so the "1..9 VND rounding gap on every G = 1 day" never happens for stocks. A diff there is still a unit/adapter bug.
- FPT 2026-09-18 has `G_v = 1/1.1` (ex-date 09-21 ≤ S2's `last`): ours = 71,701 × 1/1.1 = **65,182.73** vs S2 **65,180** →
  0.0042 % < 0.1 % — the threshold branch passes it already.
- What actually fires: 09-18 is pre-crawl, `nominal_kind = reconstructed` → the **1-VND self-consistency** branch (R7), which
  is a check against the source the row was *inverted from* (V2), not against a second source. Against S2 it reports
  2.73 > 1 as `self_consistency` — on every pre-ex reconstructed day (noise up to ≈ 5.5 VND). That is the mismatch you saw.

## Rule (tech plan v1.2 R7; `analytics.md` v1.4 §1.3; old copies `2-tech-plan.ai.prev-2.md`, `analytics.prev-4.md`)
Self-consistency only against the origin source; any other `theirs` sees a reconstructed row as an ordinary row
(`G_v = 1` → exact, else 0.1 %).

## Who does what
- New AI task **AI-recon-xsrc** (~30 lines, block in `2-tech-plan.ai.md`; `dag.json` dagRev 5, old copy `dag.prev-3.json`):
  `reconcile(..., self_check: bool = True)`; the reconstructed branch runs only when `self_check`. Default = today's behaviour,
  every existing test unchanged. **BE-recon-s2 now waits on it**; SA, keep that `after` if you re-emit the dag.
- BE-recon-s2 (your file set): `_compare` passes `self_check=(source == "vci")` (V2 is the only reconstruction source, data.md
  §1.4). Tests: the FPT fixture → 0 mismatches on 09-18; a hand-broken S2 close (e.g. 65.28) → `factor_or_event`.
- SA: the acceptance wording "S2 close equals V2 65,182.47" is wrong — S2 gives 65,180; reword to "ours 65,182.73 vs S2
  65,180 = 0.0042 % → 0 mismatches". data.md §1.4 line "V2/S2/B1 all showed 65,182.47" is likewise not what the S2 fixture
  shows (65.18) — your file.

## Risk, stated
A missing ex-date in our factors makes a pre-ex V2 row pass self-consistency by construction (0.47 ≤ 1) but fail vs S2 as
`unit_or_adapter` (65,182 vs 65,180): the label is off, the signal is right and wanted. Sponsor not needed.
