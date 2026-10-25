# 3-build AI-rw-curve (S04-RW AI-1 + AI-3)

Result: done. Curve loop starts at i = 0 with an assert that the first calendar day is the first fill; holding_days comment added.
Files: services/analytics/finvest_analytics/sim/whatif.py, tests/test_whatif_lumpsum.py, tests/test_whatif_dca.py.
Tests: lumpsum curve[0] = buy date, market_value 9_985_975; DCA curve[0].invested == contributions[0].amount_vnd.
Checks: pytest services/analytics 42 passed; ruff clean; goldens untouched; `i = -1` gone.
Deviations: none. Outside-set edits: tests/test_whatif_dca.py (plan names its fixture for the DCA assert).
