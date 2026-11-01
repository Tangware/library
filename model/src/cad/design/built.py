import json
from pathlib import Path
from typing import TypedDict, cast

OUTPUTS = Path("build") / "out"


class BuiltPart(TypedDict):
    id: str
    mass_g: float


class Instance(TypedDict, total=False):
    id: str
    name: str
    part: str
    mass_g: float


class BuiltAssembly(TypedDict):
    instances: list[Instance]
    hardware: list[Instance]


class Line(TypedDict):
    kind: str
    qty: int
    unit_price: float


class Manifest(TypedDict):
    parts: list[BuiltPart]
    assemblies: list[BuiltAssembly]
    bom: list[Line]


def output(name: str) -> Path:
    return OUTPUTS / name


def manifest() -> Manifest:
    return cast("Manifest", json.loads(output("manifest.json").read_text()))
