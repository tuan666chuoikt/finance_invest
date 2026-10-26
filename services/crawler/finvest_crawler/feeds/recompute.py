"""Per-press recompute of adjustment factors and reconstructed nominal rows (F-015; tech plan sprint-05 R1-R6,
R9; data.md 1.4 (1)). Glue only: the maths is `finvest_analytics.adjust.series.reconstruct`; this module loads
the inputs, turns unusable events into anomalies and writes `adj_factors` + `bars_1d` (kind `reconstructed`).
Reads only our own tables: 0 source requests."""

from collections.abc import Sequence
from datetime import UTC, date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from finvest_analytics.adjust.series import cumulative, events_by_ex_date, reconstruct, round_vnd
from finvest_analytics.domain.models import AdjBar, CorporateAction, Factor
from finvest_market_data.domain.models import Bar
from finvest_market_data.infrastructure import repositories as repo
from finvest_rules import RULES_VERSION, CaEvent, InvalidCorporateAction
from sqlalchemy import Connection, Engine

SOURCE = "vci"  # the adjusted history that reconstruction inverts (data.md V2)
VN = ZoneInfo("Asia/Ho_Chi_Minh")
Anomaly = tuple[date, str, str]  # (ex_date, rule, value)
Result = tuple[list[Factor], list[Bar], list[Anomaly]]


def _reconstruct(src: list[AdjBar], events: dict[date, list[CaEvent]], observed: dict[date, int]):
    """`reconstruct`, dropping each ex-date whose event data is unusable (the symbol continues, R2/R6)."""
    bad: list[tuple[date, str]] = []
    while True:
        try:
            return *reconstruct(src, events, observed), bad
        except InvalidCorporateAction:
            # the walk is newest first, so the first ex-date (descending) whose suffix fails is the culprit
            for d in sorted(events, reverse=True):
                try:
                    reconstruct(src, {e: v for e, v in events.items() if e >= d}, observed)
                except InvalidCorporateAction as e:
                    bad.append((d, e.reason))
                    del events[d]
                    break


def _one(conn: Connection, sym: str, acts: list, rules_version: str) -> Result:
    rows = repo.newest_src_bars(conn, sym, SOURCE)
    if not rows:  # nothing to invert; leave what is stored
        return [], [], []
    src = [AdjBar(sym, r.trading_date, Decimal(r.adj_c), r.last) for r in rows]
    observed = {d: c for d, c, kind, _ in repo.nominal_bars(conn, sym) if kind == "observed"}
    events = events_by_ex_date([CorporateAction(sym, a.ex_date, CaEvent(
        a.type, a.ratio_a, a.ratio_b, a.cash_per_share, a.issue_price), datetime.now(UTC))
        for a in acts if a.ex_date])  # NULL ex_date = listing_change: no factor
    first = src[0].trading_date
    anomalies: list[Anomaly] = [(d, "adj_factor_no_pre_close", "no_bar_before_ex_date")
                                for d in sorted(events) if d <= first]  # R1: never guessed
    nominal, factors, bad = _reconstruct(src, events, observed)
    anomalies += [(d, "adj_factor_invalid_input", reason) for d, reason in bad]
    ids = repo.corporate_action_ids(conn, sym)
    by_date = {r.trading_date: r for r in rows}
    newest = max(r.fetched_at for r in rows)
    out = []
    for n in nominal:  # same factor for every price of the bar, so the OHLC reconstructs like the close
        r = by_date[n.trading_date]
        g = cumulative(factors, n.trading_date, r.last)  # its own version's last (R6a)
        o, h, lo = (max(1, round_vnd(Decimal(x) / g)) for x in (r.adj_o, r.adj_h, r.adj_l))
        out.append(Bar(sym, datetime(n.trading_date.year, n.trading_date.month, n.trading_date.day,
                                     tzinfo=VN).astimezone(UTC), o, h, lo, n.c, r.v, r.value, SOURCE))
    repo.replace_adj_factors(conn, sym, [(f.ex_date, str(f.f), ids.get(f.ex_date)) for f in factors],
                             rules_version)
    # the repo guard keeps observed rows
    repo.upsert_bars_1d(conn, out, nominal_kind="reconstructed", fetched_at=newest)
    for d, rule, value in anomalies:
        repo.insert_anomaly_once(conn, sym, d, rule, value)
    return factors, out, anomalies


def recompute(
    conn: Connection, symbols: Sequence[str], *, rules_version: str = RULES_VERSION
) -> dict[str, Result]:
    """Recompute `adj_factors` and the reconstructed `bars_1d` rows of each symbol; one commit per symbol."""
    out: dict[str, Result] = {}
    cas = repo.corporate_actions_for(conn, symbols)
    for sym in symbols:
        out[sym] = _one(conn, sym, cas[sym], rules_version)
        conn.commit()
    return out


def recompute_press(engine: Engine, changed: Sequence[str], run_id: int) -> None:
    """The press's step 4: recompute the stale names and note it on the `corporate_actions` run row."""
    with engine.connect() as conn:
        names, skipped = repo.recompute_set(conn, changed, SOURCE)
        recompute(conn, names)
        repo.append_run_reason(conn, run_id, f"recompute: {len(names)} symbols, {skipped} skipped")
