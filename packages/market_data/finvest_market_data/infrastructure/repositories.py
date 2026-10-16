"""Idempotent writes over a SQLAlchemy Connection (platform.md §4). The caller owns the transaction."""

from collections.abc import Sequence
from datetime import date, datetime
from itertools import batched

from sqlalchemy import Connection, Engine, create_engine, func, literal_column, select, tuple_
from sqlalchemy.dialects.postgresql import insert

from finvest_market_data.domain.manifest import Manifest
from finvest_market_data.domain.models import Tick
from finvest_market_data.infrastructure.tables import crawl_runs, crawl_sessions, data_anomalies, ticks

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
