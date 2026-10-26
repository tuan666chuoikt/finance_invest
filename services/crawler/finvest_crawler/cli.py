import argparse
import json
import re
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

from finvest_market_data.infrastructure import repositories
from finvest_rules.calendar import day

from finvest_crawler.feeds.bars_1d import run_bars_1d
from finvest_crawler.feeds.catchup import CatchupFailed, catchup
from finvest_crawler.feeds.corporate_actions import run_corporate_actions
from finvest_crawler.feeds.symbols import run_symbols
from finvest_crawler.feeds.ticks import run_ticks
from finvest_crawler.fetch import SourceBlocked
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
    y = sub.add_parser("symbols", help="refresh the symbol master (delisted kept)")
    y.add_argument("--date", type=date.fromisoformat, default=datetime.now(VN).date())
    b = sub.add_parser("bars", help="back-fill daily bars for every symbol and the indices (resumable)")
    b.add_argument("--date", type=date.fromisoformat, default=datetime.now(VN).date())
    b.add_argument("--only", default=None, help="SYM,SYM", type=_symbols)
    c = sub.add_parser("corporate-actions", help="read V5 corporate events (budget ca_budget)")
    c.add_argument("--date", type=date.fromisoformat, default=datetime.now(VN).date())
    sub.add_parser("catchup", help="crawl every trading day missed since the last session")
    a = p.parse_args(argv)

    if a.cmd == "symbols":
        try:
            run_symbols(Settings(), a.date)
        except SourceBlocked as e:
            print(e)
            return 2  # non-zero so a retry timer sees the failure
        return 0

    if a.cmd == "bars":
        try:
            m = run_bars_1d(Settings(), a.date, only=a.only)
        except SourceBlocked as e:
            print(e)
            return 2
        return 2 if m.status == "blocked" else 0

    if a.cmd == "corporate-actions":
        r = run_corporate_actions(Settings(), a.date)
        print(json.dumps({k: v for k, v in vars(r).items() if k != "changed_symbols"}))
        return 2 if r.status == "blocked" else 0

    if a.cmd == "catchup":
        settings = Settings()
        eng = repositories.engine(settings.database_url)
        try:
            with eng.connect() as conn:
                try:
                    ms = catchup(settings, now_vn=datetime.now(VN), conn=conn)
                except CatchupFailed as e:
                    print(e)
                    return 2
        finally:
            eng.dispose()
        return 2 if any(m.status == "blocked" for m in ms) else 0

    cd = day(a.date)
    if not cd.is_open:  # no manifest, no DB row (S01 decision (c))
        print(json.dumps({"skipped": cd.kind, "name": cd.name}, ensure_ascii=False))
        return 0
    m = run_ticks(Settings(), a.date, a.only)
    return 2 if m.status == "blocked" else 0  # non-zero so the 20:00 retry timer sees the failure


if __name__ == "__main__":
    sys.exit(main())
