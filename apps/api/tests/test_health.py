from fastapi.testclient import TestClient
from finvest_api.main import app, get_engine


class _Conn:
    def __init__(self, fail):
        self.fail = fail

    def __enter__(self):
        if self.fail:
            raise RuntimeError("down")
        return self

    def __exit__(self, *a):
        return False

    def execute(self, _):
        return 1


class _Engine:
    def __init__(self, fail):
        self.fail = fail

    def connect(self):
        return _Conn(self.fail)


def _get(fail):
    app.dependency_overrides[get_engine] = lambda: _Engine(fail)
    try:
        return TestClient(app).get("/health")
    finally:
        app.dependency_overrides.clear()


def test_health_ok():
    r = _get(False)
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "db": "ok", "version": "0.1.0", "rules_version": None}


def test_health_db_down():
    r = _get(True)
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "DB_UNAVAILABLE"
