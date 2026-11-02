from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    Convexity,
    Location,
    Locations,
    Select,
    chamfer,
    fillet,
)
from cad.design.parts import part
from cad.library.features.hardware import LIPS, screw_holes
from cad.library.shapes import Printed, built, edges_on

from box.master import BoxMaster

BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


@part
def lid(m: BoxMaster) -> Printed:
    outside = m.outside
    with BuildPart() as made:
        with Locations(Location(m.rim) * outside.at):
            Box(outside.width, outside.depth, m.wall, align=BOTTOM)
        fillet(made.edges(Select.LAST).filter_by(Axis.Z), m.wall)
        chamfer(edges_on(built(made), m.rim.offset(m.wall)), m.fits.min_wall)
        chamfer(edges_on(built(made), m.rim), m.wall_edge_break)
        screw_holes(m.rim, m.lid_spots, m.lid_screw, m.wall, LIPS, fits=m.fits)
        chamfer(made.edges(Select.NEW).filter_by(Convexity.CONVEX), m.wall_edge_break)
    return Printed(
        name="lid",
        pose=Location(),
        body=built(made),
        bed="+z",
        exterior=True,
        material=m.material,
        print_settings=m.print_settings,
    )
