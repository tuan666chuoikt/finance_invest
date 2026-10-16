# 3-build BE-compose
Result: DONE. Files: docker-compose.yml, Dockerfile, .dockerignore, Makefile (appended), README.md (Run rewritten), ops/README.md, .env.example (+POSTGRES_PASSWORD; outside-set, needed by the card).
Contract: db has no ports, bind ./data/pg, pg_isready healthcheck; api on 127.0.0.1:8000 only, runs alembic then uvicorn; crawler in profile `tools`; one image.
Acceptance transcript (run for real with docker):
- `make up` then `curl 127.0.0.1:8000/api/health` -> {"status":"ok","db":"ok","version":"0.1.0","rules_version":null}
- `ss -ltn`: only 127.0.0.1:8000; nothing on 5432; `git status --porcelain` shows no data/ or .env
- `make crawl DATE=2026-10-18` -> "not a trading day (weekend)"; `DATE=2026-10-16` -> exit 3 (not implemented), as allowed
- `make down && make up` -> health ok, no errors in api log; `docker compose config` valid
Deviations: image tag `2.17-pg16` does not exist on Docker Hub; used `timescale/timescaledb:2.17.2-pg16`. Alembic is invoked as `alembic -c apps/api/alembic.ini upgrade head`. `make crawl` on the weekend prints the message and exit status was seen as 0 only via the tail pipe; the weekday path returns 3 through make. Not measured: weekend exit code directly.
Notes for tester: Makefile `crawl` surfaces the container exit code through make.

## Fix round 1
- Must-fix: api and crawler now share `image: finvest-app:local`; `make crawl` uses `run --rm --build`, so crawl always runs current source. Proof: edited a crawler source file, `make up` then `make crawl DATE=2026-10-18` rebuilt and ran ("not a trading day (weekend)"); both services use the one tag.
- Nits done: healthcheck `-h 127.0.0.1`; .env.example password wording. Not done: root-owned data/, Dockerfile layer caching, make exit code note.
- `docker compose config -q` OK. data/ left root-owned (needs sudo to remove; gitignored).
