# Consult BE-ca-recompute (fix round 1, late, answers already given) — fi-be-dev, 2026-10-26

Must-fix 1 of `3-pr.BE-ca-recompute.md`: I missed the size stop in round 1 and found it only at the end.

- **Why it grew:** plan ~170 counted source only. Round 1 = 296 lines (src 150, tests 144 + test_jobs): OHLC reconstruction, the finder for the
  culprit ex-date of an `InvalidCorporateAction`, anomaly dedupe, 5 db tests.
- **Re-estimate (now):** ~356 lines excl. lockfile after fix round 1 (per-version `last`, watermark set, queries moved to `repositories.py`,
  reason with skipped count, 4 new db tests). SA's card says ~340; 1.5x = 510. Nothing left to split.
- Items 2, 3, 4 and nits a-d were already decided in `3-consult.BE-ca-recompute.answer.{ai,sa}.md`; this round implements them. No open question.
