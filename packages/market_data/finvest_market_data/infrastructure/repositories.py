"""Idempotent writes over a SQLAlchemy Connection (platform.md §4). The caller owns the transaction."""

from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal
from itertools import batched

from sqlalchemy import (
    Connection,
    Engine,
    Numeric,
    bindparam,
    case,
    create_engine,
    exists,
    func,
    literal_column,
    or_,
    select,
    text,
    tuple_,
    update,
)
from sqlalchemy.dialects.postgresql import distinct_on, insert

from finvest_market_data.domain.manifest import Manifest
from finvest_market_data.domain.models import Bar, CorporateAction, IndexBar, SymbolRecord, Tick
from finvest_market_data.infrastructure.tables import (
    adj_factors,
    bars_1d,
    bars_1d_src,
    corporate_action_log,
    corporate_actions,
    crawl_runs,
    crawl_sessions,
    data_anomalies,
    index_1d,
    recon_mismatches,
    symbols,
    ticks,
)
from finvest_market_data.infrastructure.tables import (
    symbol_index_membership as membership,
)

BATCH = 5_000  # 7 columns x 5,000 stays under psycopg's 65,535 bind-parameter cap


def engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True)


def upsert_ticks(conn: Connection, rows: Sequence[Tick]) -> int:
    """Upsert on (symbol, ts, seq); return how many existing rows were changed (price/volume/side differed).

    Unchanged duplicates are a no-op and not counted. Keys must be unique within `rows` (run
    domain.manifest.dedupe first): Postgres rejects a statement that hits one key twice.
    """
    changed = 0
    for chunk in batched(rows, BATCH):
        ins = insert(ticks).values(
            [
                {
                    "symbol": t.symbol,
                    "ts": t.ts,
                    "seq": t.seq,
                    "price": t.price,
                    "volume": t.volume,
                    "side": t.side,
                    "source": t.source,
                }
                for t in chunk
            ]
        )
        new = ins.excluded
        stmt = ins.on_conflict_do_update(
            index_elements=["symbol", "ts", "seq"],
            set_={"price": new.price, "volume": new.volume, "side": new.side, "source": new.source},
            where=tuple_(ticks.c.price, ticks.c.volume, ticks.c.side).is_distinct_from(
                tuple_(new.price, new.volume, new.side)
            ),
        ).returning(literal_column("(xmax = 0)").label("inserted"))  # xmax = 0 only on a fresh insert
        changed += sum(1 for r in conn.execute(stmt) if not r.inserted)
    return changed


def insert_crawl_run(conn: Connection, feed: str, trading_date: date, started_at: datetime) -> int:
    stmt = crawl_runs.insert().values(feed=feed, trading_date=trading_date, started_at=started_at)
    return conn.execute(stmt.returning(crawl_runs.c.id)).scalar_one()


def fail_unfinished_runs(conn: Connection, feed: str, trading_date: date) -> int:
    """Close runs a crash left open (status NULL) so they never read as in progress."""
    r = conn.execute(
        crawl_runs.update()
        .where(
            crawl_runs.c.feed == feed,
            crawl_runs.c.trading_date == trading_date,
            crawl_runs.c.status.is_(None),
        )
        .values(status="failed", reason="interrupted", finished_at=func.now())
    )
    return r.rowcount


def finish_crawl_run(
    conn: Connection,
    id: int,
    status: str,
    reason: str | None,
    requests: int,
    rows: int,
    manifest_path: str | None,
) -> None:
    conn.execute(
        crawl_runs.update()
        .where(crawl_runs.c.id == id)
        .values(
            finished_at=func.now(),
            status=status,
            reason=reason,
            requests=requests,
            rows=rows,
            manifest_path=manifest_path,
        )
    )


def _status_rank(col):
    return case({"complete": 3, "partial": 2, "blocked": 2, "missed": 1}, value=col, else_=0)


def upsert_crawl_session(conn: Connection, m: Manifest) -> None:
    vals = {
        "status": m.status,
        "symbols_fetched": m.symbols_fetched,
        "symbols_no_trades": len(m.symbols_no_trades),
        "symbols_skipped": len(m.symbols_skipped),
        "rows": m.rows,
        "checksum": m.checksum,
        "reason": m.reason,
    }
    ins = insert(crawl_sessions).values(feed=m.feed, trading_date=m.trading_date, **vals)
    # the ledger keeps the richest replay, never lowers the status rank; the manifest file is always written
    conn.execute(ins.on_conflict_do_update(
        index_elements=["feed", "trading_date"], set_=vals,
        where=(ins.excluded.rows >= crawl_sessions.c.rows)
        & (_status_rank(ins.excluded.status) >= _status_rank(crawl_sessions.c.status))))


def insert_anomaly(
    conn: Connection, symbol: str | None, trading_date: date | None, rule: str, value: str | None
) -> None:
    conn.execute(
        data_anomalies.insert().values(symbol=symbol, trading_date=trading_date, rule=rule, value=value)
    )


def session_status(conn: Connection, feed: str, trading_date: date) -> str | None:
    q = select(crawl_sessions.c.status).where(
        crawl_sessions.c.feed == feed, crawl_sessions.c.trading_date == trading_date
    )
    return conn.execute(q).scalar_one_or_none()


def last_session_date(conn: Connection, feed: str) -> date | None:
    q = select(func.max(crawl_sessions.c.trading_date)).where(crawl_sessions.c.feed == feed)
    return conn.execute(q).scalar()


def upsert_symbols(conn: Connection, rows: Sequence[SymbolRecord], fetched_at: datetime) -> None:
    """Upsert on `symbol`. A delisted row keeps the exchange already stored (V3 does not know it) and
    `delisted_at`/`listed_at` are never cleared: a re-listing flips `is_delisted` back only."""
    if not rows:
        return
    ins = insert(symbols).values(
        [
            {
                "symbol": r.symbol, "exchange": r.exchange, "type": r.type, "name_vi": r.name_vi,
                "name_en": r.name_en, "icb_code2": r.icb_code2, "listed_at": r.listed_at,
                "delisted_at": r.delisted_at, "is_delisted": r.is_delisted, "source": r.source,
                "fetched_at": fetched_at,
            }
            for r in rows
        ]
    )
    new = ins.excluded
    conn.execute(
        ins.on_conflict_do_update(
            index_elements=["symbol"],
            set_={
                "exchange": case((new.is_delisted, symbols.c.exchange), else_=new.exchange),
                "type": new.type, "name_vi": new.name_vi, "name_en": new.name_en,
                "icb_code2": new.icb_code2, "is_delisted": new.is_delisted, "source": new.source,
                "fetched_at": new.fetched_at,
                "listed_at": func.coalesce(new.listed_at, symbols.c.listed_at),
                "delisted_at": func.coalesce(symbols.c.delisted_at, new.delisted_at),
            },
        )
    )


def mark_delisted(conn: Connection, present: set[str], run_date: date) -> int:
    """Rows the source no longer lists are delisted, never deleted. An empty `present` is a bad
    payload, not "everything vanished": it changes nothing."""
    if not present:
        return 0
    r = conn.execute(
        symbols.update()
        .where(symbols.c.symbol.not_in(present), symbols.c.is_delisted.is_(False))
        .values(is_delisted=True, delisted_at=func.coalesce(symbols.c.delisted_at, run_date))
    )
    return r.rowcount


def upsert_listed_at(conn: Connection, listed: dict[str, date]) -> int:
    """Set `listed_at` only where it is NULL (source date is the truth, ours is never older)."""
    if not listed:
        return 0
    q = (symbols.update().where(symbols.c.symbol == bindparam("s"), symbols.c.listed_at.is_(None))
         .values(listed_at=bindparam("d")))
    return conn.execute(q, [{"s": k, "d": v} for k, v in listed.items()]).rowcount


def sync_index_membership(
    conn: Connection, index_code: str, members: set[str], run_date: date
) -> tuple[int, int]:
    """Snapshot -> intervals: new symbol opens `[run_date, NULL)`, an open row whose symbol is gone closes
    at `run_date`, unchanged writes nothing. Returns (opened, closed). Empty `members` is bad: no-op."""
    if not members:
        return 0, 0
    cur = select(membership.c.symbol).where(
        membership.c.index_code == index_code, membership.c.valid_to.is_(None))
    open_ = {r[0] for r in conn.execute(cur)}
    new = sorted(members - open_)
    if new:
        conn.execute(insert(membership).values(
            [{"index_code": index_code, "symbol": s, "valid_from": run_date} for s in new]
        ).on_conflict_do_nothing())
    closed = conn.execute(
        membership.update()
        .where(membership.c.index_code == index_code, membership.c.valid_to.is_(None),
               membership.c.symbol.not_in(members))
        .values(valid_to=run_date)).rowcount
    return len(new), closed


def list_symbols(conn: Connection, include_delisted: bool = True) -> list[SymbolRecord]:
    q = select(symbols).order_by(symbols.c.symbol)
    if not include_delisted:
        q = q.where(symbols.c.is_delisted.is_(False))
    return [
        SymbolRecord(r.symbol, r.exchange, r.type, r.name_vi, r.name_en, r.icb_code2, r.is_delisted,
                     r.source, r.listed_at, r.delisted_at)
        for r in conn.execute(q)
    ]


def upsert_bars_1d_src(conn: Connection, bars: Sequence[Bar], fetched_at: datetime) -> None:
    """One versioned snapshot per `fetched_at` (data.md §1.4 (2)): the same `fetched_at` overwrites in place,
    a later one adds a version. Keys must be unique within `bars`."""
    for chunk in batched(bars, BATCH):
        ins = insert(bars_1d_src).values(
            [
                {"symbol": b.symbol, "trading_date": b.trading_date, "source": b.source,
                 "fetched_at": fetched_at, "adj_o": b.o, "adj_h": b.h, "adj_l": b.l, "adj_c": b.c,
                 "v": b.v, "value": b.value}
                for b in chunk
            ]
        )
        new = ins.excluded
        conn.execute(
            ins.on_conflict_do_update(
                index_elements=["symbol", "trading_date", "source", "fetched_at"],
                set_={k: getattr(new, k) for k in ("adj_o", "adj_h", "adj_l", "adj_c", "v", "value")},
            )
        )


def upsert_bars_1d(
    conn: Connection, bars: Sequence[Bar], *, nominal_kind: str, fetched_at: datetime,
    ref: dict[str, int] | None = None,
) -> int:
    """Upsert nominal daily bars on (symbol, trading_date); returns rows written. An `observed` row is never
    replaced by a `reconstructed` one (F-015); every other combination is latest-wins. `ref` maps symbol ->
    exchange reference price (NULL when absent). Keys must be unique within `bars`."""
    written = 0
    for chunk in batched(bars, BATCH):
        ins = insert(bars_1d).values(
            [
                {"symbol": b.symbol, "trading_date": b.trading_date, "o": b.o, "h": b.h, "l": b.l, "c": b.c,
                 "ref": (ref or {}).get(b.symbol), "v": b.v, "value": b.value, "nominal_kind": nominal_kind,
                 "source": b.source, "fetched_at": fetched_at}
                for b in chunk
            ]
        )
        new = ins.excluded
        res = conn.execute(
            ins.on_conflict_do_update(
                index_elements=["symbol", "trading_date"],
                set_={k: getattr(new, k) for k in ("o", "h", "l", "c", "ref", "v", "value", "nominal_kind",
                                                   "source", "fetched_at")},
                where=or_(bars_1d.c.nominal_kind != "observed", new.nominal_kind == "observed"),
            ).returning(bars_1d.c.symbol)  # rowcount is -1 for a batched insert
        )
        written += len(res.all())
    return written


def move_ssi_board_rows(conn: Connection) -> int:
    """Migration 0010: the newest `fetched_at` ssi row per (symbol, trading_date) moves from `bars_1d_src` to
    `bars_1d` as `observed` (ref NULL), then every ssi `bars_1d_src` row is deleted. Returns rows inserted.
    Re-runnable: an existing `bars_1d` row is kept."""
    n = conn.execute(
        text(
            """
            INSERT INTO bars_1d (symbol, trading_date, o, h, l, c, v, value, nominal_kind, source, fetched_at)
            SELECT DISTINCT ON (symbol, trading_date)
                   symbol, trading_date, adj_o, adj_h, adj_l, adj_c, v, value, 'observed', 'ssi', fetched_at
            FROM bars_1d_src WHERE source = 'ssi'
            ORDER BY symbol, trading_date, fetched_at DESC
            ON CONFLICT (symbol, trading_date) DO NOTHING
            """
        )
    ).rowcount
    conn.execute(text("DELETE FROM bars_1d_src WHERE source = 'ssi'"))
    return n


def restore_ssi_board_rows(conn: Connection) -> int:
    """Migration 0010 downgrade: observed ssi rows go back to `bars_1d_src` (they are not derivable);
    reconstructed rows are dropped with the table. Returns rows restored."""
    return conn.execute(
        text(
            """
            INSERT INTO bars_1d_src
                (symbol, trading_date, source, fetched_at, adj_o, adj_h, adj_l, adj_c, v, value)
            SELECT symbol, trading_date, source, fetched_at, o, h, l, c, v, value
            FROM bars_1d WHERE nominal_kind = 'observed' AND source = 'ssi'
            ON CONFLICT DO NOTHING
            """
        )
    ).rowcount


def upsert_index_1d(conn: Connection, bars: Sequence[IndexBar]) -> None:
    """Latest wins per (index_code, trading_date); index levels are not versioned."""
    for chunk in batched(bars, BATCH):
        ins = insert(index_1d).values(
            [
                {"index_code": b.index_code, "trading_date": b.trading_date, "o": b.o, "h": b.h,
                 "l": b.l, "c": b.c, "v": b.v, "value": b.value}
                for b in chunk
            ]
        )
        new = ins.excluded
        conn.execute(
            ins.on_conflict_do_update(
                index_elements=["index_code", "trading_date"],
                set_={k: getattr(new, k) for k in ("o", "h", "l", "c", "v", "value")},
            )
        )


def last_bar_dates(conn: Connection) -> dict[str, date]:
    """Latest `trading_date` per symbol in `bars_1d_src`; a name with no bar is absent."""
    q = select(bars_1d_src.c.symbol, func.max(bars_1d_src.c.trading_date)).group_by(bars_1d_src.c.symbol)
    return {r[0]: r[1] for r in conn.execute(q)}


def daily_coverage(conn: Connection) -> dict[str, Decimal]:
    """Per exchange: share of symbols (delisted included) with at least one `bars_1d_src` row, in percent
    with 1 decimal. Feeds platform.md §2.3 `daily_coverage_pct`."""
    covered = exists().where(bars_1d_src.c.symbol == symbols.c.symbol)
    pct = func.round(100 * func.count().filter(covered) / func.count().cast(Numeric), 1)
    q = select(symbols.c.exchange, pct).group_by(symbols.c.exchange)
    return {r[0]: r[1] for r in conn.execute(q)}


def repair_crawl_sessions_from_ticks(conn: Connection) -> int:
    """Raise `rows`/`symbols_fetched` of `ticks` ledger rows to what the `ticks` table holds per VN day;
    returns rows updated. `checksum` becomes NULL: the manifest on disk is the overwritten replay,
    so a NULL digest is honest and a stale one is not.
    `status`/`reason` stay (the table cannot tell a skip from a no-trade).
    Idempotent (`s.rows < t.n`); never inserts a ledger row (platform.md §4 v1.12)."""
    return conn.execute(
        text(
            """
            UPDATE crawl_sessions s SET rows = t.n, symbols_fetched = t.syms, checksum = NULL
            FROM (SELECT (ts AT TIME ZONE 'Asia/Ho_Chi_Minh')::date AS d, COUNT(*) AS n,
                         COUNT(DISTINCT symbol) AS syms FROM ticks GROUP BY 1) t
            WHERE s.feed = 'ticks' AND s.trading_date = t.d AND s.rows < t.n
            """
        )
    ).rowcount


def repair_index_1d_value(conn: Connection) -> int:
    """NULL `index_1d.value` where it is 0, the volume is 0 or value/volume is outside 100..1e7 VND per unit
    (the adapter's INDEX_VALUE_PER_UNIT band); o/h/l/c/v stay. Returns rows updated; idempotent."""
    return conn.execute(
        update(index_1d)
        .where(index_1d.c.value.is_not(None),
               or_(index_1d.c.v == 0, index_1d.c.value == 0,
                   index_1d.c.value / index_1d.c.v < 100, index_1d.c.value / index_1d.c.v > 10_000_000))
    .values(value=None)
    ).rowcount


CA_FIELDS = ("type", "ex_date", "record_date", "pay_date", "ratio_a", "ratio_b", "cash_per_share",
             "issue_price")


def upsert_corporate_actions(
    conn: Connection, rows: Sequence[CorporateAction], fetched_at: datetime
) -> tuple[int, int]:
    """Upsert on (source, source_event_id); return (rows upserted, log rows written). A changed field of an
    existing row writes one `corporate_action_log` row; an unchanged row writes none, so a re-run is a no-op
    apart from `fetched_at`. Row by row: a press holds a few dozen events per symbol."""
    changes = 0
    for r in rows:
        vals = {**{f: getattr(r, f) for f in CA_FIELDS}, "symbol": r.symbol, "public_date": r.public_date,
                "title": r.title, "fetched_at": fetched_at}
        cur = conn.execute(select(corporate_actions).where(
            corporate_actions.c.source == r.source, corporate_actions.c.source_event_id == r.source_event_id
        )).first()
        if cur is None:
            conn.execute(insert(corporate_actions).values(
                **vals, source=r.source, source_event_id=r.source_event_id))
            continue
        old = cur._mapping
        log = [{"ca_id": cur.id, "changed_at": fetched_at, "field": f,
                "old": None if old[f] is None else str(old[f]),
                "new": None if vals[f] is None else str(vals[f])}
               for f in CA_FIELDS if old[f] != vals[f]]
        if log:
            conn.execute(insert(corporate_action_log).values(log))
            changes += len(log)
        conn.execute(update(corporate_actions).where(corporate_actions.c.id == cur.id).values(**vals))
    return len(rows), changes


def ca_symbols_in_order(conn: Connection, limit: int | None = None) -> list[str]:
    """Press order: VN30 (current members), then scenario symbols, then the rest by oldest
    `ca_checked_at` (NULL first). Delisted names are excluded."""
    # shortcut: api-owned table read by name; move to a view if a third reader appears
    q = text("""
        SELECT symbol FROM (
          SELECT s.symbol, s.ca_checked_at,
                 CASE WHEN EXISTS (SELECT 1 FROM symbol_index_membership m WHERE m.symbol = s.symbol
                                   AND m.index_code = 'VN30' AND m.valid_to IS NULL) THEN 0
                      WHEN s.symbol IN (SELECT DISTINCT symbol FROM scenarios) THEN 1 ELSE 2 END AS tier
          FROM symbols s WHERE NOT s.is_delisted) t
        ORDER BY tier, CASE WHEN tier = 2 THEN ca_checked_at END NULLS FIRST, symbol
        LIMIT :n""")
    return [r[0] for r in conn.execute(q, {"n": limit})]


def mark_ca_checked(conn: Connection, syms: Sequence[str], at: datetime) -> None:
    conn.execute(update(symbols).where(symbols.c.symbol.in_(list(syms))).values(ca_checked_at=at))


def corporate_actions_for(conn: Connection, syms: Sequence[str]) -> dict[str, list[CorporateAction]]:
    """Every requested symbol is a key (empty list when it has no events), events by ex_date then id."""
    out: dict[str, list[CorporateAction]] = {s: [] for s in syms}
    q = select(corporate_actions).where(corporate_actions.c.symbol.in_(list(syms))).order_by(
        corporate_actions.c.ex_date, corporate_actions.c.id)
    for r in conn.execute(q):
        out[r.symbol].append(CorporateAction(
            r.symbol, r.type, r.ex_date, r.record_date, r.pay_date, r.ratio_a, r.ratio_b,
            r.cash_per_share, r.issue_price, r.source, r.source_event_id, r.public_date, r.title))
    return out


def replace_adj_factors(
    conn: Connection, symbol: str, rows: Sequence[tuple[date, Decimal | str, int | None]], rules_version: str
) -> None:
    """Delete + insert one symbol's factors; rows are (ex_date, factor, ca_id). Pass `factor` as a 12-place
    string or Decimal, never float."""
    conn.execute(adj_factors.delete().where(adj_factors.c.symbol == symbol))
    if rows:
        conn.execute(insert(adj_factors).values([
            {"symbol": symbol, "ex_date": d, "factor": Decimal(f), "ca_id": ca,
             "rules_version": rules_version}
            for d, f, ca in rows]))


def adj_factors_for(conn: Connection, symbol: str) -> list[tuple[date, Decimal, int | None]]:
    q = select(adj_factors.c.ex_date, adj_factors.c.factor, adj_factors.c.ca_id).where(
        adj_factors.c.symbol == symbol).order_by(adj_factors.c.ex_date)
    return [(r.ex_date, r.factor, r.ca_id) for r in conn.execute(q)]


def replace_recon_mismatches(
    conn: Connection, symbol: str, rows: Sequence[tuple[date, int, int, Decimal]]
) -> None:
    """Delete + insert one symbol's mismatches; rows are (trading_date, ours, theirs, diff_pct)."""
    conn.execute(recon_mismatches.delete().where(recon_mismatches.c.symbol == symbol))
    if rows:
        conn.execute(insert(recon_mismatches).values([
            {"symbol": symbol, "trading_date": d, "ours": o, "theirs": t, "diff_pct": p,
             "checked_at": func.now()}
            for d, o, t, p in rows]))


def newest_src_bars(conn: Connection, symbol: str, source: str) -> list[tuple[date, int]]:
    """(trading_date, adj_c) of the newest `fetched_at` version of each date."""
    b = bars_1d_src
    q = (select(b.c.trading_date, b.c.adj_c).where(b.c.symbol == symbol, b.c.source == source)
         .ext(distinct_on(b.c.trading_date)).order_by(b.c.trading_date, b.c.fetched_at.desc()))
    return [(r.trading_date, r.adj_c) for r in conn.execute(q)]


def nominal_bars(conn: Connection, symbol: str) -> list[tuple[date, int, str, int | None]]:
    """(trading_date, c, nominal_kind, ref) by date."""
    q = select(bars_1d.c.trading_date, bars_1d.c.c, bars_1d.c.nominal_kind, bars_1d.c.ref).where(
        bars_1d.c.symbol == symbol).order_by(bars_1d.c.trading_date)
    return [(r.trading_date, r.c, r.nominal_kind, r.ref) for r in conn.execute(q)]
