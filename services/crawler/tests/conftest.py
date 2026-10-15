import pytest


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for k in list(__import__("os").environ):
        if k.startswith("FINVEST_"):
            monkeypatch.delenv(k)
