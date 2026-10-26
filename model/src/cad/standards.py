from dataclasses import dataclass
from enum import Enum
from typing import ClassVar

type Point = tuple[float, float, float]


@dataclass(frozen=True, kw_only=True)
class Rated:
    check: str
    body_solved: ClassVar[bool] = False
    connectors: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class StaticLoad(Rated):
    check: str = "ISO 76 static load"
    static_n: float
    between_races: float


@dataclass(frozen=True, kw_only=True)
class ToothRoot(Rated):
    check: str = "VDI 2736 tooth root"
    body_solved: ClassVar[bool] = True
    teeth: int
    module: float
    width: float
    pressure_deg: float
    dedendum: float
    root_fillet: float
    plastic: str


@dataclass(frozen=True, kw_only=True)
class RodEndLoad(Rated):
    check: str = "rod end static load"
    tensile_short_n: float
    tensile_long_n: float
    radial_short_n: float
    radial_long_n: float
    shank: Point


class Direction(Enum):
    ALONG = "along its axis"
    ACROSS = "across its axis"
    ANY = "in any direction"


@dataclass(frozen=True, kw_only=True)
class RatedForce(Rated):
    rated_n: float
    direction: Direction


@dataclass(frozen=True, kw_only=True)
class ScrewStrength(Rated):
    check: str = "screw strength"
    diameter: float
    pitch: float
    yield_mpa: float


@dataclass(frozen=True, kw_only=True)
class NutProof(Rated):
    check: str = "ISO 3506-2 nut proof load"
    diameter: float
    pitch: float
    proof_mpa: float


@dataclass(frozen=True, kw_only=True)
class RoundSection:
    outside: float
    bore: float = 0.0


@dataclass(frozen=True, kw_only=True)
class HexSection:
    across_flats: float


@dataclass(frozen=True, kw_only=True)
class ThreadSection:
    diameter: float
    pitch: float


@dataclass(frozen=True, kw_only=True)
class EulerStrut(Rated):
    check: str = "Euler buckling"
    body_solved: ClassVar[bool] = True
    length: float
    modulus_mpa: float
    section: RoundSection | HexSection | ThreadSection


@dataclass(frozen=True, kw_only=True)
class RatedTorque:
    nm: float
    source: str


@dataclass(frozen=True, kw_only=True)
class Draw:
    volts: float
    typical_a: float
    worst_a: float
    source: str


@dataclass(frozen=True, kw_only=True)
class Carries:
    amps: float
    source: str


@dataclass(frozen=True, kw_only=True)
class Converts:
    port: str
    volts: float
    efficiency: float
    amps: float
    source: str
