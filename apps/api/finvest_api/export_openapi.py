"""Export the API schema: `python -m finvest_api.export_openapi [--check]`."""
import json
import sys
from pathlib import Path

from .main import app

PATH = Path(__file__).resolve().parents[3] / "packages" / "contracts" / "openapi.json"


def render() -> str:
    return json.dumps(app.openapi(), sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> int:
    new = render()
    if "--check" in argv:
        old = PATH.read_text(encoding="utf-8") if PATH.exists() else ""
        if old != new:
            print(f"{PATH} is stale ({len(old)} vs {len(new)} chars): run `make contracts`")
            return 1
        return 0
    PATH.write_text(new, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
