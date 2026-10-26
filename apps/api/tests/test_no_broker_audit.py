"""F-033 / PR-130: the app never places orders.

Fails on a broker dependency or an order-placing endpoint/identifier.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DENY = {"ssi-fctrading", "vnstock", "dnse", "tcbs", "vps-api", "entrade", "pyvnd", "ccxt", "ib-insync",
        "alpaca"}
ORDER = re.compile(r"placeOrder|/orders?\b|/order/|newOrder|cancelOrder|/trading/")


def norm(n: str) -> str:
    return re.sub(r"[-_.]+", "-", n.lower())  # PEP 503


def banned_deps(root: Path) -> list[str]:
    names = re.findall(r'^name = "([^"]+)"', (root / "uv.lock").read_text(), re.M)
    pkgs = json.loads((root / "apps/web/package-lock.json").read_text())["packages"]
    names += [k.rsplit("node_modules/", 1)[-1] for k in pkgs if k]
    return sorted({n for n in map(norm, names) if n in DENY})


def order_hits(root: Path) -> list[str]:
    hits = []
    for top in ("apps", "services", "packages"):
        for p in (root / top).rglob("*"):
            parts = p.parts
            if p.suffix not in (".py", ".ts", ".tsx") or "node_modules" in parts or ".venv" in parts:
                continue
            if {"tests", "e2e"} & set(parts) or p.name.startswith("test_"):
                continue
            if {"test", "spec"} & set(p.name.split(".")):
                continue
            for i, line in enumerate(p.read_text(errors="ignore").splitlines(), 1):
                if ORDER.search(line):
                    hits.append(f"{p.relative_to(root)}:{i}: {line.strip()[:100]}")
    return hits


def test_no_broker_dependency():
    assert banned_deps(ROOT) == []


def test_no_order_endpoint_in_source():
    assert order_hits(ROOT) == []


def test_audit_catches_banned_dependency(tmp_path):
    (tmp_path / "apps/web").mkdir(parents=True)
    (tmp_path / "uv.lock").write_text((ROOT / "uv.lock").read_text() + '\n[[package]]\nname = "vnstock"\n')
    (tmp_path / "apps/web/package-lock.json").write_text('{"packages": {"": {}, "node_modules/react": {}}}')
    assert banned_deps(tmp_path) == ["vnstock"]


def test_audit_catches_normalised_name(tmp_path):
    (tmp_path / "apps/web").mkdir(parents=True)
    (tmp_path / "uv.lock").write_text('[[package]]\nname = "ib-insync"\n')
    (tmp_path / "apps/web/package-lock.json").write_text('{"packages": {}}')
    assert banned_deps(tmp_path) == ["ib-insync"]


def test_audit_catches_order_call(tmp_path):
    (tmp_path / "apps/x").mkdir(parents=True)
    (tmp_path / "apps/x/a.ts").write_text("api.placeOrder(1)\n")
    assert len(order_hits(tmp_path)) == 1
