from build123d import Axis, Pos, Sphere

from cad.library.bought.catalogue import Catalogue
from cad.library.bought.vendor import vendor_reach

KNOB = Catalogue(file="made-up knob", grams=10.0, model=lambda: Pos(1, 2, 3) * Sphere(4))
AXES = (Axis.X, -Axis.X, Axis.Y, -Axis.Y, Axis.Z, -Axis.Z)


def test_a_maker_part_reaches_as_far_as_its_shape_along_and_across_its_axes() -> None:
    across = Axis((0, 0, 0), (1, 1, 0))
    reaches = [round(vendor_reach(KNOB, axis), 6) for axis in (*AXES, across)]

    assert reaches == [5, 3, 6, 2, 7, 1, round(3 / 2**0.5 + 4, 6)]
