# ADR-S-008 — Ticks: natural key (symbol, ts, seq) with seq = accumulated volume; raw archive + per-session manifest
Status: Accepted · 2026-10-15

## Context
KBS returns the whole session per symbol with `t` at centisecond precision, no trade id, and the accumulated
volume after each trade (`AVO`), which is strictly increasing within the day. VCI has an `id` but serves 100 rows
per call. Re-runs must be byte-idempotent (F-017) and absence must be recorded, not inferred (G1).

## Decision
`ticks PK (symbol, ts, seq)`, `seq` = KBS accumulated volume (or VCI id when the source is VCI; the `source`
column disambiguates). Rows with the same key and a different price are upserted (newest `fetched_at` wins) and
logged as `duplicate_tick` anomalies. Each session writes `data/raw/ticks/<date>/<SYMBOL>.json.gz` (exact bytes)
plus `_manifest.json` (platform.md §4) with a sha256 over the canonical normalised rows; `crawl_sessions`
mirrors it. A skipped symbol or missed session is a manifest entry with a reason; the gap list is a table read.
The raw archive doubles as the cache: a re-run for a date first replays archived payloads and only fetches what
is missing.

## Consequences
Re-crawl = same rows, same checksum. If KBS ever stops exposing AVO, seq falls back to row order within equal `ts`
(documented shortcut, requires a one-off migration).
