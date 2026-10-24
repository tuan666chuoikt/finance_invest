# 3-build OPS-crawl-manual
Result: done. api published 127.0.0.1:8001 only, mounts ./data to /app/data (FINVEST_DATA_DIR); ops/systemd, Makefile timer targets removed; docs, README and vite proxy updated; apps/api/tests/test_no_scheduler.py added.
Checks: test_no_scheduler 1 passed; ruff clean; `docker compose config` shows 8001 + /app/data; `make -n install-timers` -> No rule.
Not run: real-stack `make up` + curl (tester).
## Outside-set edits
- services/crawler/tests/test_qa_sprint01.py line 159: expected api port 8000 -> 8001.
Note: a stale cli.py comment mentions "retry timer" (left alone).
