export FINVEST_UID ?= $(shell id -u)
export FINVEST_GID ?= $(shell id -g)
.PHONY: test-kernel test lint
lint:
	uv run ruff check .

test-kernel:
	uv run pytest -m "not db" -q && uv run ruff check . && uv run mypy && uv run lint-imports

test: test-kernel
	uv run pytest -m db -q

# docker compose (ops); mkdir first so the host user, not the Docker daemon (root), creates data/
DATE ?= $(shell TZ=Asia/Ho_Chi_Minh date +%F)
.PHONY: up down logs crawl db-shell
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
db-shell:
	docker compose exec db psql -U finvest finvest
