from build123d import Axis, Plane, Pos, Sphere

from cad.library.bought.catalogue import Catalogue
from cad.library.bought.vendor import vendor_reach
from cad.library.features.planes import between, normal_to

KNOB_CENTRE = Pos(1, 2, 3)
KNOB_RADIUS = 4
KNOB = Catalogue(file="made-up knob", grams=10.0, model=lambda: KNOB_CENTRE * Sphere(KNOB_RADIUS))
AXES = (Axis.X, -Axis.X, Axis.Y, -Axis.Y, Axis.Z, -Axis.Z)


def test_a_maker_part_reaches_as_far_as_its_shape_along_and_across_its_axes() -> None:
    across = Axis((0, 0, 0), (1, 1, 0))
    reaches = [round(vendor_reach(KNOB, axis), 6) for axis in (*AXES, across)]

    centre_across = between(normal_to(across.direction, through=Pos()), Plane(KNOB_CENTRE))
    assert reaches == [5, 3, 6, 2, 7, 1, round(centre_across + KNOB_RADIUS, 6)]
