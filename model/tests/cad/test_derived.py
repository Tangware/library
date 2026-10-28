import pytest
from build123d import Box, BuildPart, Locations

from cad.library.derived import derived
from cad.library.shapes import Brep, built

SIDE_MM = 2.0


@derived
def cube() -> Brep:
    with BuildPart() as made:
        Box(SIDE_MM, SIDE_MM, SIDE_MM)
    return built(made)


def test_m3_a_part_is_the_same_wherever_its_builder_is_called() -> None:
    with BuildPart(), Locations((20, 0, 0), (40, 0, 0)):
        inside = cube()

    assert inside.volume == pytest.approx(SIDE_MM**3)
