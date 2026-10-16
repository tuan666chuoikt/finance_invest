"""Idempotent writes over a SQLAlchemy Connection (platform.md §4). The caller owns the transaction."""

from collections.abc import Sequence
from datetime import date, datetime
from itertools import batched

from sqlalchemy import Connection, Engine, case, create_engine, func, literal_column, select, tuple_
from sqlalchemy.dialects.postgresql import insert

from finvest_market_data.domain.manifest import Manifest
from finvest_market_data.domain.models import SymbolRecord, Tick
from finvest_market_data.infrastructure.tables import (
    crawl_runs,
    crawl_sessions,
    data_anomalies,
    symbols,
    ticks,
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
    conn.execute(ins.on_conflict_do_update(index_elements=["feed", "trading_date"], set_=vals))


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


def list_symbols(conn: Connection, include_delisted: bool = True) -> list[SymbolRecord]:
    q = select(symbols).order_by(symbols.c.symbol)
    if not include_delisted:
        q = q.where(symbols.c.is_delisted.is_(False))
    return [
        SymbolRecord(r.symbol, r.exchange, r.type, r.name_vi, r.name_en, r.icb_code2, r.is_delisted,
                     r.source, r.listed_at, r.delisted_at)
        for r in conn.execute(q)
    ]
