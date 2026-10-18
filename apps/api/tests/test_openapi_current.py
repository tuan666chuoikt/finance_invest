from finvest_api.export_openapi import PATH, render


def test_openapi_current():
    assert PATH.read_text(encoding="utf-8") == render(), "openapi.json is stale: run `make contracts`"
