# 3-pr AI-whatif-lumpsum

## Round 1 — CHANGES_REQUIRED (lead BE, 2026-10-18)
Reviewed head H = `8e8446af81368a8bdfbadbd33310cc3d53c5c68f` (task branch synced with origin/sprint-03 @ 5f90edc, clean
merge, pushed).
Files reviewed: `sim/{__init__,dates,whatif,figures}.py`, `tests/test_golden.py`, `tests/test_whatif_lumpsum.py`,
`tests/golden/sim/001..004*.json`, `services/analytics/pyproject.toml` (+ `finvest-rules` workspace dep; implied by the
plan's `rules=finvest_rules.costs`), `uv.lock` (lock only). File set = plan block + the two listed outside-set edits.

### Size
`--shortstat` = 12 files, +606 / -2; excluding `uv.lock` +600 vs plan ~250 (1.5x = 375) = **2.4x**. Production code only
(sim/*.py + pyproject) = +344 (1.38x). The plan's Size covers the whole file set (tests + golden JSON are in it), and no
`3-consult.AI-whatif-lumpsum.md` exists; the build report lists the overrun as deviation 5 instead of stopping.

### Must-fix
1. **Size stop skipped** (lead.md §3, retro S01 R2). Write `SPRINT_DIR/3-consult.AI-whatif-lumpsum.md` for the AI
   architect: actual size (+600 incl. tests/golden, +344 code), why (figures.py `how` boilerplate, golden runner), and the
   ask: accept as is, or split (e.g. golden runner / figures to a follow-up). No code split unless the architect asks.
   Proof: the consult file exists (and its answer) before the next review round.
2. **`whatif.py:90-92` — buy day without a bar returns `NO_DATA {"missing_bar": ...}`**, which contradicts contracts
   §2.1 (`NO_DATA` = "no bar on/after `buy_date`", details `first_available`). Repro: fixture with the 2026-10-12 bar
   dropped, buy 2026-10-12 -> `NO_DATA {'missing_bar': '2026-10-12'}` although bars exist from 10-13. Fix in the shared
   date code, symmetric to your sell handling (`dates.py:37-41`): move N forward to the first bar >= the shifted day
   (shift row `{"field": "buy_date", ..., "reason": "no_bar"}`, `fill_shifted`), still reading with `as_of = N`.
   Proof: a test in `test_whatif_lumpsum.py` (drop 2026-10-12, buy 2026-10-12 -> `dates.buy == "2026-10-13"`, shift
   reason `no_bar`, `fill_shifted` in flags, qty 100) that fails on H.

### Accepted deviations (from 3-build)
- D1 row-level `how` on `contributions[]` (additive, cite VN§5); D2 `result.details.min_amount` as a Figure; D3 shift
  reason `no_bar` (additive); D6 Pydantic `Literal` + in-function guard for `fill_rule`.
- Equity curve over trading days: contract §2.4 says "every trading day"; the plan's "every calendar day" loses to it.

### Nits (optional)
- `whatif.py:78` reads the whole history `bars_1d(first..snapshot)` only to find the last bar date; on the SQL view this
  is a 20-year read per request. A `last_bar_date` port method (like `first_bar_date`) belongs to N1/BE (SA follow-up).
- `whatif.py:86-87` `VALIDATION no_trading_day_near_buy` vs contract `NOT_TRADING_DAY`; unreachable after the last-bar
  check, so fine, but a one-line comment would say so.
- A sell date after the snapshot is accepted and shifted back with reason `no_bar` (probe: 2026-12-31 -> 2026-10-15). OK
  per "sell_date default = last trading day with data", just noting it for the UX copy.

### Follow-up (AI architect, not in this plan)
- D4: `rules_unverified:<rule_id>` flags (contracts §1.3, C7) are not emitted; `finvest_rules.Rule` has `verified`, but
  `costs()` returns values only. Needs a plan line in a later task.

### Correctness (hand check)
python Decimal: liquidation 10,000,000 - 9,350,000 - 14,025 + 10,000,000 - 15,000 - 10,000 = 10,610,975; pl_pct =
6.10975 -> 6.1098 (half-up); CAGR 730 d = 1.0610975^0.5 - 1 = 3.00959 % -> 3.0096. All match golden 001/004 and
contracts §2.4. No look-ahead: buy reads `as_of=N` only; the one wider read (`whatif.py:78`) feeds validation only;
`test_no_look_ahead` (x1.3 after N) keeps contributions/position identical. Money in int VND / Decimal; costs via
`finvest_rules` (VN§4/VN§5). No secrets, no network, no SQL.

### Checks on H
- `make test-kernel` (q.sh): exit 0, 161 passed / 19 deselected, ruff clean, mypy ok, import-linter 5 kept / 0 broken.
- `uv run pytest services/analytics -q`: 16 passed.

## Round 2 — ESCALATE to AI architect (size-stop consult unanswered); code otherwise APPROVE-ready (lead BE, 2026-10-18)
Reviewed head H = `36f9dbafa5b2ed7c0eaf4a8f4d0fa6ba358b1214` (fix 5e2e171 + clean merge of origin/sprint-03 @ ae11587
BE-scenarios-api, touches apps/api only; pushed).
Files reviewed (delta since round 1 H 8e8446a): `sim/whatif.py`, `tests/test_whatif_lumpsum.py`. Rest unchanged from round 1.

### Round-1 must-fix status
1. Size stop: `3-consult.AI-whatif-lumpsum.md` now exists (recommends A, accept as is), but
   `3-consult.AI-whatif-lumpsum.answer.1.md` does **not**. Round 1 required the answer before this round. The size
   decision is the plan owner's (AI architect), not the lead's -> ESCALATE (owner: ai). Size now `--shortstat` 12 files
   +619 / -2 (excl. uv.lock ~+613 vs ~250, 2.45x; code-only ~+350).
2. Buy day without a bar: FIXED. `whatif.py:48-53` moves N to the first stored bar >= the calendar-shifted day (shift
   `no_bar`, `fill_shifted`), then reads the buy with `as_of = N` (new N), so the removed `buy_bars` empty guard is
   unreachable (n_bar is a stored bar date <= snapshot). `NO_DATA {last_available}` branch is unreachable in practice
   (buy <= last bar is checked above), harmless. Choosing N from bar existence (not prices) after the request date is not
   look-ahead. Proof: `test_buy_day_without_bar_moves_forward` fails on round-1 whatif.py (verified: 1 failed), passes on H.

### Must-fix
None in code. Only open item: architect answer to the size consult.

### Checks on H
- `make test-kernel` (q.sh): exit 0, 165 passed / 20 deselected, ruff clean, mypy ok, import-linter all KEPT.
- `uv run pytest services/analytics -q`: 17 passed.

### Next
If the architect answers A (accept): next lead round can APPROVE and merge H as is (no dev round). If B (split): dev
round per the answer.

## Round 3 — APPROVE (lead BE, 2026-10-18)
Reviewed head H = `36f9dbafa5b2ed7c0eaf4a8f4d0fa6ba358b1214` (sync with origin/sprint-03 @ ae11587: already up to date;
no code change since round 2).
Files reviewed: `sim/whatif.py`, `sim/dates.py` re-read on H (money path + date shifts); rest unchanged from round 1/2.

### Round-2 open item
- Size stop: answered **A, accept as is** in `3-consult.AI-whatif-lumpsum.answer.ai.md`; plan block Size updated to ~600
  (`2-tech-plan.ai.md`). `--shortstat` 12 files +619 / -2 (excl. uv.lock ~+613), within the updated Size. CLOSED.

### Must-fix
None.

### Nits / follow-ups (carried, not blocking)
- `last_bar_date` port method instead of the full-history validation read (`whatif.py:36`) — SA follow-up with N1.
- D4 `rules_unverified:<rule_id>` flags — now a bullet in AI-whatif-dca (architect answer).
- dag.json `AI-whatif-lumpsum.size` -> 613 + `dagRev` bump — software architect (per the consult answer).

### Correctness
Unchanged from round 1 hand check: liquidation 10,610,975; pl_pct 6.1098; CAGR 730 d 3.0096 %. Buy reads `as_of=N`;
valuation reads `as_of=M`; the wide read feeds validation/bar existence only (no look-ahead).

### Checks on H
- `make test-kernel` (q.sh, under fi-test.lock): exit 0, 165 passed / 20 deselected, ruff clean, mypy ok.
- `uv run pytest services/analytics -q`: exit 0, 17 passed.
- Merge: `78e636cc6b5ef72c917df94eebb223a5ef419de4` into sprint-03 (sm.sh merge, base ae11587).
