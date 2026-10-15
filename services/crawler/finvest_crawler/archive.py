import gzip
import json
import os
from datetime import date
from pathlib import Path


class Archive:
    """Raw response archive: root/<feed>/<YYYY-MM-DD>/<name>.json.gz. Never deletes (platform.md 4)."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def path(self, feed: str, trading_date: date, name: str) -> Path:
        return self.root / feed / trading_date.isoformat() / f"{name}.json.gz"

    def read(self, feed: str, trading_date: date, name: str) -> bytes | None:
        p = self.path(feed, trading_date, name)
        return gzip.decompress(p.read_bytes()) if p.exists() else None

    def write(self, feed: str, trading_date: date, name: str, payload: bytes) -> Path:
        return self._atomic(self.path(feed, trading_date, name), gzip.compress(payload))

    def write_manifest(self, feed: str, trading_date: date, manifest: dict) -> Path:
        p = self.path(feed, trading_date, "_manifest").with_suffix("").with_suffix(".json")
        return self._atomic(p, json.dumps(manifest, indent=2, sort_keys=True).encode())

    @staticmethod
    def _atomic(p: Path, data: bytes) -> Path:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_name(p.name + ".tmp")
        tmp.write_bytes(data)
        os.replace(tmp, p)
        return p
