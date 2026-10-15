# ADR-S-001 — Storage: PostgreSQL 16 + TimescaleDB for every tier
Status: Accepted · 2026-10-15 · Owner: fi-software-architect

## Context
Tiers: ticks (~2–3 M rows/day, keep forever, A12), 1m bars, daily bars, corporate actions, reference tables, run
manifests, results. One machine, docker available, zero budget. Queries: idempotent upserts by natural key, range
scans per symbol, gap/coverage scans over calendar × sessions, later 1m-from-ticks aggregation.

## Decision
One PostgreSQL 16 database with the TimescaleDB extension (image `timescale/timescaledb:2.17-pg16`, Apache 2 +
Timescale Community licence, free self-hosted). `ticks` and `bars_1m` are hypertables with native compression
(segment by symbol, order by ts; compress after 1 day / 7 days). Everything else is plain tables in the same DB.
Raw payloads are gzip files on disk (data.md §2), not rows. Data directory bind-mounted at `finance_invest/data/pg`.

## Alternatives
- Parquet files + DuckDB: cheapest to write, but no upsert/idempotence story, no realtime reads, two query engines.
- Plain PostgreSQL with declarative partitioning: viable fallback (same DDL minus hypertable calls) if Timescale ever
  blocks an upgrade; ~10× more disk for ticks.
- ClickHouse/QuestDB: faster scans we do not need; second engine for money tables.

## Consequences
Single backup unit, single SQL dialect, continuous aggregates available for 1m-from-ticks (F-067). Extension
upgrades follow the image tag; migrations via Alembic.
