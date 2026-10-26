# Answer BE-v5-adapter consult — fi-software-architect, 2026-10-26

**Decision: waive** (option A). No code change; tech lead may re-review head f223cc5 as is.

## Why
- The estimate was wrong, not the build. `Size` counts production + tests (owner.md), and my ~150 covered only the
  source (144 lines actual, on target). Eight acceptance lines → eight tests (113 lines) is the right ratio; the plan
  should have said ~260.
- Option B would delete two acceptance proofs (`bad page is not archived`, `invalid-datetime body is a shape error`).
  Both guard data correctness: a cached HTTP-200/`status 400` page would replay as "no events" forever for that
  symbol. Trimming tests to satisfy a line counter is the wrong trade; the size stop exists to catch scope creep,
  and there is none here (file set unchanged, no extra features).
- The 1.5x rule still applied correctly as a *stop*: the dev should have written the consult before the push
  (dev.md §3). That process miss is already fixed by this consult; no further action.

## Documents updated
- `2-tech-plan.md` BE-v5-adapter block: `Size: ~260 lines` (old copy in `2-tech-plan.prev-1.md`).
- `dag.json`: BE-v5-adapter `size` 150 → 260, `dagRev` 2 (old copy in `dag.prev-1.json`).
- No contract, data.md or architecture change: mapping, ratio and archive-after-parse behaviour match data.md §1.2 V5 / §3.

## Note for the tech lead
- The 4 silent-card decisions in `3-build.BE-v5-adapter.md` are accepted as-is (they were already judged consistent in round 1).
- Nit to carry to BE-ca-step3's card (already there as "informational"): `listing_change` rows never feed `adj_factors`.
- Sponsor not needed (A24-D1 "count tests in the size stop" stays open; this answer applies the current rule and re-estimates instead).
