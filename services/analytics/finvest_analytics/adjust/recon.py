"""Reconciliation rules and run report (tech plan sprint-05 R7, R8; data.md §1.4 (3); VN§6 S7). Pure, no I/O.

ours(d) = nominal(d) x G(d) against theirs(d) = A(d) of the newest source version; G counts only ex-dates
<= the source's last bar (the source could not know later ones), so nothing here looks past that date.
"""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from ..domain.models import AdjBar, Factor, NominalBar
from .series import cumulative, round_vnd

_PCT_PLACES = Decimal("0.0001")  # NUMERIC(8,4)
_PX_PLACES = Decimal("0.01")
UNIT_OR_ADAPTER = "unit_or_adapter"  # G = 1 and still different: not a factor problem
FACTOR_OR_EVENT = "factor_or_event"  # a streak starting at X hints at a missing/wrong event with ex-date X+1
SELF_CONSISTENCY = "self_consistency"  # reconstructed row no longer matches its source within 1 VND


@dataclass(frozen=True)
class Mismatch:
    symbol: str
    trading_date: date
    ours: int
    theirs: int
    diff_pct: Decimal  # 4 places half-up
    note: str = ""  # not stored (recon_mismatches has no column); for the message/report only


@dataclass(frozen=True)
class ReconResult:
    mismatches: list[Mismatch]
    checked: int
    exact_days: int
    first_mismatch: date | None


def reconcile(
    nominal_bars: list[NominalBar],
    factors: list[Factor],
    src_bars: list[AdjBar],
    *,
    threshold: Decimal = Decimal("0.1"),
) -> ReconResult:
    theirs_by_date = {b.trading_date: b.c for b in src_bars}
    if not theirs_by_date:
        return ReconResult([], 0, 0, None)
    last = max(theirs_by_date)
    out: list[Mismatch] = []
    checked = exact = 0
    for b in sorted(nominal_bars, key=lambda b: b.trading_date):
        theirs = theirs_by_date.get(b.trading_date)
        if theirs is None:
            continue
        g = cumulative(factors, b.trading_date, last)
        ours = (b.c * g).quantize(_PX_PLACES, ROUND_HALF_UP)
        diff = abs(ours - theirs)
        pct = (diff / theirs * 100).quantize(_PCT_PLACES, ROUND_HALF_UP) if theirs > 0 else Decimal(100)
        checked += 1
        exact += diff == 0
        if b.nominal_kind == "reconstructed":  # pre-crawl: self-consistency, <= 1 VND (R7)
            note = SELF_CONSISTENCY if diff > 1 else ""
        elif g == 1:  # exact equality, whatever the percentage
            note = UNIT_OR_ADAPTER if diff != 0 else ""
        else:
            note = FACTOR_OR_EVENT if pct > threshold else ""
        if note:
            out.append(Mismatch(b.symbol, b.trading_date, round_vnd(ours), round_vnd(theirs), pct, note))
    return ReconResult(out, checked, exact, out[0].trading_date if out else None)


def summary(results: dict[str, ReconResult], expected: set[str]) -> str:
    """'30/30, k mismatches; first mismatch FPT 2026-09-18'. A symbol with no result or nothing compared is
    missing, never a pass."""
    done = {s: r for s, r in results.items() if s in expected and r.checked}
    out = f"{len(done)}/{len(expected)}, {sum(len(r.mismatches) for r in done.values())} mismatches"
    if missing := sorted(expected - done.keys()):
        out += "; missing " + ", ".join(missing)
    firsts = [(r.first_mismatch, s) for s, r in done.items() if r.first_mismatch]
    if firsts:
        d, s = min(firsts)
        out += f"; first mismatch {s} {d.isoformat()}"
    return out


def round_to_tick(x: Decimal, tick: int) -> int:
    # nearest tick, half-up; VN§3 does not state the exchange's direction, ref_check's 1-tick slack covers it
    return round_vnd(x / tick) * tick


def ref_check(f: Decimal, pre_close: int, board_ref: int, tick: int) -> bool:
    """R8: |round_to_tick(f x P) - ref| <= 1 tick, against the exchange's own reference price (VN§6 S7)."""
    return abs(round_to_tick(f * pre_close, tick) - board_ref) <= tick
