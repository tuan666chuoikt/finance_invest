"""Reconciliation press step (F-016; tech plan sprint-05 R7, R8; data.md 1.4 (3)). Glue only: the rules are
`finvest_analytics.adjust.recon`; this loads our own tables, writes `recon_mismatches` + R8 anomalies and one
`crawl_runs` row (feed `recon`). 0 source requests."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import httpx
from finvest_analytics.adjust.recon import ReconResult, reconcile, ref_check, summary
from finvest_analytics.domain.models import AdjBar, Factor, NominalBar
from finvest_market_data.domain.ports import PayloadShapeError, SourceNoLongerServes
from finvest_market_data.infrastructure import repositories as repo
from finvest_rules.calendar import trading_days
from finvest_rules.prices import tick_size
from sqlalchemy import Connection, text

from finvest_crawler.adapters.registry import make_source
from finvest_crawler.feeds.bars_1d import COUNT
from finvest_crawler.feeds.ticks import _fetcher
from finvest_crawler.fetch import Fetcher, SourceBlocked
from finvest_crawler.settings import Settings

FEED = "recon"
SOURCE = "vci"  # the adjusted history that reconstruction inverts (data.md V2)


@dataclass
class ReconRun:
    summary: str = ""
    results: dict[str, ReconResult] = field(default_factory=dict)
    expected: int = 0
    checked: int = 0  # names that had data to compare
    missing: list[str] = field(default_factory=list)  # no src rows or no nominal rows: never a pass
    mismatches: int = 0
    anomalies: int = 0  # R8 findings
    run_id: int = 0
    ssi_mismatches: int = 0  # --cross-check ssi: printed and in `reason` only (storing both waits for F-021)
    ssi_requests: int = 0
    ssi_blocked: bool = False


def default_symbols(conn: Connection) -> list[str]:
    """VN30 (current members) and scenario symbols: the head of `repo.ca_symbols_in_order`, which cannot
    return only its first two tiers. shortcut: api-owned table read by name, as there; one query if a third
    reader appears."""
    return [r[0] for r in conn.execute(text("""
        SELECT s.symbol FROM symbols s WHERE NOT s.is_delisted AND (
          EXISTS (SELECT 1 FROM symbol_index_membership m WHERE m.symbol = s.symbol
                  AND m.index_code = 'VN30' AND m.valid_to IS NULL)
          OR s.symbol IN (SELECT DISTINCT symbol FROM scenarios)) ORDER BY s.symbol"""))]


def _compare(conn: Connection, sym: str, source: str, nominal, factors) -> ReconResult | None:
    src = repo.newest_src_bars(conn, sym, source)
    if not src:
        return None
    return reconcile([NominalBar(sym, d, c, k) for d, c, k, _ in nominal],  # type: ignore[arg-type]
                     [Factor(sym, d, f) for d, f, _ in factors],
                     [AdjBar(sym, x.trading_date, Decimal(x.adj_c), x.last) for x in src],
                     self_check=(source == "vci"))  # only V2 is what reconstructed rows were inverted from


def _cross_check(conn: Connection, run_date: date, names: list[str], fetcher: Fetcher, r: ReconRun) -> None:
    """S2 as a second `theirs` (F-016): fetch (archive-first), store as source 'ssi', reconcile. The first
    blocked answer stops it; the local result stands."""
    ssi = make_source("ssi", fetcher)
    req0 = fetcher.requests
    try:
        for sym in names:
            nominal = repo.nominal_bars(conn, sym)
            if not nominal:
                continue
            try:
                bars = ssi.bars([sym], "1d", run_date, COUNT)
            except (SourceNoLongerServes, PayloadShapeError, httpx.HTTPError):
                continue  # this name stays uncompared on S2; the others go on
            if not bars:
                continue
            # fetched_at is the archive file's mtime, so a replay hits the same key
            mtime = fetcher.archive.path("bars_1d_ssi", run_date, f"{sym}-1d-{COUNT}").stat().st_mtime
            repo.upsert_bars_1d_src(conn, bars, datetime.fromtimestamp(mtime, UTC))
            conn.commit()
            res = _compare(conn, sym, "ssi", nominal, repo.adj_factors_for(conn, sym))
            r.ssi_mismatches += len(res.mismatches) if res else 0
    except SourceBlocked:
        r.ssi_blocked = True
    r.ssi_requests = fetcher.requests - req0


def _r8(conn: Connection, sym: str, kind: tuple[str, str] | None, factors, nominal) -> int:
    """R8: our factor against the exchange's reference price on each observed ex-date; returns findings."""
    # tick unknown, or UPCoM whose reference is the previous day's VWAP (not stored), not its close (VN§3)
    if kind is None or kind[0] == "UPCOM":
        return 0
    by_date = {d: (c, k, ref) for d, c, k, ref in nominal}
    found = 0
    for ex, f, _ in factors:
        cur = by_date.get(ex)
        if not cur or cur[1] != "observed" or not cur[2]:
            continue
        prev = by_date.get(trading_days(ex - timedelta(14), ex - timedelta(1))[-1])
        if not prev or prev[1] != "observed" or ref_check(f, prev[0], cur[2], tick_size(*kind, cur[2])):
            continue
        repo.insert_anomaly_once(conn, sym, ex, "adj_factor_ref_mismatch",
                                 f"factor={f} pre_close={prev[0]} ref={cur[2]}")
        found += 1
    return found


def run_recon(settings: Settings, run_date: date, symbols: list[str] | None = None, *,
              conn: Connection | None = None, cross_check: str | None = None,
              fetcher: Fetcher | None = None) -> ReconRun:
    if cross_check not in (None, "ssi"):
        raise ValueError(f"unknown cross-check source {cross_check!r}")
    own = repo.engine(settings.database_url) if conn is None else None
    conn = conn or own.connect()  # type: ignore[union-attr]
    client = httpx.Client() if cross_check and fetcher is None else None
    if client:
        fetcher = _fetcher(settings, client)
    try:
        return _run(conn, run_date, symbols, fetcher if cross_check else None)
    finally:
        if client:
            client.close()
        if own:
            conn.close()
            own.dispose()


def _run(conn: Connection, run_date: date, symbols: list[str] | None, fetcher: Fetcher | None) -> ReconRun:
    repo.fail_unfinished_runs(conn, FEED, run_date)
    run_id = repo.insert_crawl_run(conn, FEED, run_date, datetime.now(UTC))
    conn.commit()
    r = ReconRun(run_id=run_id)
    try:
        names = default_symbols(conn) if symbols is None else symbols
        kinds = {s.symbol: (s.exchange, s.type) for s in repo.list_symbols(conn)}
        r.expected = len(names)
        for sym in names:
            nominal = repo.nominal_bars(conn, sym)
            factors = repo.adj_factors_for(conn, sym)
            res = _compare(conn, sym, SOURCE, nominal, factors) if nominal else None
            if not res:  # listed by `missing` below
                continue
            repo.replace_recon_mismatches(conn, sym, [(m.trading_date, m.ours, m.theirs, m.diff_pct)
                                                      for m in res.mismatches])
            r.anomalies += _r8(conn, sym, kinds.get(sym), factors, nominal)
            conn.commit()  # an interrupt loses at most this one symbol
            r.results[sym] = res
        done = {s for s, x in r.results.items() if x.checked}  # nothing compared is missing too
        r.checked, r.missing = len(done), sorted(set(names) - done)
        r.mismatches = sum(len(x.mismatches) for x in r.results.values())
        r.summary = summary(r.results, set(names))
        if fetcher:
            _cross_check(conn, run_date, names, fetcher, r)
            r.summary += (f" | vci: {r.mismatches}, ssi: {r.ssi_mismatches} mismatches"
                          + ("; ssi blocked, cross-check stopped" if r.ssi_blocked else ""))
        status = "partial" if r.missing else "ok"
        repo.finish_crawl_run(conn, run_id, status, r.summary, r.ssi_requests, r.mismatches, None)
        conn.commit()
    except Exception:
        conn.rollback()
        repo.finish_crawl_run(conn, run_id, "failed", None, 0, 0, None)
        conn.commit()
        raise
    return r
