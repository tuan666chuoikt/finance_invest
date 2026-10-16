# 5-review.tech — Sprint 01 technical review

Reviewer: `fi-software-architect`. Head: origin/sprint-01 `36788eb` (8 BE tasks merged). Inputs: 2-tech-plan v1.0,
3-build.*/3-pr.*, 4-test.be.md (RED), code of `feeds/ticks.py`, `fetch.py`, `archive.py`, `adapters/*`, `cli.py`,
`repositories.py`. Verdict: **FAIL** — 5 PASS / 3 FAIL per task; contracts platform.md §4 and ADR-S-008 FAIL in
the field. Three FIX tasks appended to 2-tech-plan.md (dagRev 2); the sprint goal "ticks collected every evening"
is not met until FIX-feed-past-date and FIX-universe-pinned merge and the M3 live run is repeated.

## Per task

| Task | Verdict | Findings (stage · severity) |
|---|---|---|
| BE-scaffold | PASS | `/health` path fixed in round 2. `cli.py` still swallows `ImportError` broadly — gone with BE-feed-ticks (stub replaced). |
| BE-domain | PASS | Port + checksum + dedupe match platform.md §4 / ADR-S-008. `SourceNoLongerServes(symbol, served_date)` extended by BE-adapter-kbs: accepted. |
| BE-fetcher | FAIL | **F1** (plan · high): `Fetcher.get` archives every 200 body before anyone checks it belongs to `trading_date` — the plan's "archive doubles as cache" assumed payloads are session-specific; K1 is not. Root of QA-BUG-2's 1,186 foreign empty tapes under `ticks/2026-10-15/`. **F2** (build · low): `Archive.path(name)` accepts path separators (QA-BUG-1 second guard). |
| BE-schema | PASS | 410 vs 200 lines without a consult (plan · low: estimate missed the migration + db test weight; lead confirmed no scope creep — accepted, noted for sprint-02 sizing). `fetched_at` contradiction between ADR-S-008/platform.md §4 and data.md §3 resolved in platform.md v1.2: `ticks` has no `fetched_at`, last write wins. Missing: no way to close a killed run (QA-BUG-3b) — fixed by FIX-universe-pinned, not a schema change. |
| BE-adapter-kbs | PASS | Session check correct; `served_date=None` on empty tape is the right signal. The *decision* on an empty tape belongs to the feed (see FIX-feed-past-date). |
| BE-adapter-vci-ssi | FAIL | **F3** (plan · medium): `VciSource.symbols()` archives under *today*, not the feed's `trading_date`; port has no date parameter. Root of QA-BUG-3 (universe drift 1540 vs 1541, manifest 80,272 ≠ DB 80,336). Delisted-symbol handling (keep for survivorship, data.md §1.2 V3 vs card "drop") stays open for F-004 planning (architecture · low, S02). |
| BE-compose | PASS | Shared image + `--build` fixed in round 2. Root-owned `data/` remains (ops nit, F-019). |
| BE-feed-ticks | FAIL | **F4** (plan+build · high): `missed/source_no_longer_serves` fires only when `served_date is not None and not fetched`; on a resumed/late run the probe replays from archive (`fetched>0`) and every later foreign tape is `no_ticks` → `partial` instead of saying the source moved on (QA-BUG-2). The plan's single-probe rule did not cover resume. **F5** (build · low): `--only` values reach the URL path and archive name unvalidated (QA-BUG-1). **F6** (build · medium): unfinished `crawl_runs` row after a kill is never closed (QA-BUG-3b). |

## Per contract

| Contract | Verdict | Note |
|---|---|---|
| platform.md §4 manifest JSON, status/reason enums, checksum line, `universe.source` | PASS (offline) / FAIL (live) | Keys and checksum exact (tests); live 10-15 manifest disagrees with the DB (QA-BUG-3) and misreports the gap (QA-BUG-2). §4 amended to v1.2: archive-only-after-accept, universe keyed by `trading_date`, `partial` + `source_no_longer_serves`, skip-reason list, `interrupted` runs, `fetched_at` wording. |
| platform.md §4 rate limit / `SourceBlocked` / exit non-zero | PASS | Backoff, 3-strike, exit 2, universe-block path all tested. |
| ADR-S-008 archive-first idempotence | FAIL | Idempotence holds on fixtures; on the real source the archive stores non-session data under the session date and replays it forever. Fix is F1 (no ADR change: the rule "archive = cache" stands, with "accepted payloads only"). |
| data.md §3 DDL (ticks hypertable, crawl_*, anomalies) | PASS | Compression policy, CHECK on `side`, PKs verified by db tests. |
| codebase.md §3 layering / §5 kernel | PASS | import-linter kept; mypy covers domain only (crawler untyped — accepted for S01, widen in S02 scaffold). |
| codebase.md §5 guardrails (allow-list, no secrets, free sources) | PASS with F5 | Host allow-list holds; symbol input needs validation at the CLI boundary. |

## Decisions (architecture)
- Empty tape semantics: K1 serves only the current session (data.md §1.2 K1), so **trading_date < today(VN) + empty
  tape = conclusive `source_no_longer_serves`**; today + empty = `no_ticks`. The adapter stays pure (raises with
  `served_date=None`); the feed applies the date rule. No "probe" special case any more.
- Early stop on `source_no_longer_serves`: with fetched > 0 the session is `partial`, reason
  `source_no_longer_serves`, the untouched symbols listed as skipped with that reason (no 1,186 wasted requests).
- Universe is part of the session: archive/replay keyed by `trading_date`; `universe.as_of` = archive file mtime.
- Data already on disk: the tester's `data/raw/ticks/2026-10-15/` holds 1,186 empty tapes. Code never deletes
  (platform.md §4); the sponsor/tester removes files whose gunzipped body is `{"data":[]}` by hand before re-running.
  Ticks of those symbols for 10-15 are lost (C1) — nothing to recover.

## Follow-ups not turned into tasks
- `fetch.py` typed error instead of regex on the message (lead nit) — S02 scaffold cleanup.
- Delisted symbols / `SymbolRecord.exchange` — F-004 plan (S02).
- Sizing: BE-schema 2x estimate; count migration + db-test lines explicitly in S02 estimates.

## FIX tasks (appended to 2-tech-plan.md, dag.json dagRev 2)
- FIX-feed-past-date (high, opus) — F1, F4: archive only accepted tapes; date rule for empty tapes; early stop.
- FIX-universe-pinned (medium, sonnet; after FIX-feed-past-date) — F3, F6: `symbols(as_of)`, `as_of` from archive, close interrupted runs.
- FIX-only-validate (low, sonnet) — F2, F5: `--only` regex at the CLI, `Archive.path` rejects separators.
After the three merge: tester re-runs `make crawl DATE=<today after 15:30>` for the M3 numbers.
