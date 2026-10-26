from dataclasses import dataclass
from enum import Enum

from build123d import Axis, Location

from cad.library.shapes import TEETH, Part, Seat


class Kind(Enum):
    RIGID = "rigid"
    REVOLUTE = "revolute"
    PRISMATIC = "prismatic"
    BALL = "ball"
    GEAR = "gear"
    CONTACT = "contact"


TURNING = (Kind.REVOLUTE, Kind.BALL)
MOVING = (*TURNING, Kind.PRISMATIC)


@dataclass(frozen=True)
class JointRange:
    low: float
    high: float

    @property
    def mirrored(self) -> JointRange:
        return JointRange(low=-self.high, high=-self.low)


def weighted(coefficients: dict[str, float], angles: dict[str, float]) -> float:
    return sum(weight * angles[joint] for joint, weight in coefficients.items())


@dataclass(frozen=True)
class JointRelation:
    coefficients: dict[str, float]
    span: JointRange

    def value(self, angles: dict[str, float]) -> float:
        return weighted(self.coefficients, angles)


type Reference = Part | str
PIECE_MARK = " #"


def copy_keys(name: str, copies: int) -> list[str]:
    return [name] if copies == 1 else [f"{name}{PIECE_MARK}{n}" for n in range(1, copies + 1)]


def part_name(geom: str) -> str:
    return geom.partition(PIECE_MARK)[0]


def joined(reference: Reference) -> Part:
    if isinstance(reference, str):
        raise TypeError(f"{reference} is not joined")
    return reference


def named(reference: Reference) -> str:
    return reference if isinstance(reference, str) else reference.name


@dataclass(frozen=True)
class Connector:
    part: Reference
    name: str
    placing: Reference | Location | None = None

    @property
    def seat(self) -> Seat:
        part = joined(self.part)
        seat = part.connector(self.name)
        if self.placing is None or not seat.instances:
            return seat
        at = self.placing if isinstance(self.placing, Location) else joined(self.placing).pose
        found = [each for each in seat.instances if part.pose * each.frame == at]
        if len(found) != 1:
            raise ValueError(f"{part.name} has {len(found)} {self.name} at {at}")
        (instance,) = found
        return instance

    @property
    def frame(self) -> Location:
        return joined(self.part).pose * self.seat.frame


@dataclass(frozen=True, eq=False)
class Mate:
    name: str
    kind: Kind
    child: Connector
    parent: Connector
    at: Location | None = None
    closes: bool = False
    servo: Reference | None = None
    fasteners: tuple[Reference, ...] = ()
    limits: JointRange | None = None
    approach: Axis | None = None

    def __post_init__(self) -> None:
        if self.kind in MOVING and self.at is None:
            raise ValueError(f"{self.name} is {self.kind.value} and carries no frame")
        if self.kind not in MOVING and self.at is not None:
            raise ValueError(f"{self.name} is {self.kind.value} and sits at its child's pose")

    @property
    def child_part(self) -> Part:
        return joined(self.child.part)

    @property
    def parent_part(self) -> Part:
        return joined(self.parent.part)

    @property
    def frame(self) -> Location:
        return self.child_part.pose if self.at is None else self.at

    @property
    def axis(self) -> Axis:
        return Axis(self.frame)


def meshing(gear: Reference, pinion: Reference) -> Mate:
    teeth = (Connector(gear, TEETH), Connector(pinion, TEETH))
    return Mate(f"{named(gear)} on {named(pinion)}", Kind.GEAR, *teeth, closes=True)
