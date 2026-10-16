import csv
from dataclasses import dataclass
from datetime import date, timedelta
from functools import cache
from importlib.resources import files


class CalendarNotMaintained(ValueError):
    """The year is outside holidays.csv; holidays are never inferred (VN§2, F-003)."""


@dataclass(frozen=True)
class CalendarDay:
    trading_date: date
    venue: str
    is_open: bool
    kind: str  # trading | weekend | holiday | half
    name: str | None


@cache
def _load() -> tuple[dict[date, tuple[str, str]], range]:
    text = files("finvest_rules").joinpath("holidays.csv").read_text(encoding="utf-8")
    rows = {date.fromisoformat(r["date"]): (r["kind"], r["name"]) for r in csv.DictReader(text.splitlines())}
    years = {d.year for d in rows}
    return rows, range(min(years), max(years) + 1)


def day(d: date, venue: str = "HOSE") -> CalendarDay:
    # shortcut: one holiday list for all venues (venue is echoed), split when a venue-specific closure appears
    rows, years = _load()
    if d.year not in years:
        raise CalendarNotMaintained(d.year)
    if d.weekday() >= 5:
        return CalendarDay(d, venue, False, "weekend", None)
    if d in rows:
        kind, name = rows[d]
        return CalendarDay(d, venue, kind == "half", kind, name)
    return CalendarDay(d, venue, True, "trading", None)


def trading_days(start: date, end: date, venue: str = "HOSE") -> list[date]:
    days = (start + timedelta(n) for n in range((end - start).days + 1))
    return [d for d in days if day(d, venue).is_open]
