"""F-033 / PR-130: the app never places orders. Fails on a broker dependency or an order-placing endpoint/identifier."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DENY = {"ssi-fctrading", "ssi_fctrading", "vnstock", "dnse", "tcbs", "vps-api", "entrade", "pyvnd", "ccxt", "ib_insync", "alpaca"}
ORDER = re.compile(r"placeOrder|/orders?\b|/order/|newOrder|cancelOrder|/trading/")


def banned_deps(root: Path) -> list[str]:
    names = re.findall(r'^name = "([^"]+)"', (root / "uv.lock").read_text(), re.M)
    pkgs = json.loads((root / "apps/web/package-lock.json").read_text())["packages"]
    names += [k.rsplit("node_modules/", 1)[-1] for k in pkgs if k]
    return sorted({n for n in names if n.lower() in DENY or n.lower().replace("_", "-") in DENY})


def order_hits(root: Path) -> list[str]:
    hits = []
    for top in ("apps", "services", "packages"):
        for p in (root / top).rglob("*"):
            parts = p.parts
            if p.suffix not in (".py", ".ts", ".tsx") or "node_modules" in parts or ".venv" in parts:
                continue
            if "tests" in parts or "e2e" in parts or p.name.startswith("test_") or ".test." in p.name or ".spec." in p.name:
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
