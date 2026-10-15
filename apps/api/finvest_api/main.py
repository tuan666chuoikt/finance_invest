import os
from functools import lru_cache
from importlib.metadata import version

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

app = FastAPI(title="finvest")


@lru_cache
def get_engine() -> Engine:
    url = os.environ.get("FINVEST_DATABASE_URL", "postgresql+psycopg://finvest:finvest@localhost:5432/finvest")
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 3})


@app.get("/api/health")
def health(engine: Engine = Depends(get_engine)):
    try:
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
    except Exception:  # any DB failure is 503; details stay out of the body (platform.md 1.3)
        return JSONResponse(
            status_code=503,
            content={"error": {"code": "DB_UNAVAILABLE", "message": "database unreachable", "details": {}}},
        )
    # rules_version stays null until F-001
    return {"status": "ok", "db": "ok", "version": version("finvest-api"), "rules_version": None}
