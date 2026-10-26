import subprocess
import sys
import tomllib
from importlib.metadata import version
from pathlib import Path

from design_run import cad

PRODUCT = "Desk Tidy"
UV = ("uv", "--offline")


def test_cad_new_scaffolds_a_design_clean_under_the_library_lint_rules_once_moved_and_upgraded(
    tmp_path: Path,
) -> None:
    cad("new", tmp_path / "tidy", "--name", PRODUCT)
    moved = tmp_path / "deeper" / "still" / "tidy"
    moved.parent.mkdir(parents=True)
    (tmp_path / "tidy").rename(moved)
    cad("upgrade", moved)
    model = moved / "model"

    linted = [
        subprocess.run(  # noqa: S603
            [sys.executable, "-m", "ruff", *command, "--no-cache", "."],
            cwd=model,
            capture_output=True,
            text=True,
            check=False,
        )
        for command in (["check"], ["format", "--check"])
    ]

    assert [run.returncode for run in linted] == [0, 0], [run.stdout for run in linted]


def test_cad_upgrade_restores_the_tooling_files_and_leaves_the_design_alone(
    tmp_path: Path,
) -> None:
    cad("new", tmp_path / "tidy", "--name", PRODUCT)
    model = tmp_path / "tidy" / "model"
    ruff = model / "ruff.toml"
    written = ruff.read_text()
    ruff.unlink()
    plate = model / "src" / "desk_tidy" / "parts" / "plate.py"
    plate.write_text(plate.read_text() + "\nEDITED = True\n")
    designed = plate.read_text()

    upgraded = cad("upgrade", tmp_path / "tidy")

    assert (upgraded.returncode, ruff.read_text(), plate.read_text()) == (0, written, designed)


def test_cad_new_links_the_library_by_a_path_relative_to_the_design(tmp_path: Path) -> None:
    cad("new", tmp_path / "tidy", "--name", PRODUCT)
    model = tmp_path / "tidy" / "model"
    ruff = tomllib.loads((model / "ruff.toml").read_text())["extend"]
    project = tomllib.loads((model / "pyproject.toml").read_text())
    source = project["tool"]["uv"]["sources"]["tangware"]["path"]

    assert [Path(each).is_absolute() for each in (ruff, source)] == [False, False]


def test_cad_new_depends_on_the_release_of_the_library_that_made_it(tmp_path: Path) -> None:
    cad("new", tmp_path / "tidy", "--name", PRODUCT)
    project = tomllib.loads((tmp_path / "tidy" / "model" / "pyproject.toml").read_text())

    assert project["project"]["dependencies"] == [f"tangware=={version('tangware')}"]


def test_cad_upgrade_restores_the_pre_commit_hook_that_refuses_a_commit_breaking_the_lint(
    tmp_path: Path,
) -> None:
    cad("new", tmp_path / "tidy", "--name", PRODUCT)
    (tmp_path / "tidy" / ".githooks" / "pre-commit").unlink()
    cad("upgrade", tmp_path / "tidy")
    plate = tmp_path / "tidy" / "model" / "src" / "desk_tidy" / "parts" / "plate.py"
    plate.write_text(f"import os\n{plate.read_text()}")
    git = ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com"]
    subprocess.run([*git, "add", "-A"], cwd=tmp_path / "tidy", check=True)  # noqa: S603

    committed = subprocess.run(  # noqa: S603
        [*git, "commit", "-m", "an unused import"],
        cwd=tmp_path / "tidy",
        capture_output=True,
        text=True,
        check=False,
    )

    assert (committed.returncode, "F401" in committed.stdout + committed.stderr) == (1, True)


def _run(*command: str | Path, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [str(each) for each in command], cwd=cwd, capture_output=True, text=True, check=False
    )


def test_cad_new_from_a_wheel_install_links_the_lint_rules_of_the_design_s_own_environment(
    tmp_path: Path,
) -> None:
    library = Path(__file__).parents[2]
    dist = tmp_path / "dist"
    _run(*UV, "build", "--wheel", "--out-dir", dist, library, cwd=tmp_path)
    _run(*UV, "venv", "--quiet", tmp_path / "venv", cwd=tmp_path)
    tools = tmp_path / "venv" / "bin"
    (wheel,) = dist.glob("*.whl")
    _run(*UV, "pip", "install", "--quiet", "--python", tools / "python", wheel, cwd=tmp_path)
    _run(tools / "cad", "new", tmp_path / "tidy", "--name", PRODUCT, cwd=tmp_path)
    (tmp_path / "venv").rename(tmp_path / "gone")
    model = tmp_path / "tidy" / "model"

    linted = [
        _run(*UV, "run", "--quiet", "--find-links", dist, *command, cwd=model)
        for command in (("ast-grep", "scan"), ("ruff", "check", "--no-cache", "."))
    ]

    assert [run.returncode for run in linted] == [0, 0], [run.stderr for run in linted]
