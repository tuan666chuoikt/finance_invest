"""Monthly DCA contribution schedule (contracts §2.4, F-057); reused by the F-081 backtest wrapper."""

import calendar as _cal
from datetime import date

from .dates import record, shift_forward


def schedule(
    start: date, end: date, calendar: list[date], shifts: list[dict] | None = None
) -> list[tuple[date, date]]:
    """(requested, actual) per month from `start` to `end`: day `start.day` (clamped to the month's last day),
    shifted forward to a trading day of `calendar`. A contribution shifted past `end` is dropped and noted in
    `shifts` (reason after_end); every kept shift is noted with field "contribution". `calendar` must reach
    a few days past `end`."""
    out, (y, m) = [], (start.year, start.month)
    while (y, m) <= (end.year, end.month):
        req = date(y, m, min(start.day, _cal.monthrange(y, m)[1]))
        act = shift_forward(req, calendar)
        if act is None or act > end:
            if shifts is not None:
                shifts.append(
                    {
                        "field": "contribution",
                        "from": req.isoformat(),
                        "to": act.isoformat() if act else None,
                        "reason": "after_end",
                    }
                )
        else:
            if shifts is not None:
                record(shifts, "contribution", req, act)
            out.append((req, act))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out
