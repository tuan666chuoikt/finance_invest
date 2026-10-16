# BE-fetcher build
Result: DONE. TokenBucket, Archive, Fetcher (backoff 1/2/4 s, SourceBlocked after 3 consecutive 429/403/HTML challenge, 5xx/timeout max 3 tries -> httpx.HTTPError, archive-as-cache, host allow-list, UA from caller).
Files: services/crawler/finvest_crawler/{ratelimit,archive,fetch}.py, tests/test_fetch.py, tests/test_archive.py.
Contract: data.md 1.2 rate policy, ADR-S-008 (archive as cache), codebase.md 5 allow-list.
Checks: `make test-kernel` exit 0: 14 passed, ruff ok, mypy ok, lint-imports 3 kept.
Deviations: with 3 blocked tries the sleeps are [1, 2] (no sleep after the last); `Fetcher.sleep` is separate from the bucket sleep. Timeouts are retried like 5xx. 4xx other than 403/429 raise httpx.HTTPStatusError, not archived.
Outside-set edits: none.
Notes for tester: the manifest file is `_manifest.json` beside the date's payloads; Fetcher does not read Settings itself (caller passes user_agent and buckets built from Settings.rate_per_s).
