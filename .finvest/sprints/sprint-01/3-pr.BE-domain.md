# PR BE-domain (task/sprint-01/BE-domain -> sprint-01), lead: BE (opus)

## Round 1 - APPROVE (head 65b7ae71b602d702715ab6d90c36ad66faffce17)
Synced with origin/sprint-01 (cf49a8e, BE-fetcher) by a clean merge commit, no conflicts.
Files reviewed: domain/models.py, ports.py, units.py, manifest.py, tests/test_units.py, tests/test_manifest.py.
Size: 191 production + 83 test = 274 lines vs ~170 est (1.6x total, 1.1x production only); excess is tests; no consult needed.
Must-fix: none.
Contract check:
- platform.md §1.2 / ADR-S-005: prices int VND; to_vnd Decimal ROUND_HALF_UP; card examples 93500, 65182, 65183, to_shares 100 all tested.
- platform.md §4: canonical line symbol,ts,seq,price,volume,side with ts %Y-%m-%dT%H:%M:%S.%f+00:00, side empty when null; lines sorted bytewise with trailing \n (sorting line+"\n" equals sorting lines for these printable rows). Test computes sha256 independently and checks order invariance. Manifest.to_dict emits exactly the 13 §4 keys in order, started_at/finished_at/universe.as_of as +07:00 (example 15:20:03+07:00 reproduced).
- ADR-S-006: Tick/Bar reject naive and non-zero-offset ts (tested, incl. +07:00).
- ADR-S-008: dedupe keeps last row per (symbol, ts, seq), returns displaced (tested 3 -> 2 kept, 1 displaced).
- codebase.md §3: port is the S01 subset (name, symbols, ticks, bars) with matching signatures; SourceError/Unsupported/SourceNoLongerServes/PayloadShapeError(raw_path); SourceBlocked not here.
Layering: domain is pure (stdlib only); lint-imports 3 kept, 0 broken.
Nits (no action required):
1. units.py:8 docstring says floats are rejected, but Decimal(float) accepts them at runtime; only mypy rejects. Fine for typed callers.
2. manifest.py:49 Manifest.status is str; a Literal of the five §4 states would let mypy catch typos.
3. Bar validation (prices > 0, v >= 0, UTC ts) is beyond the card but same rule as Tick; accepted.
Checks (synced head): make test-kernel exit 0: 22 passed, ruff ok, mypy strict ok (5 files), lint-imports 3 kept.
Merged into sprint-01: bfe14bc3cd40ca55751a1bf456ea920f1ff8fc39
