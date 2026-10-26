import argparse
import sys
from collections.abc import Callable
from dataclasses import dataclass
from importlib.metadata import entry_points
from pathlib import Path

from cad.design.template import scaffold, upgrade

COMMANDS = "cad.commands"


@dataclass(frozen=True)
class Command:
    help: str
    arguments: Callable[[argparse.ArgumentParser], None]
    run: Callable[[argparse.Namespace], int]


def _new_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("dir", type=Path)
    parser.add_argument("--name", required=True)


def _new(given: argparse.Namespace) -> int:
    scaffold(given.dir, given.name)
    print(given.dir)
    return 0


def repo_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("repo", type=Path)


def _upgrade(given: argparse.Namespace) -> int:
    for kept in upgrade(given.repo):
        print(f"kept, differs from the template: {kept}")
    print(given.repo)
    return 0


OPEN = {
    "new": Command("scaffold a design repo", _new_arguments, _new),
    "upgrade": Command(
        "write a design repo's missing tooling files and its library path; list the files"
        " that differ from the current template",
        repo_argument,
        _upgrade,
    ),
}


def main(argv: list[str] | None = None) -> int:
    added: dict[str, Command] = {each.name: each.load() for each in entry_points(group=COMMANDS)}
    commands = {**OPEN, **added}
    parser = argparse.ArgumentParser(prog="cad")
    chosen = parser.add_subparsers(dest="command", required=True)
    for name, command in commands.items():
        command.arguments(chosen.add_parser(name, help=command.help))
    given = parser.parse_args(argv)
    return commands[given.command].run(given)


if __name__ == "__main__":
    sys.exit(main())
