# 3-pr FIX-only-validate - round 1
Verdict: APPROVE. Head H=948c48cb23ded27c6f0a58bc13d64d19b8ef8c72 (already in sync with origin/sprint-01, no merge needed).
Files reviewed: cli.py, archive.py, test_cli.py, test_archive.py (+41/-2), matches the plan file set and ~25 line size.
Review: --only regex ^[A-Z0-9]{1,10}$ after strip/upper raises ArgumentTypeError (exit 2, before run_ticks); Archive.path rejects empty, / , \, leading . and resolved escape; _manifest stays valid. Tests cover both and fail without the change.
Checks: pytest/uv not available in sandbox (same as builder), so not run; logic hand-verified by reading. Tester to run crawler suite and drop the xfail on test_f017 (branch test/sprint-01/be).
Nits: --only "" yields [] (runs all symbols), pre-existing, out of scope.
Merge sha: 2532ecfd7b30be850854a330d09e84346bdec0de
