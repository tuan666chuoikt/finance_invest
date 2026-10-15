.PHONY: test-kernel test lint
lint:
	uv run ruff check .

test-kernel:
	uv run pytest -m "not db" -q && uv run ruff check . && uv run mypy && uv run lint-imports

test: test-kernel
	uv run pytest -m db -q
