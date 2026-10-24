# 3-pr FIX-symbols-exact-first
## Round 1 — APPROVE (head f9d53798ee903e25984e48811a492252b245add8)
Files reviewed: apps/api/finvest_api/routes/symbols.py, tests/test_symbols.py, tests/conftest.py (12+/4-, within 1.5x of ~30).
Contract platform.md §2.5 v1.7: exact match (case-insensitive) first, then symbol asc; order_by(None) rebuild keeps limit applied after ordering. Dev's Change/Acceptance inconsistency for q=fp resolved correctly (no exact match -> FOC, FPT).
Tests: q=FPT/fpt -> [FPT,FOC], limit=1 -> [FPT]; fail without change (FOC sorts first).
Checks (synced head, already up to date): kernel 207 passed 22 deselected; ruff clean; lint-imports ok; mypy ok. No migrations/SQL repos touched, -m db not required.
Must-fix: none. Nits: none.
Merge sha: a2d6a1c43c00f4eb3e19b47f9ba35020794106cf
