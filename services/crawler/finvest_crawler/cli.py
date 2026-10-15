import argparse
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

VN = ZoneInfo("Asia/Ho_Chi_Minh")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="finvest-crawl")
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("ticks", help="crawl a full session of ticks")
    t.add_argument("--date", type=date.fromisoformat, default=datetime.now(VN).date())
    t.add_argument("--only", type=lambda s: s.split(","), default=None, help="SYM,SYM")
    a = p.parse_args(argv)

    if a.date.weekday() >= 5:  # holidays come with finvest_rules; weekend check only for now
        print("not a trading day (weekend)")
        return 0
    try:
        from finvest_crawler.feeds import ticks  # lands with BE-feed-ticks)
    except ImportError:
        print("not implemented", file=sys.stderr)
        return 3
    return ticks.run(a.date, a.only)  # type: ignore[attr-defined]


if __name__ == "__main__":
    sys.exit(main())
