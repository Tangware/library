from build123d import Solid

DIAMETER = 14.5
LENGTH = 50.5
GRAMS = 23.0


def solid() -> Solid:
    return Solid.make_cylinder(DIAMETER / 2, LENGTH)
