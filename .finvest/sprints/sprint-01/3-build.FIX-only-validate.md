# 3-build FIX-only-validate
Result: done. `--only` validated at CLI (`^[A-Z0-9]{1,10}$` after strip/upper, ArgumentTypeError -> exit 2); `Archive.path` raises ValueError on empty/`/`/`\`/leading `.` and on resolved path escaping root.
Files: services/crawler/finvest_crawler/{cli,archive}.py, tests/{test_cli,test_archive}.py (+41/-2).
Checks: NOT run via pytest/ruff, the sandbox has no python deps or uv. Verified archive.path and _symbols logic by a stdlib script (all bad names raise, `fpt, vnm` -> [FPT, VNM], `_manifest` valid).
Tester: run crawler suite; remove xfail from test_f017_symbol_param_cannot_escape_archive (branch test/sprint-01/be) and confirm it passes.
Deviations / outside-set edits: none.
