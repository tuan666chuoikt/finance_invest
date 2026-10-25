export FINVEST_UID ?= $(shell id -u)
export FINVEST_GID ?= $(shell id -g)
.PHONY: test-kernel test lint web-install web-test web-build contracts
lint:
	uv run ruff check .

test-kernel:
	uv run pytest -m "not db" -q && uv run ruff check . && uv run mypy && uv run lint-imports

test: test-kernel
	uv run pytest -m db -q -rs

web-install:
	npm --prefix apps/web ci
web-test:
	npm --prefix apps/web run typecheck && npm --prefix apps/web test
web-build:
	npm --prefix apps/web run build
# OpenAPI export + TS types (needs BE-contracts-ts: finvest_api.export_openapi)
contracts:
	uv run python -m finvest_api.export_openapi && npm --prefix apps/web run gen

# docker compose (ops); mkdir first so the host user, not the Docker daemon (root), creates data/
DATE ?= $(shell TZ=Asia/Ho_Chi_Minh date +%F)
.PHONY: up down logs crawl backfill db-shell test-db smoke
up:
	mkdir -p data/raw data/exports
	docker compose up -d --build
down:
	docker compose down
logs:
	docker compose logs -f --tail=100
crawl:
	mkdir -p data/raw data/exports
	docker compose run --rm --build crawler ticks --date $(DATE)
# one-off daily-bars back-fill; resume = run again. Run outside 15:00-23:00 VN (shared rate budget)
backfill:
	mkdir -p data/raw data/exports
	docker compose run --rm --build crawler bars --date $(DATE)
db-shell:
	docker compose exec db psql -U finvest finvest

# db tests on the host against the compose db (loopback 55432); per-branch db: make test-db FINVEST_TEST_DB=finvest_<branch>_test
FINVEST_TEST_DB ?= finvest_test
PGPASS = $(shell sed -n 's/^POSTGRES_PASSWORD=\([^ #]*\).*/\1/p' .env)
test-db:
	@case "$(FINVEST_TEST_DB)" in *_test) ;; *) echo "FINVEST_TEST_DB must end in _test (tests drop all tables)"; exit 1;; esac
	docker compose exec -T db createdb -U finvest $(FINVEST_TEST_DB) || true
	FINVEST_DATABASE_URL=postgresql+psycopg://finvest:$(PGPASS)@127.0.0.1:55432/$(FINVEST_TEST_DB) uv run pytest -m db -q -rs
smoke:
	docker compose exec -T db psql -U finvest finvest -f - < ops/smoke.sql
