from collections.abc import Sequence
from dataclasses import dataclass

from build123d import Axis, CenterOf, Compound, Location, Plane, Solid
from cad.library.bought.catalogue import Catalogue
from cad.library.bought.query import LENGTH_TOLERANCE, cylinders, exactly, planes
from cad.library.bought.vendor import placed_solids, vendor_extent
from cad.library.derived import derived
from cad.library.shapes import radius_of

LENGTH = 56.8
GRAMS_ESTIMATED = 11.76
LEADS = 2
LAYERS = 2


def beyond_the_end(solid: Solid) -> bool:
    return solid.bounding_box().max.X <= -LENGTH / 2 + LENGTH_TOLERANCE


def without_leads(solids: list[Solid]) -> Sequence[Solid | None]:
    return [None if beyond_the_end(solid) else solid for solid in solids]


@dataclass(frozen=True)
class Leads:
    out: Location
    diameter: float


@derived
def leads(item: Catalogue) -> Leads:
    if not isinstance(item.frame, Plane):
        raise TypeError(f"{item.file} is placed by a query, not a plane")
    framing = item.frame.location.inverse()
    solids = [solid for solid, _, _ in placed_solids(item.shape, None, detailed=False)]
    wires = [solid for solid in solids if beyond_the_end(solid)]
    body = Compound([framing * solid for solid in solids if not beyond_the_end(solid)])
    centring = Location(vendor_extent(item).min) * Location(body.bounding_box().min).inverse()
    ends = exactly(planes(wires, Axis.X.direction), LEADS * LAYERS, "lead end faces")
    out = Compound(ends).center(CenterOf.BOUNDING_BOX)
    outside = max(radius_of(face) for face in cylinders(wires, Axis.X.direction))
    return Leads(out=centring * framing * Location(out), diameter=2 * outside)
