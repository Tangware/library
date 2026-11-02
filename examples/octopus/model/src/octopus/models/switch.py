from dataclasses import dataclass

from build123d import Axis, Location, Solid
from cad.library.bought.catalogue import Catalogue
from cad.library.bought.query import exactly, planes
from cad.library.bought.vendor import solids_of, vendor_reach
from cad.library.derived import derived

BEZEL_LENGTH = 21.0
BEZEL_WIDTH = 9.6
ABOVE_THE_PANEL = 6.2
CUTOUT_WIDTH = 6.8
CUTOUT_LENGTHS = ((0.75, 1.25, 19.2), (1.25, 2.0, 19.4), (2.0, 3.0, 19.6))
TERMINALS = 2
GRAMS_ESTIMATED = 2.0  # no maker weight: the STEP's volumes, PA66 body and actuator, brass tabs


def cutout_length(panel: float) -> float:
    (length,) = [
        length for thinnest, thickest, length in CUTOUT_LENGTHS if thinnest < panel <= thickest
    ]
    return length


@dataclass(frozen=True)
class Terminals:
    supply: Location
    load: Location


def tip_of(tab: Solid) -> Location:
    (tip,) = exactly(planes([tab], (-Axis.Z).direction), 1, "tab tips")
    return Location(tip.center())


@derived
def terminals(item: Catalogue) -> Terminals:
    seat = vendor_reach(item, Axis.Z) - ABOVE_THE_PANEL
    tabs = exactly(
        [solid for solid in solids_of(item) if seat > solid.bounding_box().max.Z],
        TERMINALS,
        "terminal tabs",
    )
    supply, load = sorted((tip_of(tab) for tab in tabs), key=lambda at: at.position.X)
    return Terminals(supply=supply, load=load)
