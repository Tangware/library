from build123d import Align, BuildPart, Cylinder, Location, Locations, fillet
from cad.design.parts import part
from cad.library.provenance import step
from cad.library.shapes import FacesOn, Printed, built, edges_on, register

from dispenser.master import DispenserMaster

SEAT = "seat"
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


@part
def lid(m: DispenserMaster) -> Printed:
    with BuildPart() as made:
        with step("cap"), Locations(Location(m.rim)):
            Cylinder(m.radius, m.wall, align=BOTTOM)
        with step("rounded top edge"):
            fillet(edges_on(built(made), m.rim.offset(m.wall)), m.fits.min_wall)
        with step("plug"), Locations(Location(m.plug_bottom)):
            Cylinder(m.plate_radius, m.wall, align=BOTTOM)
        with step("broken plug edge"):
            fillet(edges_on(built(made), m.plug_bottom), m.fits.min_wall)
        register(SEAT, m.rim, [FacesOn(plane=m.rim)])
    return Printed(
        name="lid",
        pose=Location(),
        body=built(made),
        bed="+z",
        material=m.material,
        print_settings=m.print_settings,
    )
