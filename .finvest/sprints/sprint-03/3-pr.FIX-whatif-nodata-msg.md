# 3-pr FIX-whatif-nodata-msg (round 1)
APPROVE. Reviewed head b09b9592000438dc097a7ea211b87e35455d41da (synced with origin/sprint-03, clean merge).
Files: apps/api/finvest_api/errors.py, apps/api/tests/test_whatif_api.py, services/analytics/.../sim/whatif.py (+symbol in NO_DATA details, additive, declared), tests/test_whatif_lumpsum.py (2 pins updated).
Size: 33+/5- vs ~35 est, within 1.5x. Templates match card; fallback to code on missing/None keys; code/details unchanged.
Checks: make test-kernel exit 0 (227 passed); api+analytics -m "not db" 80 passed; ruff and mypy clean.
Must-fix: none. Nit: none.
Merge sha: 481a42405b936cd06047690116f181b374776d1e
