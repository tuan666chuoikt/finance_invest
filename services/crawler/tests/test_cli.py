
from finvest_crawler.cli import main
from finvest_crawler.settings import Settings


def test_weekend_exits_0(capsys):
    assert main(["ticks", "--date", "2026-10-18"]) == 0
    assert "not a trading day (weekend)" in capsys.readouterr().out


def test_settings_defaults_and_no_url_in_repr():
    s = Settings(_env_file=None)
    assert s.source_ticks == "kbs" and s.rate_per_s["ssi"] == 1 and s.retention_days is None
    assert "postgresql" not in repr(s)


def test_only_normalised(monkeypatch):
    seen = []
    monkeypatch.setattr("finvest_crawler.cli.run_ticks",
                        lambda s, d, only: seen.append(only) or type("M", (), {"status": "ok"})())
    assert main(["ticks", "--date", "2026-10-15", "--only", "fpt, vnm"]) == 0
    assert seen == [["FPT", "VNM"]]


def test_only_bad_symbol_exits_2_without_running(monkeypatch):
    import pytest
    monkeypatch.setattr("finvest_crawler.cli.run_ticks", lambda *a: pytest.fail("ran"))
    with pytest.raises(SystemExit) as e:
        main(["ticks", "--date", "2026-10-15", "--only", "../../x"])
    assert e.value.code == 2
