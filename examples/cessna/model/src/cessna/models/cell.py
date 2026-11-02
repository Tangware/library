from build123d import Solid
from cad.library.bought.catalogue import STEEL, Rgb

DIAMETER = 14.5
LENGTH = 50.5
GRAMS = 23.0
LABEL: Rgb = STEEL  # Energizer's E91 product photos: a silver label


def solid() -> Solid:
    return Solid.make_cylinder(DIAMETER / 2, LENGTH)
