from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from build123d import Compound, Location

from cad.library.bought.bearings import inner_ring_of, ring_sizes
from cad.library.bought.catalogue import Catalogue
from cad.library.bought.vendor import vendor_shape
from cad.library.fits import Fits
from cad.library.shapes import FACES, Brep, Part, Seat, flat_faces, round_faces, seat_of
from cad.standards import StaticLoad

INNER_RACE = "inner race"
INNER_RING = "inner ring"
OUTER_RACE = "outer race"


@dataclass(frozen=True)
class BearingSize:
    static_n: float
    da_max: float
    ra_max: float
    model: Catalogue

    @property
    def name(self) -> str:
        return self.model.bill.number

    @property
    def grams(self) -> float:
        return self.model.grams

    @property
    def bore(self) -> float:
        return ring_sizes(self.model).bore

    @property
    def outside(self) -> float:
        return ring_sizes(self.model).outside

    @property
    def width(self) -> float:
        return ring_sizes(self.model).width

    @property
    def between_races(self) -> float:
        return (self.bore + self.outside) / 4

    @property
    def inner_race_middle(self) -> float:
        return (self.bore / 2 + self.between_races) / 2

    @property
    def outer_race_middle(self) -> float:
        return (self.between_races + self.outside / 2) / 2


def shaft_seat_radius(bearing: BearingSize, *, fits: Fits) -> float:
    return bearing.bore / 2 - fits.bearing_seat


def housing_seat_radius(bearing: BearingSize, *, fits: Fits) -> float:
    return bearing.outside / 2 + fits.bearing_seat


class Role(Enum):
    LOCATES = "locates"
    FLOATS = "floats"
    CROSSED = "crossed"


class Race(Enum):
    INNER = "inner"
    OUTER = "outer"


def inner_ring(bearing: str) -> str:
    return f"{bearing} {INNER_RING}"


def both_rings(bearings: Sequence[str]) -> tuple[str, ...]:
    return (*bearings, *(inner_ring(bearing) for bearing in bearings))


@dataclass(kw_only=True)
class Bearing(Part):
    size: BearingSize
    role: Role
    axis: str
    ring: Race
    material: str = "steel"

    @property
    def label(self) -> str:
        z = self.size
        return f"bearing {z.name} ({z.bore:g} x {z.outside:g} x {z.width:g})"

    @property
    def grams(self) -> float:
        whole = vendor_shape(self.size.model).volume
        return self.size.grams * self.shape().volume / whole

    @property
    def catalogue(self) -> Catalogue | None:
        return self.size.model

    def rating(self, fits: Fits) -> StaticLoad:
        return StaticLoad(
            static_n=self.size.static_n,
            between_races=self.size.between_races,
            connectors=(FACES,),
        )

    def shape(self) -> Brep:
        solids = vendor_shape(self.size.model).solids()
        inner = inner_ring_of(solids, self.size.bore)
        match self.ring:
            case Race.INNER:
                return inner
            case Race.OUTER:
                return Compound([solid for solid in solids if solid is not inner])

    def published(self) -> dict[str, Seat]:
        shape = self.unposed()
        race, radius = (
            (INNER_RACE, self.size.bore / 2)
            if self.ring is Race.INNER
            else (OUTER_RACE, self.size.outside / 2)
        )
        ends = [*flat_faces(shape, 0.0), *flat_faces(shape, self.size.width)]
        middle = Location((0.0, 0.0, self.size.width / 2))
        return {
            race: seat_of(round_faces(shape, radius), middle),
            FACES: seat_of(ends, middle),
        }


@dataclass(frozen=True)
class BearingRings:
    outer: Bearing
    inner: Bearing

    @property
    def parts(self) -> list[Part]:
        return [self.outer, self.inner]

    def on(self, race: str) -> Bearing:
        return {INNER_RACE: self.inner, OUTER_RACE: self.outer}[race]


def bearing_rings(
    name: str, pose: Location, size: BearingSize, role: Role, axis: str
) -> BearingRings:
    return BearingRings(
        outer=Bearing(name=name, pose=pose, size=size, role=role, axis=axis, ring=Race.OUTER),
        inner=Bearing(
            name=inner_ring(name),
            pose=pose,
            size=size,
            role=role,
            axis=axis,
            ring=Race.INNER,
            ships_with=name,
        ),
    )
