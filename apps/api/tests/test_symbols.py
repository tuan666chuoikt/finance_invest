def _syms(r):
    return [s["symbol"] for s in r.json()]


def test_search(make_client):
    c = make_client()
    assert _syms(c.get("/api/symbols?q=fp")) == ["FOC", "FPT"]  # no exact match: symbol asc
    assert _syms(c.get("/api/symbols?q=fp&include_delisted=true")) == ["FOC", "FPT", "FPTX"]
    assert _syms(c.get("/api/symbols?q=sữa")) == ["VNM"]
    assert _syms(c.get("/api/symbols?q=%25")) == []  # wildcard is escaped
    assert _syms(c.get("/api/symbols")) == ["FOC", "FPT", "VNM"]
    assert _syms(c.get("/api/symbols?q=FPT")) == ["FPT", "FOC"]  # exact match first
    assert _syms(c.get("/api/symbols?q=fpt")) == ["FPT", "FOC"]
    assert _syms(c.get("/api/symbols?q=FPT&limit=1")) == ["FPT"]


def test_limit_validation(make_client):
    r = make_client().get("/api/symbols?limit=0")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION"
    assert r.json()["error"]["details"] == {"field": "limit"}


def test_detail(make_client):
    c = make_client()
    b = c.get("/api/symbols/fpt").json()["bars_1d"]
    assert (b["first"], b["last"]) == ("2025-01-02", "2026-10-16")
    assert b["as_of"] == "2026-10-17T10:00:00.000+07:00"  # latest fetched_at, 03:00Z
    assert c.get("/api/symbols/VNM").json()["bars_1d"] is None
    r = c.get("/api/symbols/ZZZ")
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"
