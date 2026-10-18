# contracts

`openapi.json` is generated from the FastAPI app; `apps/web/src/api/types.ts` is generated from it.
Regenerate both after changing any API model: `make contracts`.
Check only: `uv run python -m finvest_api.export_openapi --check` (the kernel test `test_openapi_current` does the same).
Never edit the generated files by hand.
