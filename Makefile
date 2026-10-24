export FINVEST_UID ?= $(shell id -u)
export FINVEST_GID ?= $(shell id -g)
.PHONY: test-kernel test lint web-install web-test web-build contracts
lint:
	uv run ruff check .

test-kernel:
	uv run pytest -m "not db" -q && uv run ruff check . && uv run mypy && uv run lint-imports

test: test-kernel
	uv run pytest -m db -q

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
.PHONY: up down logs crawl backfill db-shell
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
