from build123d import Align, BuildPart, Cylinder, Location, Locations, Plane, chamfer
from cad.design.parts import part
from cad.library.features.boards import insert_posts
from cad.library.features.hardware import counterbored_screws
from cad.library.provenance import step
from cad.library.shapes import FacesOn, Printed, built, edges_on, register
from cad.library.turns import UPSIDE_DOWN

from fan.master import FanMaster

FEET = "feet"
DRIVER_INSERTS = "driver inserts"
TAPE_SEAT = "tape seat"
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


@part
def floor(m: FanMaster) -> Printed:
    with BuildPart() as made:
        with step("plate"), Locations(Location(m.floor_bottom)):
            Cylinder(m.puck_radius, m.floor_thickness, align=BOTTOM)
        with step("broken bottom edge"):
            chamfer(edges_on(built(made), m.floor_bottom), m.fits.min_wall)
        with step("floor screws"):
            heads = [spot * UPSIDE_DOWN for spot in m.floor_spots]
            counterbored_screws(
                Plane(heads[0]),
                heads,
                m.screw,
                m.screw_sunk,
                m.floor_thickness,
                fits=m.fits,
            )
        with step("driver posts"):
            insert_posts(
                m.driver_mount, m.driver_at, m.floor_top, DRIVER_INSERTS, fits=m.fits, stock=m.stock
            )
        register(FEET, m.floor_bottom, [FacesOn(plane=-m.floor_bottom)])
        register(TAPE_SEAT, m.floor_top, [FacesOn(plane=m.floor_top)])
    return Printed(
        name="floor", pose=Location(), body=built(made), bed="-z", print_settings=m.print_settings
    )
