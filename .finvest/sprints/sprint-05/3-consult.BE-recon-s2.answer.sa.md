# Answer BE-recon-s2 consult — fi-software-architect, 2026-10-26

**Decision: option 1, done by the BE-recon-s2 dev (sponsor not needed).** S2 is thousand VND with 2 decimals = 10 VND
resolution; the fixture is the proof (`ssi/history/FPT-1d.json.gz` 2026-09-18 `c` = 65.18 → 65,180 vs V2 65,182). The
acceptance line claiming "S2 close equals V2 65,182.47" was wrong (data.md §1.4 said the same; both fixed). Option 2 rejected:
the rule would live in two places and `diff_pct`/`note`/`exact_days` would still come out wrong. Option 3 rejected: a cross-check
that is mostly noise is no cross-check.

## Rule (data.md v1.6 §1.4 (4) last paragraph; the AI architect may refine the wording in their answer)
- `reconcile(..., slack_vnd: Decimal = Decimal(0))`; `diff <= slack_vnd` counts as equal in **every** branch: reconstructed
  `diff > max(1, slack_vnd)`, G = 1 `diff > slack_vnd`, and `exact_days += diff <= slack_vnd`. Default 0 → every existing
  AI-recon-rules test stays byte-identical. The 0.1 % branch is untouched (10 VND on a VN30 price is < 0.02 %).
- BE passes `slack_vnd=Decimal(10)` for `ssi` only; V2 stays exact (it is the primary check; S2 is the cross-check).
- Note: on the fixture, 2026-09-18 is a **pre-crawl** date → the reconstructed branch (≤ 1 VND) hits first, not G = 1;
  that is why the slack must apply to both branches, not only G = 1 as option 1 was phrased.
- Known limit, accepted: at prices < 10,000 VND (tick 10) a one-tick adapter slip on S2 equals the slack and is masked there —
  V2 exact still catches it; VN30 names are far above 10,000.

## Who does what (plan v1.2, dag rev 5)
- **BE-recon-s2 file set += `services/analytics/finvest_analytics/adjust/recon.py`, `services/analytics/tests/test_recon.py`**
  (only the keyword above; AI-recon-rules is merged, no overlap). Size ~90 → ~120. No new task.
- Acceptance rewritten: S2 row for FPT 2026-09-18 lands as 65,180; 0 mismatches at slack 10, 1 `unit_or_adapter` at the
  default 0 (one analytics test covering both branches); 11 VND at slack 10 is still a mismatch; 418 keeps the local summary.

## Documents updated (old copies archived)
- `architecture/data.md` v1.6 (`data.prev-6.md`): §1.2 S2 resolution + fixture cite; §1.4 lead sentence corrected; §1.4 (4) slack rule.
- `2-tech-plan.md` v1.2 (`2-tech-plan.prev-3.md`): BE-recon-s2 files, change, contract, acceptance, size.
- `dag.json` rev 5 (`dag.prev-3.json`): BE-recon-s2 size 120, `_doc.dagRev5`.
