## Round 1 - APPROVE (head dd54436d68a5eb15955922da0db39b9ef96af5d7)
Files reviewed: ratelimit.py, archive.py, fetch.py, test_fetch.py, test_archive.py (239 lines vs ~210 est, within 1.5x). No conflicts with origin/sprint-01.
Must-fix: none. Contract: backoff [1,2], SourceBlocked after 3 consecutive, 5xx/timeout max 3, allow-list before call, archive bytes exact, UA header, per-source buckets: all match task card and each has a test.
Nits: Archive name is not sanitised (callers are internal; fine); Fetcher.sleep separate from bucket sleep (documented).
Checks: make test-kernel exit 0, 14 passed, ruff ok, mypy ok, lint-imports ok.
Merged into sprint-01: cf49a8e850f195a24a7bb0fe4af70132cb8741ea
