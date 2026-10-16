
## Fix round 1
- Must-fix 1: `catchup.start = last or today` (last day is retried when partial/blocked/failed; skipped when complete/missed). Tests: last-day blocked reruns, last-day complete runs nothing; Repo fake now returns a row for `last` like a real repo; `test_complete_and_missed_skipped_others_run` uses last=10-15.
- Nits done: redundant `import pytest` removed, README stale F-019 wording, README note about `make up` rebuild. Skipped: conn.commit nit.
- Checks: make test-kernel green.
