from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Literal

from build123d import Axis, Compound, Location, Plane, Solid

from cad.standards import Carries, Converts, Draw, Rated, RatedTorque

type Rgb = tuple[float, float, float]
STEEL: Rgb = (0.55, 0.56, 0.58)
SOLDER_MASK_BLACK: Rgb = (0.05, 0.05, 0.06)
SOLDER_MASK_GREEN: Rgb = (0.0, 0.4, 0.15)
SOLDER_MASK_BLUE: Rgb = (0.05, 0.25, 0.6)
BLACK_PLASTIC: Rgb = (0.08, 0.08, 0.08)
NATURAL_NYLON: Rgb = (0.93, 0.91, 0.84)
TRIANGLES = 12000
EXACT_SIMPLIFY = 3
COARSE_SIMPLIFY = 7
USB_C = "USB-C"


@dataclass(frozen=True)
class Piece:
    name: str
    grams: float
    component: str
    solids: int = 1


@dataclass(frozen=True)
class PlugFace:
    into_the_socket: Axis
    across: Axis
    inserted: float
    leaving: Axis | None = None
    fronts: int = 1


@dataclass(frozen=True)
class Port:
    name: str
    instance: str
    mating: Axis
    across: Axis
    levels: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConnectionPoint:
    name: str
    at: Location
    source: str


@dataclass(frozen=True)
class Pins:
    radius: float
    along: Axis
    lines: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class Download:
    url: str
    sha256: str
    member: str | None = None


@dataclass(frozen=True)
class Bores:
    narrowest_radius: float
    widest_radius: float
    count: int


class Type(StrEnum):
    PART = "Part"
    CONSUMABLE = "Consumable"
    ACCESSORY = "Accessory"
    TOOL = "Tool"


@dataclass(frozen=True, kw_only=True)
class Bill:
    type: Type = Type.PART
    number: str = ""
    ships_with: str = ""


NO_BILL = Bill()


@dataclass(frozen=True, kw_only=True)
class Cleanup:
    centred: bool = False
    only: Literal["all", "case", "bare case", "horn"] = "all"
    keep_above: float | None = None
    trim_radius: float | None = None
    piece: Piece | None = None
    correct: Callable[[list[Solid]], list[Solid]] | None = None
    colour: Rgb | None = None
    paint: Rgb | None = None
    triangles: int = TRIANGLES
    simplify: int = EXACT_SIMPLIFY


@dataclass(frozen=True, kw_only=True)
class BoardKind:
    ports: tuple[Port, ...] = ()
    pins: tuple[Pins, ...] = ()
    parts_under_the_board: float = 0.0


@dataclass(frozen=True, kw_only=True)
class ServoKind:
    horn_radius: float
    spline_radius: float
    spline_faces: int


type Kind = BoardKind | ServoKind


@dataclass(frozen=True, kw_only=True)
class Catalogue:
    file: str
    grams: float
    frame: Plane | Bores | PlugFace = Plane.XY
    pieces: tuple[Piece, ...] = ()
    connection_points: tuple[ConnectionPoint, ...] = ()
    kind: Kind | None = None
    rating: Rated | None = None
    torque: RatedTorque | None = None
    draw: Draw | None = None
    carries: Carries | None = None
    converts: tuple[Converts, ...] = ()
    cleanup: Cleanup = Cleanup()
    bill: Bill = Bill()
    model: Callable[[], Solid | Compound] | None = None
    folder: Path | None = None
    download: Download | None = None
    shape: Path | Download | Callable[[], Solid | Compound] = field(init=False)

    def __post_init__(self) -> None:
        if self.model is None and self.folder is None and self.download is None:
            raise ValueError(f"{self.file} has no model, folder of maker STEP or download")
        step = None if self.folder is None else self.folder / f"{self.file}.step.gz"
        object.__setattr__(self, "shape", self.model or self.download or step)

    @property
    def board(self) -> BoardKind:
        if not isinstance(self.kind, BoardKind):
            raise TypeError(f"{self.file} has no board data")
        return self.kind
