# 3-pr OPS-crawl-manual

## Round 1 (fi-tech-lead, BE, 2026-10-24) — APPROVE
Reviewed head H = 087ef149b673aac5a63cc23fc719e9d03e92cf08 (cbe32b6 + clean sync merge of origin/sprint-03 4c5037e, no conflicts).

Files reviewed: docker-compose.yml, Makefile, ops/systemd/* (deleted), ops/README.md, README.md, apps/web/vite.config.ts,
apps/api/tests/test_no_scheduler.py, services/crawler/tests/test_qa_sprint01.py (outside set, justified: port assertion 8000->8001 would fail otherwise).

- Plan/file set: matches the block; `.env.example` has no port mention, untouched (correct). Size 34+/55- vs ~70 est: within 1.5x.
- Contract: system.md §5 (127.0.0.1:8001:8000, no timer/cron, ./data:/app/data) and platform.md §2.6 (api mounts ./data at /app/data)
  match exactly; api env mirrors the crawler service (`<<: *app-env` + FINVEST_DATA_DIR=/app/data, Settings env_prefix FINVEST_).
  nginx `proxy_pass http://api:8000` stays (in-compose port unchanged) - correct.
- Tests: test_no_scheduler fails on the base (ops/systemd existed; Makefile had timer/systemctl). Offline, no network.
- Security: loopback only, no secrets, no new dependency.

Must-fix: none.
Nits (not blocking):
1. services/crawler/finvest_crawler/cli.py:49,79 comments still say "retry timer" / "20:00 retry timer"; reword next time cli.py is touched.

Checks on H:
- kernel `make test-kernel`: exit 0 — 214 passed, 22 deselected; ruff clean; mypy no issues (5 files); lint-imports ok.
- `pytest apps/api/tests/test_no_scheduler.py services/crawler/tests/test_qa_sprint01.py`: 18 passed.
- `docker compose config`: api ports [127.0.0.1:8001->8000], volume bind ./data -> /app/data, FINVEST_DATA_DIR=/app/data.
- `make -n install-timers`: "No rule to make target 'install-timers'".
- Not run here: real-stack `make up` + curl 8001/8080 health (SM/BE tester per acceptance).
Merged: 58300d634e313734c2018b70a3673a9c30775696 (base 998011e, head 087ef14). Worktree removed.
