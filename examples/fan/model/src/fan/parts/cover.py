from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    Location,
    Locations,
    Plane,
    Select,
    chamfer,
    fillet,
)
from cad.design.parts import part
from cad.library.features.hardware import LIPS, screw_holes
from cad.library.shapes import Printed, built, edges_on

from fan.features import grille
from fan.master import FanMaster
from fan.models import FAN_HUB

BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


@part
def cover(m: FanMaster) -> Printed:
    plate = m.facing_back(m.fan_middle, m.fan_back)
    with BuildPart() as made:
        with Locations(plate):
            Box(m.head_width, m.head_height, m.wall, align=BOTTOM)
        fillet(made.edges(Select.LAST).filter_by(Axis.Y), m.wall)
        chamfer(edges_on(built(made), Plane(plate).offset(m.wall)), m.fits.min_wall)
        grille(m, plate, m.wall, FAN_HUB, m.fan_side / 2 - m.wall)
        spots = [m.facing_back(at, m.fan_back) for at in m.fan_screws]
        screw_holes(Plane(spots[0]), spots, m.screw, m.wall, LIPS, fits=m.fits)
    return Printed(
        name="cover",
        pose=Location(),
        body=built(made),
        bed="+y",
        exterior=True,
        material=m.material,
        print_settings=m.print_settings,
    )
