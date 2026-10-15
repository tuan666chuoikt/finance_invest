
from finvest_crawler.cli import main
from finvest_crawler.settings import Settings


def test_weekend_exits_0(capsys):
    assert main(["ticks", "--date", "2026-10-18"]) == 0
    assert "not a trading day (weekend)" in capsys.readouterr().out


def test_settings_defaults_and_no_url_in_repr():
    s = Settings(_env_file=None)
    assert s.source_ticks == "kbs" and s.rate_per_s["ssi"] == 1 and s.retention_days is None
    assert "postgresql" not in repr(s)
