# 3-build AI-recon-xsrc (F-016, R7 v1.2)
Result: `reconcile(..., self_check: bool = True)`; the reconstructed <= 1 VND branch runs only when self_check. Default unchanged.
Files: services/analytics/finvest_analytics/adjust/recon.py (+4 lines incl. docstring), services/analytics/tests/test_recon.py (+13).
Contract: acceptance cases covered in one test: self_check=True -> one self_consistency (2.73 > 1); False -> 0 mismatches, checked 1; False with G=1, 71,701 vs 71,700 -> unit_or_adapter.
Checks: analytics suite 73 passed (run via uv with pytest, pytest-socket, pytest-asyncio, hypothesis; no ruff on this machine, so lint not run).
Deviations / outside-set edits: none. No unmerged task branch touches recon.py or test_recon.py.
