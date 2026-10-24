# 3-consult BE-jobs-crawl (F-034), filed in fix round 1, 2026-10-24

Question 1 (size stop): 438 added lines excluding lock/generated files vs plan ~240 (1.5x = 360). Accept as is (A) or split (B)?
- Production 232 vs 110 planned, tests 166 vs 105 planned. Nothing is left to split: thread body, lock, route, migration and
  tests are one unit. Fix round 1 adds about +50 (blocked handling, running-row guard, 2 tests).
- Recommendation: A, update plan Size to the actual.

Question 2 (contract gaps found while building):
- `summary.bars_1d.sessions_added` is in no manifest; dev computes `COUNT(DISTINCT trading_date)` of `bars_1d_src` after minus
  before. Recommend: contract says so.
- `count` = min of the two TABLE maxima, an empty table ignored. While `index_1d` is empty the job never back-fills indices
  (only `make backfill` does). Recommend: accept, or redefine.
- platform.md §1.3 says 409 `JOB_ALREADY_RUNNING`, §2.6 says `JOB_RUNNING`; code follows §2.6. Recommend: fix §1.3.
