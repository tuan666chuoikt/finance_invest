import pytest
from finvest_crawler.cli import main
from finvest_crawler.settings import Settings


def test_closed_day_exits_0_with_skip_line(capsys, monkeypatch):
    monkeypatch.setattr("finvest_crawler.cli.run_ticks", lambda *a: pytest.fail("ran"))
    assert main(["ticks", "--date", "2026-10-18"]) == 0
    assert '"skipped": "weekend"' in capsys.readouterr().out
    assert main(["ticks", "--date", "2026-09-02"]) == 0
    assert '"skipped": "holiday"' in capsys.readouterr().out


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
    monkeypatch.setattr("finvest_crawler.cli.run_ticks", lambda *a: pytest.fail("ran"))
    with pytest.raises(SystemExit) as e:
        main(["ticks", "--date", "2026-10-15", "--only", "../../x"])
    assert e.value.code == 2


def test_catchup_help_exits_0(capsys):
    with pytest.raises(SystemExit) as e:
        main(["catchup", "--help"])
    assert e.value.code == 0


def _fake_db(monkeypatch):
    class Eng:
        def connect(self):
            from contextlib import nullcontext
            return nullcontext()

        def dispose(self):
            pass
    monkeypatch.setattr("finvest_crawler.cli.repositories.engine", lambda url: Eng())


def test_catchup_exit_2_when_a_day_blocked(monkeypatch):
    _fake_db(monkeypatch)
    ms = [type("M", (), {"status": "complete"})(), type("M", (), {"status": "blocked"})()]
    monkeypatch.setattr("finvest_crawler.cli.catchup", lambda *a, **k: ms)
    assert main(["catchup"]) == 2
    monkeypatch.setattr("finvest_crawler.cli.catchup", lambda *a, **k: ms[:1])
    assert main(["catchup"]) == 0


def test_catchup_exit_2_when_a_day_raised(monkeypatch):
    from finvest_crawler.feeds.catchup import CatchupFailed
    _fake_db(monkeypatch)

    def boom(*a, **k):
        raise CatchupFailed([], ["2026-10-14"])
    monkeypatch.setattr("finvest_crawler.cli.catchup", boom)
    assert main(["catchup"]) == 2


def test_symbols_runs_the_feed_and_exits_2_when_blocked(monkeypatch):
    from finvest_crawler.fetch import SourceBlocked

    seen = []
    monkeypatch.setattr("finvest_crawler.cli.run_symbols", lambda s, d: seen.append(str(d)))
    assert main(["symbols", "--date", "2026-10-15"]) == 0
    assert seen == ["2026-10-15"]

    def blocked(s, d):
        raise SourceBlocked("vci", 429)

    monkeypatch.setattr("finvest_crawler.cli.run_symbols", blocked)
    assert main(["symbols", "--date", "2026-10-15"]) == 2
