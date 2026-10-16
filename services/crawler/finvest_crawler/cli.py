import argparse
import re
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

from finvest_crawler.feeds.ticks import run_ticks
from finvest_crawler.settings import Settings

VN = ZoneInfo("Asia/Ho_Chi_Minh")


def _symbols(s: str) -> list[str]:
    out = [x.strip().upper() for x in s.split(",") if x.strip()]
    for x in out:
        if not re.fullmatch(r"[A-Z0-9]{1,10}", x):
            raise argparse.ArgumentTypeError(f"bad symbol: {x!r}")
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="finvest-crawl")
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("ticks", help="crawl a full session of ticks")
    t.add_argument("--date", type=date.fromisoformat, default=datetime.now(VN).date())
    t.add_argument("--only", default=None, help="SYM,SYM",
                   type=_symbols)
    a = p.parse_args(argv)

    if a.date.weekday() >= 5:  # holidays come with finvest_rules; weekend check only for now
        print("not a trading day (weekend)")
        return 0
    m = run_ticks(Settings(), a.date, a.only)
    return 2 if m.status == "blocked" else 0  # non-zero so the 20:00 retry timer sees the failure


if __name__ == "__main__":
    sys.exit(main())
