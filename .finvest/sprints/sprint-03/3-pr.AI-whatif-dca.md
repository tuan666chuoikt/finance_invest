# 3-pr AI-whatif-dca (F-057 monthly DCA + D4 rules_unverified)

## Round 1 — CHANGES_REQUIRED (lead BE, opus, 2026-10-18)

Reviewed head H = `95b7fc6` (task branch), base `origin/sprint-03` = `78e636c`. Sync: already up to date, no merge commit.
Files reviewed (whole diff): `sim/dca.py`, `sim/whatif.py`, `sim/figures.py`, `tests/test_whatif_dca.py`,
`tests/test_golden.py`, `tests/test_whatif_lumpsum.py`, golden `005`, `005b`, `006`, `007`.

### Size
`git diff origin/sprint-03...HEAD --shortstat`: 10 files, +382 / -71. Plan block Size ~200 (+~15 for D4 per
`3-consult.AI-whatif-lumpsum.answer.ai.md`) -> 1.5x = 322. Over the stop, and no `3-consult.AI-whatif-dca.md` exists.
The build report's "nothing left to split, so no consult" is the dev deciding the plan owner's question.

### Must-fix
1. **Size stop skipped** (lead.md §3, retro S01 R2). Write `SPRINT_DIR/3-consult.AI-whatif-dca.md` for the AI architect:
   actual +382/-71 (code ~170, tests + golden ~212), why, options (accept as is / split). The lead re-reviews only
   once `3-consult.AI-whatif-dca.answer*.md` exists. Proof: the consult file + answer.
2. **`how.inputs.buy_fee_rate` can misreport per contribution** — `sim/figures.py:53` (`buy_how(r)`) and
   `figures.py:179` (`details.min_amount`) use the single `buy_rate` of `rules(n)` (`whatif.py:143`), while each
   contribution's fee uses `rules(t_i)` (`whatif.py:79-80`) and `min_amount` uses the rate of its own contribution date
   (`whatif.py:100`). With a time-versioned buy fee (the `rules` callable is injectable; `finvest_rules.rule(name, on)` is
   dated) the `how` panel shows a rate that did not produce the number (contracts §1.1/§2.4: `how.inputs` names every
   number in the formula). Fix: carry the rate used in each row (and in the `min_amount` tuple) and print that.
   Test (in `test_whatif_dca.py`): inject a `rules` callable whose `buy_fee_rate` changes between contribution 1 and 2;
   assert each `contributions[i].how.inputs.buy_fee_rate` equals the rate behind `contributions[i].fee_vnd`. Fails today.

### Nits (optional)
- `whatif.py:66`: a contribution whose trading day has no bar up to `m` emits a second `after_end` row after
  `schedule()` already noted its non-trading shift; one row (`from` = requested) would read cleaner for the FE notice.
- `position.shares.how.inputs.buy_fee_rate` (DCA) also shows one rate; fine while the rate is constant, same fix as 2.
- `rules_unverified` reads shipped `finvest_rules.RULES`, not the injected callable — accepted shortcut, comment present.
- `below_one_lot` on any qty-0 contribution follows contracts §2.4 literally and matches UX "sẽ tích luỹ đến khi đủ 1 lô"
  (min at the first qty-0 close = start close in 005). No escalation needed.

### Correctness (checked)
- Hand recompute (independent python, Decimal half-up, lot 100, fee 0.15 %, tax 0.1 %):
  005 cash 2,635,975 / shares 100 / liquidation 12,610,975 / pl 610,975 / 5.0915 %; 005b 10,610,975 / 6.1098 %;
  007 cash 594,900 / shares 300 / 3,886,650 / -113,350 / -2.8338 %; 006 cash 1,271,950 / shares 200. All equal the goldens.
- No look-ahead: each contribution reads `bars_1d(t, t, as_of=t)`; only bar existence (not prices) beyond t is used
  for the no_bar shift, as accepted in AI-whatif-lumpsum. Test perturbs bars after each t_i -> identical prefix.
- Schedule: day clamp, month wrap, leap Feb 29, after_end drop correct; `style` validated by `Literal` in the model, so
  removing the engine `style_not_supported` check is safe. Lump-sum output unchanged except the new D4 flags.
- Layering: import-linter ok; no new dependency; no SQL, no secrets, no network in tests.

### Checks on H `95b7fc6`
- `q.sh kernel make test-kernel`: exit 0 — 175 passed, 20 deselected (db); ruff All checks passed; mypy no issues (5 files);
  lint-imports ok.
- `q.sh analytics pytest -q tests` (services/analytics): 27 passed.
- `-m db` not needed (no migration/repository/SQL change).

Verdict: CHANGES_REQUIRED (2 must-fix). Code is otherwise APPROVE-ready.
