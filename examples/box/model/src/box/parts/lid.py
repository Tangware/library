from build123d import Align, Axis, Box, BuildPart, Location, Locations, Select, fillet

from box.master import BoxMaster
from cad.design.parts import part
from cad.library.features.hardware import LIPS, screw_holes
from cad.library.provenance import step
from cad.library.shapes import Printed, built

BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


@part
def lid(m: BoxMaster) -> Printed:
    outside = m.outside
    with BuildPart() as made:
        with step("plate"), Locations(Location(m.rim) * outside.at):
            Box(outside.width, outside.depth, m.wall, align=BOTTOM)
        with step("rounded corners"):
            fillet(made.edges(Select.LAST).filter_by(Axis.Z), m.wall)
        with step("screw holes"):
            screw_holes(m.rim, m.lid_spots, m.lid_screw, m.wall, LIPS, fits=m.fits)
    return Printed(
        name="lid", pose=Location(), body=built(made), bed="+z", print_settings=m.print_settings
    )
