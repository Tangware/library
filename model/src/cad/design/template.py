import json
import os
import re
import subprocess
import sys
import tomllib
from importlib.metadata import distribution
from pathlib import Path
from urllib.parse import unquote, urlparse

from cad.design.package import MODEL, package_name

TEMPLATE = Path(__file__).parent / "template"
SUFFIX = ".tmpl"
PACKAGE = "__package__"
TOOLING = [f"{MODEL}/ruff.toml", f"{MODEL}/.importlinter"]
HOOKS = ".githooks"
HOOK = f"{HOOKS}/pre-commit"
GENERATED = [f"{MODEL}/sgconfig.yml", HOOK]
HOOKS_PATH = "core.hooksPath"
LIBRARY = "tangware"
LINT = Path(__file__).resolve().parents[1] / "lint"
LINKS = {
    f"{MODEL}/ruff.toml": (("extend",), "{{lint}}", "/ruff.toml"),
    f"{MODEL}/pyproject.toml": (("tool", "uv", "sources", LIBRARY, "path"), "{{library}}", ""),
}


def package_of(name: str) -> str:
    package = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    if not package or package[0].isdigit():
        raise ValueError(f"{name} makes no Python package name")
    return package


def _relative(path: Path, where: Path) -> str:
    return Path(os.path.relpath(path, (where / MODEL).resolve())).as_posix()


def _installed() -> dict[str, object]:
    found: dict[str, object] = json.loads(
        distribution(LIBRARY).read_text("direct_url.json") or "{}"
    )
    return found


def _library(where: Path) -> str:
    installed = _installed()
    if "dir_info" not in installed:
        return ""
    return _relative(Path(unquote(urlparse(str(installed["url"])).path)), where)


def _lint(where: Path) -> str:
    if _library(where):
        return _relative(LINT, where)
    return (Path(".venv") / LINT.relative_to(Path(sys.prefix).resolve())).as_posix()


def _source(where: Path) -> str:
    if library := _library(where):
        return f'{LIBRARY} = {{ path = "{library}", editable = true }}'
    match _installed():
        case {"url": url, "vcs_info": {"commit_id": commit}, "subdirectory": within}:
            return f'{LIBRARY} = {{ git = "{url}", subdirectory = "{within}", rev = "{commit}" }}'
        case {"url": url, "vcs_info": {"commit_id": commit}}:
            return f'{LIBRARY} = {{ git = "{url}", rev = "{commit}" }}'
    return ""


def _links(where: Path) -> dict[str, str]:
    return {
        "{{lint}}": _lint(where),
        "{{library}}": _library(where),
        "{{source}}": _source(where),
        "{{version}}": distribution(LIBRARY).version,
    }


def _rendered(where: Path, values: dict[str, str], relative: str) -> str:
    text = (TEMPLATE / f"{relative}{SUFFIX}").read_text()
    for key, value in {**values, **_links(where)}.items():
        text = text.replace(key, value)
    return text


def _target(where: Path, values: dict[str, str], relative: str) -> Path:
    return where / relative.replace(PACKAGE, values["{{package}}"])


def _written(where: Path, values: dict[str, str], templates: list[str]) -> None:
    for relative in templates:
        target = _target(where, values, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_rendered(where, values, relative))


def scaffold(where: Path, name: str) -> None:
    if where.exists() and any(where.iterdir()):
        raise FileExistsError(f"{where} is not empty")
    templates = [
        source.relative_to(TEMPLATE).as_posix().removesuffix(SUFFIX)
        for source in sorted(TEMPLATE.rglob(f"*{SUFFIX}"))
    ]
    _written(where, {"{{name}}": name, "{{package}}": package_of(name)}, templates)
    inside = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],  # noqa: S607
        cwd=where,
        capture_output=True,
        check=False,
    )
    if inside.returncode:
        subprocess.run(["git", "init", "--quiet"], cwd=where, check=True)  # noqa: S607
    _hooked(where)


def _git(where: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        cwd=where,
        capture_output=True,
        text=True,
        check=False,
    )


def _hooked(where: Path) -> None:
    (where / HOOK).chmod(0o755)
    hooks = _git(where, "rev-parse", "--show-prefix").stdout.strip() + HOOKS
    current = _git(where, "config", HOOKS_PATH).stdout.strip()
    if current and current != hooks:
        print(f"{HOOKS_PATH} is {current}, so git does not run {where / HOOK}")
        return
    _git(where, "config", HOOKS_PATH, hooks)


def _relinked(where: Path) -> None:
    links = _links(where)
    for relative, (keys, link, suffix) in LINKS.items():
        target = where / relative
        text = target.read_text()
        found: object = tomllib.loads(text)
        for name in keys:
            if not isinstance(found, dict) or name not in found:
                break
            found = found[name]
        else:
            if links[link]:
                target.write_text(text.replace(f'"{found}"', f'"{links[link]}{suffix}"', 1))


def upgrade(where: Path) -> list[Path]:
    values = {"{{package}}": package_name(where)}
    _written(where, values, [each for each in TOOLING if not _target(where, values, each).exists()])
    _written(where, values, GENERATED)
    _relinked(where)
    _hooked(where)
    return [
        _target(where, values, each)
        for each in TOOLING
        if _target(where, values, each).read_text() != _rendered(where, values, each)
    ]
