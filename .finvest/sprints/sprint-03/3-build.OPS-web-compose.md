# 3-build OPS-web-compose
Result: done. `web` service (nginx static + `/api/` proxy) on 127.0.0.1:8080.
Files: apps/web/Dockerfile, ops/nginx/web.conf, docker-compose.yml, Makefile, .dockerignore, README.md (1 line).
Checks: `docker compose config` shows web published host_ip 127.0.0.1 only; image builds; standalone container: /scenarios 200 (SPA fallback), /api/health -> 502 without an api (proxy path hit). `make web-test`: 7 files, 30 tests passed.
Not run: full `docker compose up` with db/api, `ss -ltn` check, `make contracts` (needs BE-contracts-ts `export_openapi`, not yet merged).
Deviation: compose build context is repo root (`dockerfile: apps/web/Dockerfile`), not `apps/web`, so the Dockerfile can COPY ops/nginx/web.conf. .dockerignore got `**/node_modules`, `**/dist`.
Outside-set edits: none beyond README line (in plan).
Tester notes: run `make up`, then curl 8080/api/health and 8080/scenarios.
