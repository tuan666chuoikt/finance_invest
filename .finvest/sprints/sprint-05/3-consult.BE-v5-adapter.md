# Consult BE-v5-adapter (size stop, retro S01 R2)

Raised in the fix round after tech-lead review (3-pr.BE-v5-adapter.md, must-fix 1). Head f223cc5.

## Question
`git diff origin/sprint-05...HEAD` = 258 lines added (257 excluding the 1-line fixture) vs plan ~150, stop at 225 (1.5x).
Waive the overage, or trim tests?

## Breakdown
- Source: events.py 95 + payloads.py 30 + models.py 19 = 144 lines (on the estimate).
- Tests: test_adapter_vci_events.py 113 lines, 8 cases. Every acceptance line has one:
  fixture -> 4 rows; 15% title -> 20:3 and neither -> NULL + anomaly; rights price forms (10,000 / 10.000 / 15000 / unparsed);
  unmapped not stored; invalid-datetime shape error; paging + toDate (run_date+400d) + archive replay; bad page not archived; 418 x3 -> SourceBlocked.
- The overage is entirely the test file (shared httpx MockTransport harness `make()` ~15 lines, `ev()`/`page()` helpers ~12 lines).

## Options
A. Waive: source is on estimate, tests map 1:1 to acceptance criteria. No code change.
B. Trim tests under 225 total (need -33 lines): drop `test_bad_page_is_not_archived` (11) and `test_invalid_datetime_body_is_a_shape_error` (4)
   and merge/shorten rights cases. Loses two acceptance proofs.

## Recommendation
A (waive). Architect to answer in `3-consult.BE-v5-adapter.answer.1.md` ("waive" or "trim"). No further code change is pending.
