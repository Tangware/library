from build123d import Align, BuildPart, Cylinder, Location, Locations, Plane, chamfer
from cad.design.parts import part
from cad.library.features.hardware import counterbored_screws
from cad.library.provenance import step
from cad.library.shapes import Printed, built, edges_on
from cad.library.turns import ALONG_X

from pantilt.master import ProductMaster

BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


@part
def cap(m: ProductMaster) -> Printed:
    rim = Location((m.drum_rim, 0, m.tilt_height)) * ALONG_X
    with BuildPart() as made:
        with step("disc"), Locations(rim):
            Cylinder(m.radius, m.screw_plate, align=BOTTOM)
        with step("edge break"):
            chamfer(edges_on(built(made), Plane(rim).offset(m.screw_plate)), m.fits.min_wall)
        with step("screws"):
            counterbored_screws(
                Plane(rim),
                m.cap_screws,
                m.screw,
                m.screw_plate - m.wall,
                m.screw_plate,
                fits=m.fits,
            )
    return Printed(
        name="cap",
        pose=Location(),
        body=built(made),
        bed="+x",
        material="PAHT-CF black",
        print_settings=m.print_settings,
    )
