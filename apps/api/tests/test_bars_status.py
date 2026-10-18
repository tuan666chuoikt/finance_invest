def test_status(make_client):
    assert make_client().get("/api/bars/1d/status").json() == {
        "last_trading_date": "2026-10-16",
        "as_of": "2026-10-17T10:00:00.000+07:00",
        "source": "vci",
        "symbols": 1,
    }


def test_status_empty(make_client):
    assert make_client(seed=False).get("/api/bars/1d/status").json() == {
        "last_trading_date": None, "as_of": None, "source": "vci", "symbols": 0}
