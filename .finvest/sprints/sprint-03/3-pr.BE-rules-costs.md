# 3-pr BE-rules-costs (F-006)

## Round 1 — CHANGES_REQUIRED (lead BE, 2026-10-18)

Reviewed head H = 825c2cf186cc3f1e104a9655f04c9e76277a5b01 (already contains origin/sprint-03 f4f4986; no sync commit needed).
Size: 3 files, +111 / -1 (plan ~90; 1.5x = 135) — within limit.

Files reviewed: `packages/market_rules/finvest_rules/costs.py`, `packages/market_rules/finvest_rules/__init__.py`,
`packages/market_rules/tests/test_costs.py`. File set matches the plan block exactly.

### What is right
- Values match VN§4/VN§5 and the plan: buy/sell fee 0.0015 (A6, verified=False), sell tax 0.001 (verified 2026-10-15,
  Law 109/2025/QH15 + Decree 253/2026), board lot 100 (VN§4), T+2 (VN§5). Decimal for rates, int for counts (ADR-S-005).
- `effective_from = 2006-01-01` with the apply-from docstring; `rule()` picks latest `effective_from <= on` via bisect,
  raises `RuleNotEffective` before the first entry. `RULES_VERSION = "2026.10.16"`.
- Acceptance tests cover all three criteria. Checked by hand: changing buy_fee_rate to 0.0016 moves the hash
  2019ac0ca54a268d -> 21c1c9399e04f0ff, so the bump test fails as required. `rule()` on 2006-01-01 (boundary) -> 100.
- Layering: `finvest_rules imports nothing of ours` KEPT. No secrets, no SQL, no network.
- `rule(..., rules=)` optional arg deviation: accepted (keeps the plan signature, avoids mutating the global).

### Must-fix
1. `packages/market_rules/finvest_rules/costs.py:69-72` — `costs()` fails `mypy --strict`, which codebase.md §4
   requires for `finvest_rules` (6 errors: untyped lambda call `[no-untyped-call]`, and `Decimal | int` passed to
   `Costs` fields typed `Decimal` / `int` `[arg-type]`). This is a real soundness gap: a rule entered with the wrong
   type (e.g. an int fee or a Decimal lot) would land in `Costs` unchecked. Replace the lambda with two typed helpers
   (e.g. `_rate(name, on) -> Decimal` and `_count(name, on) -> int`) that narrow with `isinstance` and raise `TypeError`
   on a wrong type. Proof: `uv run mypy --strict packages/market_rules/finvest_rules` exit 0, plus one test in
   `test_costs.py` that a wrongly typed entry (test-local rules) raises `TypeError` — this needs `costs()` to accept the
   same optional `rules` arg as `rule()` (pass it through).

### Nits (optional)
- `costs.py:63` `(rules or RULES)`: an empty dict silently falls back to the global RULES; prefer
  `RULES if rules is None else rules`.
- The package `__init__` exports function `costs`, which shadows submodule `finvest_rules.costs` as a package
  attribute (`from finvest_rules import costs` gives the function; `import finvest_rules.costs as m` too). Names come
  from the plan, so no change required; import the module with `from finvest_rules.costs import ...`.

### Follow-up (not this task; for SA)
- `pyproject.toml [tool.mypy] files` lists only `finvest_market_data/domain`, so the kernel's `uv run mypy` does not
  check `finvest_rules` even though codebase.md §4 says it is strict. That is why the build report showed mypy green.
  Add `packages/market_rules/finvest_rules` to `files` in a task whose file set includes `pyproject.toml`.

### Checks on H
- `make test-kernel` (q.sh): exit 0 — 133 passed, 18 deselected; ruff check all passed; mypy (configured scope)
  no issues in 5 files; import-linter 4 kept, 0 broken.
- `ruff format --check packages/market_rules`: 5 files already formatted.
- `uv run mypy --strict packages/market_rules/finvest_rules`: exit 1, 6 errors, all in costs.py:71 (calendar.py clean).
- No `-m db` run needed (no migrations, repositories or SQL).

## Round 2 — APPROVE (lead BE, 2026-10-18)

Reviewed head H = dbb2f6a4f5a98af0eb90a7c5d8d5792c9ae6c8f1 (= fix 5bf7f6c + `chore(merge)` sync of origin/sprint-03 bef00de;
clean merge, no conflicts: S-etf-bars / FE-web-scaffold / analytics scaffold touch no file of this task).

Files reviewed: `packages/market_rules/finvest_rules/costs.py`, `packages/market_rules/finvest_rules/__init__.py`,
`packages/market_rules/tests/test_costs.py`. File set = plan block.

### Round-1 must-fix
1. FIXED — `costs.py:68-89`: typed `_rate`/`_count` helpers narrow with `isinstance` (bool rejected for counts) and raise
   `TypeError`; `costs(on, rules=None)` passes `rules` through. Proof: `test_wrong_type_entry_raises` (Decimal lot, int fee)
   and `mypy --strict packages/market_rules/finvest_rules` exit 0. Nit `RULES if rules is None else rules` applied too.

### Size stop
`--shortstat` = 3 files, +139 / -1 vs plan ~90 (1.5x = 135): 4 lines over, no `3-consult`. Waived by the lead: round 1 was
+111 (within limit) and the +28 are the round-1 must-fix this lead asked for (helpers + test), not scope growth. Recorded
so the retro sees it; no new behaviour beyond the plan.

### Contract
`RULES_VERSION = "2026.10.16"` is a string in the `YYYY.MM.DD` form of contracts/analytics.md (`rules_version`); cites
`VN§5` on costs and `VN§4` on lots as contracts/analytics.md line 124 requires. Values unchanged from round 1 (hash
`2019ac0ca54a268d` still matches).

### Must-fix
None.

### Nits (optional, carry forward)
- `__init__` export `costs` shadows submodule `finvest_rules.costs` (from round 1; names from the plan).

### Follow-up (SA, unchanged from round 1)
- `pyproject.toml [tool.mypy] files` still excludes `packages/market_rules/finvest_rules`; kernel mypy does not enforce
  codebase.md §4 strictness there. Add it in a task that owns `pyproject.toml`.

### Checks on H
- `make test-kernel` (q.sh, under fi-test.lock): exit 0 — 143 passed, 18 deselected, 1 warning (starlette httpx
  deprecation, unrelated); ruff check all passed; mypy (configured scope) no issues in 5 files; import-linter 5 kept,
  0 broken (incl. "finvest_rules imports nothing of ours").
- `uv run mypy --strict packages/market_rules/finvest_rules`: exit 0, 3 files.
- `uv run pytest packages/market_rules/tests/test_costs.py`: 5 passed. `ruff format --check packages/market_rules`: 5 files formatted.
- No `-m db` needed (no migrations, repositories or SQL).

### Merge
Merged by `sm.sh merge`: base ae3b4a1 (origin/sprint-03 had gained FE-disclaimer, 3 apps/web files, after the sync)
+ head dbb2f6a -> merge **36f6c0eedce07c10717409e5b436c0a322c6c857**, pushed to sprint-03. Post-merge `make test-kernel`
on 36f6c0e: exit 0, 143 passed, 18 deselected. Worktree removed.
