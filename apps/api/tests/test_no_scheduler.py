"""F-034: crawling is manual; no timer, service or cron file ships in the repo."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_no_scheduler() -> None:
    assert not (ROOT / "ops/systemd").exists()
    makefile = (ROOT / "Makefile").read_text().lower()
    assert "timer" not in makefile and "systemctl" not in makefile
    names = [p.name for p in (ROOT / "ops").rglob("*")]
    leftovers = [n for n in names if n.endswith((".timer", ".service")) or "crontab" in n]
    assert leftovers == []
