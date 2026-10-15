import gzip
import json
from datetime import date

from finvest_crawler.archive import Archive

D = date(2026, 10, 16)


def test_roundtrip_exact_bytes(tmp_path):
    a = Archive(tmp_path)
    assert a.read("ticks", D, "FPT") is None
    p = a.write("ticks", D, "FPT", b'{"x": 1}\n')
    assert p == tmp_path / "ticks" / "2026-10-16" / "FPT.json.gz"
    assert gzip.decompress(p.read_bytes()) == b'{"x": 1}\n'
    assert a.read("ticks", D, "FPT") == b'{"x": 1}\n'
    assert not list(tmp_path.rglob("*.tmp"))


def test_manifest(tmp_path):
    p = Archive(tmp_path).write_manifest("ticks", D, {"b": 1, "a": 2})
    assert p.name == "_manifest.json"
    assert p.read_text() == json.dumps({"a": 2, "b": 1}, indent=2)
