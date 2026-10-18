from importlib.metadata import version

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.engine import Engine

from . import errors
from .deps import get_engine
from .routes import bars, symbols

app = FastAPI(title="finvest")
errors.install(app)
app.include_router(symbols.router)
app.include_router(bars.router)


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
