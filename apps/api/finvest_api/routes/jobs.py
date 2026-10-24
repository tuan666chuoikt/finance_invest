from typing import Any, Literal

from fastapi import APIRouter, Depends
from finvest_crawler.settings import Settings
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.engine import Engine

from ..deps import get_engine, vn_iso
from ..errors import ApiError
from ..jobs import jobs as t
from ..jobs import runner

router = APIRouter(prefix="/api")


class JobIn(BaseModel):
    kind: Literal["crawl"]


class Job(BaseModel):
    id: int
    kind: str
    status: Literal["running", "done", "failed"]
    created_at: str
    finished_at: str | None
    progress: dict[str, Any] | None
    summary: dict[str, Any] | None
    error: dict[str, Any] | None


def _out(row) -> dict:
    d = {k: v for k, v in row._mapping.items() if k not in ("args", "log")}
    d["created_at"], d["finished_at"] = vn_iso(d["created_at"]), vn_iso(d["finished_at"])
    return d


def _get(engine: Engine, *where):
    with engine.connect() as c:
        return c.execute(select(t).where(*where).order_by(t.c.id.desc()).limit(1)).first()


@router.post("/jobs", response_model=Job, status_code=202)
def start_job(_: JobIn, engine: Engine = Depends(get_engine)):
    job_id = runner.start_crawl(engine, Settings())
    if job_id is None:
        run = _get(engine, t.c.kind == "crawl", t.c.status == "running")
        details = {"id": run.id, "started_at": vn_iso(run.created_at)} if run else {}
        raise ApiError("JOB_RUNNING", 409, "a crawl is already running", details)
    return _out(_get(engine, t.c.id == job_id))


@router.get("/jobs/current", response_model=Job)
def current_job(engine: Engine = Depends(get_engine)):
    row = _get(engine, t.c.kind == "crawl")
    if row is None:
        raise ApiError("NOT_FOUND", 404, "no crawl job has run yet", {})
    return _out(row)


@router.get("/jobs/{id}", response_model=Job)
def get_job(id: int, engine: Engine = Depends(get_engine)):
    row = _get(engine, t.c.id == id)
    if row is None:
        raise ApiError("NOT_FOUND", 404, f"unknown job {id}", {"id": id})
    return _out(row)
