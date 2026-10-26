import subprocess
import sys
from pathlib import Path

EXAMPLE = Path(__file__).parents[2] / "examples" / "box"


def cad(*args: str | Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "cad.cli", *map(str, args)],
        capture_output=True,
        text=True,
        check=False,
    )
