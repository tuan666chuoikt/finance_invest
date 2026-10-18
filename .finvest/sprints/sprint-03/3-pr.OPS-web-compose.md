# 3-pr OPS-web-compose

## Round 1 (fi-tech-lead, BE, 2026-10-18) — APPROVE
Reviewed head H = e14d942914131f4a132674eab39704dccd493150 (1026f3c + sync merge of origin/sprint-03 8880ba6, no conflicts).
Size: 6 files, +49 / -4 (plan ~90): within budget.

Files reviewed: apps/web/Dockerfile, ops/nginx/web.conf, docker-compose.yml, Makefile, .dockerignore, README.md.
- Plan/file set: exact. Deviation (build context = repo root, `dockerfile: apps/web/Dockerfile`) is justified: the
  Dockerfile must COPY ops/nginx/web.conf; behaviour identical to the plan. Accepted.
- Contract: system.md N1 / ADR-S-001 loopback only — `docker compose config` shows web `host_ip: 127.0.0.1`,
  published 8080 only; platform.md §2.5 same-origin `/api/` -> `api:8000/api/`; codebase.md §6 Start row matches.
  `test-kernel` unchanged as planned.
- Security: no secrets, no new published port, no 0.0.0.0 host binding (uvicorn's 0.0.0.0 is in-container, pre-existing).

Must-fix: none.

Nits (not blocking, for a later ops task):
1. ops/nginx/web.conf: `index.html` gets default caching; add `Cache-Control: no-cache` on `/index.html` so a rebuilt
   bundle is picked up without a hard reload.
2. ops/nginx/web.conf: when the live board lands (SSE/WebSocket), `/api/` will need `proxy_buffering off` /
   upgrade headers.

Checks on H:
- `make test-kernel` (q.sh): exit 0 — 177 passed, 20 deselected; ruff clean; mypy clean; lint-imports clean.
- `make web-install` (fresh `npm ci`): exit 0. `make web-test`: exit 0 — typecheck ok, 7 files / 30 tests passed.
- `make contracts`: exit 0, no drift (worktree clean afterwards).
- `docker compose build web`: exit 0.
- Acceptance (main stack finance_invest already holds 127.0.0.1:8000, so the web image was run on its network
  `finance_invest_default`, resolving `api` exactly as in compose): `curl /api/health` via 8080 ->
  `{"status":"ok","db":"ok","version":"0.1.0","rules_version":null}` (same as direct 8000); `curl -sI /scenarios` ->
  `200`, `Content-Type: text/html`; unknown `/api/nope` -> 404 from api; `ss -ltn` -> `127.0.0.1:8080` only.
  Not run: a full `docker compose up` of this worktree's own stack (port 8000 taken by the running main stack).

Merged: c4c97adaba8804b7a782fa159738be4d46b39dbf into sprint-03 (base 8880ba6, head e14d942).
