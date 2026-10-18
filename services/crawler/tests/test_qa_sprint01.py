# ruff: noqa: E501
"""QA (fi-be-tester) black-box checks for sprint 01, written against the backlog criteria, not the dev tests."""
import hashlib
import json
import subprocess
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
from finvest_crawler.archive import Archive
from finvest_crawler.fetch import Fetcher, SourceBlocked
from finvest_crawler.ratelimit import TokenBucket
from finvest_crawler.settings import Settings
from test_feed_ticks import FakeRepo, load, make, run, serve  # dev helpers (fixtures + in-memory repo)

D = date(2026, 10, 15)
ROOT = Path(__file__).resolve().parents[3]


def _oracle_checksum(payloads: dict[str, bytes]) -> str:
    """Independent of domain.checksum: rebuild canonical lines from the raw KBS JSON with plain json + datetime."""
    from datetime import datetime, timedelta
    lines = []
    for sym, raw in payloads.items():
        for r in json.loads(raw)["data"]:
            head, cc = r["t"].rsplit(":", 1)
            local = datetime.strptime(head, "%Y-%m-%d %H:%M:%S") + timedelta(milliseconds=int(cc) * 10)
            utc = local - timedelta(hours=7)  # Asia/Ho_Chi_Minh has no DST
            lines.append(f"{sym},{utc.strftime('%Y-%m-%dT%H:%M:%S.%f')}+00:00,{r['AVO']},{r['FMP']},{r['FV']},{r['LC']}\n")
    return "sha256:" + hashlib.sha256("".join(sorted(lines)).encode()).hexdigest()


# ---- F-017 ------------------------------------------------------------------------------------
def test_f017_checksum_matches_oracle_from_raw_archive(tmp_path):
    m, _, _ = run(tmp_path)
    raw = {s: load(s) for s in ("FPT", "VNM")}
    assert m.checksum == _oracle_checksum(raw)


def test_f017_shuffled_and_duplicated_payload_same_checksum(tmp_path):
    base, _, _ = run(tmp_path / "a")
    rows = json.loads(load("FPT"))
    shuffled = dict(rows, data=list(reversed(rows["data"])) + rows["data"][:5])  # reversed + 5 dup rows
    m, _, repo = run(tmp_path / "b", serve({"FPT": json.dumps(shuffled).encode()}))
    assert (m.checksum, m.rows) == (base.checksum, base.rows)
    assert repo.anomalies and repo.anomalies[0][1] == "duplicate_tick"


def test_f017_rerun_manifest_file_checksum_and_disk_unchanged(tmp_path):
    repo = FakeRepo()
    run(tmp_path, repo=repo)
    p = tmp_path / "raw/ticks/2026-10-15"
    snap = {f.name: f.read_bytes() for f in p.iterdir() if f.name != "_manifest.json"}
    c1 = json.loads((p / "_manifest.json").read_text())["checksum"]
    m2, f2, _ = run(tmp_path, repo=repo)
    assert f2.requests == 0 and m2.checksum == c1 and len(repo.ticks) == 100
    assert snap == {f.name: f.read_bytes() for f in p.iterdir() if f.name != "_manifest.json"}


def test_f017_each_skip_has_reason_and_is_listed_in_file(tmp_path):
    m, _, _ = run(tmp_path, serve({"VNM": lambda: httpx.Response(200, content=b"{\"data\":[{\"x\":1}]}")}))
    on_disk = json.loads((tmp_path / "raw/ticks/2026-10-15/_manifest.json").read_text())
    assert m.status == "partial" and on_disk["symbols_skipped"] == [{"symbol": "VNM", "reason": "payload_shape"}]
    assert on_disk["symbols_fetched"] == 1 and on_disk["universe"]["count"] == 2


def test_f017_past_date_manifest_is_written_not_silent(tmp_path):
    m, _, repo = run(tmp_path, d=date(2026, 10, 14))
    assert (m.status, m.reason, m.rows) == ("missed", "source_no_longer_serves", 0)
    assert (tmp_path / "raw/ticks/2026-10-14/_manifest.json").exists() and ("ticks", date(2026, 10, 14)) in repo.sessions


def test_f017_crashed_run_is_failed_not_absent(tmp_path):
    repo = FakeRepo()
    repo.upsert_ticks = MagicMock(side_effect=RuntimeError("db down"))
    with pytest.raises(RuntimeError):
        run(tmp_path, repo=repo)
    assert repo.runs[1][0] == "failed"


def test_f017_symbol_param_cannot_escape_archive(tmp_path):
    """Injection on the symbol param: --only is user input and becomes URL path + archive filename."""
    evil = "../../../../escaped"
    seen = []

    def h(req):
        seen.append(str(req.url))
        return httpx.Response(200, content=load("FPT"))

    try:
        run(tmp_path / "data", h, only=[evil])
    except Exception:
        pass
    outside = [p for p in tmp_path.rglob("escaped*")]
    assert not outside, f"archive write escaped data dir: {outside}; requests={seen}"


# ---- F-011 ------------------------------------------------------------------------------------
def test_f011_budget_never_exceeded_20_calls_at_2_per_s():
    t = [0.0]
    b = TokenBucket(2, clock=lambda: t[0], sleep=lambda s: t.__setitem__(0, t[0] + s))
    stamps = []
    for _ in range(20):
        b.take()
        stamps.append(t[0])
    assert all(y - x >= 0.5 - 1e-9 for x, y in zip(stamps, stamps[1:]))
    assert sum(1 for s in stamps if s < 1.0) <= 2


def test_f011_ua_identifies_personal_tool_and_failures_not_cached(tmp_path):
    seen = []

    def h(req):
        seen.append(req.headers["user-agent"])
        return httpx.Response(429)

    f = Fetcher(httpx.Client(transport=httpx.MockTransport(h)), {"kbs": TokenBucket(1000)}, Archive(tmp_path),
                Settings(_env_file=None).user_agent, sleep=lambda s: None)
    with pytest.raises(SourceBlocked):
        f.get("kbs", "https://kbbuddywts.kbsec.com.vn/x", feed="ticks", trading_date=D, name="a")
    assert len(seen) == 3 and "personal" in seen[0] and not list(tmp_path.rglob("*.json.gz"))


def test_f011_host_allowlist_blocks_other_hosts(tmp_path):
    f = make(tmp_path, serve())
    with pytest.raises(ValueError):
        f.get("kbs", "https://evil.example.com/x", feed="ticks", trading_date=D, name="a")


def test_f011_blocked_mid_run_skips_rest_and_reports(tmp_path):
    m, _, _ = run(tmp_path, serve({"FPT": lambda: httpx.Response(403)}))
    assert (m.status, m.reason) == ("blocked", "source_blocked") and ("FPT", "source_blocked") in m.symbols_skipped


# ---- F-020 / F-030 ----------------------------------------------------------------------------
def test_f020_data_dir_default_and_gitignored_and_retention_keep_all():
    s = Settings(_env_file=None)
    assert s.data_dir == Path("data") and s.retention_days is None
    # fresh repo with only the project's .gitignore (the worktree's data/ may be a symlink to the shared data dir)
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["git", "init", "-q", d], check=True)
        (Path(d) / ".gitignore").write_text((ROOT / ".gitignore").read_text())
        r = subprocess.run(["git", "check-ignore", "data/raw/ticks/2026-10-15/FPT.json.gz", "data/pg/x"],
                           cwd=d, check=False, capture_output=True)
    assert r.returncode == 0 and len(r.stdout.split()) == 2, r.stderr


def test_f030_compose_publishes_only_api_on_loopback():
    cmd = ["docker", "compose", "--profile", "tools", "config", "--format", "json"]
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "POSTGRES_PASSWORD": "x"}, check=False)
    if out.returncode:
        pytest.skip("docker compose unavailable")
    svc = json.loads(out.stdout)["services"]
    ports = {n: s.get("ports", []) for n, s in svc.items()}
    assert ports["db"] == [] and ports["crawler"] == []
    assert [(p["host_ip"], p["published"]) for p in ports["api"]] == [("127.0.0.1", "8000")]


def test_f030_make_crawl_takes_date():
    mk = (ROOT / "Makefile").read_text()
    assert "ticks --date $(DATE)" in mk and "DATE ?=" in mk


# ---- re-test after fixes (QA-BUG-2 / QA-BUG-3) -------------------------------------------------
EMPTY = b'{"data":[]}'


def test_qa_bug2_late_run_empty_tape_not_archived_and_not_replayed(tmp_path):
    m, _, _ = run(tmp_path, serve({"VNM": EMPTY}), today=date(2026, 10, 16))
    day = tmp_path / "raw/ticks/2026-10-15"
    # FPT probe proves the day is still served, so the empty VNM tape is no trades (FIX-ticks-probe)
    assert (m.status, m.reason, m.symbols_no_trades) == ("complete", None, ("VNM",))
    assert not list(day.glob("VNM*")), "empty tape must not land under the old date"
    m2, f2, _ = run(tmp_path, serve({"VNM": EMPTY}), today=date(2026, 10, 16))  # re-run: nothing frozen in archive
    assert f2.requests >= 1 and not list(day.glob("VNM*")) and m2.symbols_no_trades == ("VNM",)


def test_qa_bug3_universe_pinned_to_date_even_if_source_drifts(tmp_path):
    repo = FakeRepo()
    m1, _, _ = run(tmp_path, repo=repo)

    def drifted(req):
        if "getAll" in str(req.url):
            return httpx.Response(200, content=b'{"data":[{"symbol":"DSH","type":"STOCK"}]}')
        return serve()(req)

    m2, f2, _ = run(tmp_path, drifted, repo=repo)
    assert f2.requests == 0 and m2.universe_count == m1.universe_count and m2.checksum == m1.checksum
    on = json.loads((tmp_path / "raw/ticks/2026-10-15/_manifest.json").read_text())["universe"]
    assert on["count"] == m1.universe_count


def test_qa_bug3_killed_run_is_closed_next_time(tmp_path):
    repo = FakeRepo()
    repo.runs[99] = None  # crawl_runs row left unfinished by a killed run
    run(tmp_path, repo=repo)
    assert repo.runs[99][0] == "failed"
