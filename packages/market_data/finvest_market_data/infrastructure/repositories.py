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
    tuple_,
)
from sqlalchemy.dialects.postgresql import insert

from finvest_market_data.domain.manifest import Manifest
from finvest_market_data.domain.models import Bar, IndexBar, SymbolRecord, Tick
from finvest_market_data.infrastructure.tables import (
    bars_1d_src,
    crawl_runs,
    crawl_sessions,
    data_anomalies,
    index_1d,
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
    # a late `missed` replay must not erase the rows a `partial`/`complete` session recorded
    conn.execute(ins.on_conflict_do_update(
        index_elements=["feed", "trading_date"], set_=vals,
        where=or_(crawl_sessions.c.status.not_in(("partial", "complete")), ins.excluded.status != "missed")))


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


def daily_coverage(conn: Connection) -> dict[str, Decimal]:
    """Per exchange: share of symbols (delisted included) with at least one `bars_1d_src` row, in percent
    with 1 decimal. Feeds platform.md §2.3 `daily_coverage_pct`."""
    covered = exists().where(bars_1d_src.c.symbol == symbols.c.symbol)
    pct = func.round(100 * func.count().filter(covered) / func.count().cast(Numeric), 1)
    q = select(symbols.c.exchange, pct).group_by(symbols.c.exchange)
    return {r[0]: r[1] for r in conn.execute(q)}
