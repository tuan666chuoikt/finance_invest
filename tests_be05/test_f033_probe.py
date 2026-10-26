"""F-033 tester probes on the audit's blind spots (imports the audit module, does not edit it)."""
import importlib.util
import pathlib

p = pathlib.Path(__file__).resolve().parents[1] / "apps/api/tests/test_no_broker_audit.py"
spec = importlib.util.spec_from_file_location("audit", p)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def probe(tmp_path, name, body):
    (tmp_path / "apps/x").mkdir(parents=True)
    (tmp_path / "apps/x" / name).write_text(body)
    return audit.order_hits(tmp_path)


def test_covered_suffixes(tmp_path):
    assert probe(tmp_path, "a.py", "requests.post(base + '/orders', json=o)\n")


import pytest


@pytest.mark.xfail(strict=True, reason="B-05-3 audit scans only .py/.ts/.tsx")
def test_js_mjs_jsx_blind_spot(tmp_path):  # BUG B-05-3 (low): only .py/.ts/.tsx scanned
    hits = probe(tmp_path, "a.mjs", "fetch(url + '/order/new'); client.placeOrder(1)\n")
    assert hits, "order call in .mjs not detected"


def test_current_tree_clean():
    assert audit.banned_deps(audit.ROOT) == [] and audit.order_hits(audit.ROOT) == []
