# ADR-S-003 — Backend: Python 3.12, FastAPI, SQLAlchemy Core + psycopg 3, Alembic, uv workspace
Status: Accepted · 2026-10-15

## Decision
One uv workspace with five packages (codebase.md §1). FastAPI + Pydantic v2 give OpenAPI → generated TS types
(contract spine). SQLAlchemy **Core** (not ORM) for explicit upserts and Timescale DDL; psycopg 3 binary; Alembic
migrations owned by `apps/api`. Analytics runs in-process in the API (single user, N2/N3 are CPU-bound; a separate
service would only add latency). Crawler is a CLI in the same workspace, run as one-shot containers.

## Alternatives
Django (heavier, ORM-centric), Node/TS backend (loses pandas/numpy for analytics), separate analytics service (no
need at one user).

## Consequences
One lock file to audit (F-032), one test runner, shared domain types between crawler, API and analytics.
