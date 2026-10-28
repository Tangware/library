from dataclasses import dataclass

from build123d import Axis, Face, Location

from cad.library.bought.catalogue import Catalogue, ServoKind
from cad.library.bought.query import LENGTH_TOLERANCE, cylinders, exactly, on_axis
from cad.library.bought.vendor import Bought, solids_of
from cad.library.derived import derived
from cad.library.shapes import Outside, Seat, radius_of, seat_of

SPLINE = "spline"
CASE_SEAT = "case seat"


@dataclass(frozen=True)
class ServoModel:
    stall_nm: float
    seconds_per_60_deg: float
    armature_kg_m2: float
    friction_nm: float
    backlash_deg: float
    p_coefficient: int


@derived
def spline(item: Catalogue) -> list[Face]:
    if not isinstance(item.kind, ServoKind):
        raise ValueError(f"{item.file} has no spline")
    kind = item.kind
    return exactly(
        [
            f
            for f in cylinders(solids_of(item), Axis.Z.direction)
            if on_axis(f)
            and abs(radius_of(f) - kind.spline_radius) <= LENGTH_TOLERANCE
            and f.bounding_box().max.Z >= -LENGTH_TOLERANCE
        ],
        kind.spline_faces,
        "spline faces",
    )


@dataclass(kw_only=True)
class Servo(Bought):
    model: ServoModel
    stress_analysed: bool
    torque_limit_share: float = 1.0

    @property
    def drive(self) -> Axis:
        return Axis(self.pose)

    def published(self) -> dict[str, Seat]:
        return {
            SPLINE: seat_of(spline(self.item), Location()),
            CASE_SEAT: Outside(self.unposed()),
            **self.connectors,
        }
