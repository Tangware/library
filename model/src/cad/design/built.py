import json
from pathlib import Path
from typing import Any

OUTPUTS = Path("build") / "out"


def output(name: str) -> Path:
    return OUTPUTS / name


def manifest() -> dict[str, Any]:
    return json.loads(output("manifest.json").read_text())
