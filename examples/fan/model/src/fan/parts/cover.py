from build123d import Align, Axis, Box, BuildPart, Location, Locations, Plane, Select, fillet
from cad.design.parts import part
from cad.library.features.hardware import LIPS, screw_holes
from cad.library.provenance import step
from cad.library.shapes import Printed, built

from fan.features import grille
from fan.master import FanMaster
from fan.models import FAN_HUB

BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


@part
def cover(m: FanMaster) -> Printed:
    plate = m.facing_back(m.fan_middle, m.fan_back)
    with BuildPart() as made:
        with step("plate"), Locations(plate):
            Box(m.head_width, m.head_height, m.wall, align=BOTTOM)
        with step("rounded corners"):
            fillet(made.edges(Select.LAST).filter_by(Axis.Y), m.wall)
        with step("grille"):
            grille(m, plate, m.wall, FAN_HUB, m.fan_side / 2 - m.wall)
        with step("screw holes"):
            spots = [m.facing_back(at, m.fan_back) for at in m.fan_screws]
            screw_holes(Plane(spots[0]), spots, m.screw, m.wall, LIPS, fits=m.fits)
    return Printed(
        name="cover", pose=Location(), body=built(made), bed="+y", print_settings=m.print_settings
    )
