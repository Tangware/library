from collections.abc import Sequence
from dataclasses import dataclass

from build123d import Axis, Solid

from cad.library.bought.catalogue import Catalogue
from cad.library.bought.query import cylinders, on_axis
from cad.library.bought.vendor import solids_of, vendor_reach
from cad.library.derived import derived
from cad.library.shapes import radius_of, round_faces


@dataclass(frozen=True)
class RingSizes:
    bore: float
    outside: float
    width: float


def inner_ring_of(solids: Sequence[Solid], bore: float) -> Solid:
    (inner,) = [solid for solid in solids if round_faces(solid, bore / 2)]
    return inner


def _turned(solids: Sequence[Solid]) -> list[float]:
    return [radius_of(f) for f in cylinders(solids, Axis.Z.direction) if on_axis(f)]


@derived
def ring_sizes(item: Catalogue) -> RingSizes:
    solids = solids_of(item)
    bore = 2 * min(_turned(solids))
    return RingSizes(
        bore=bore,
        outside=2 * max(_turned(solids)),
        width=vendor_reach(item, Axis.Z) + vendor_reach(item, -Axis.Z),
    )
