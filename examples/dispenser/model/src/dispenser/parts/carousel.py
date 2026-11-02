from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Cylinder,
    Location,
    Locations,
    Mode,
    Rectangle,
    Select,
    chamfer,
    extrude,
)
from cad.design.parts import part
from cad.library.features.planes import between
from cad.library.shapes import FacesOn, Printed, built, register

from dispenser.features import front_sector
from dispenser.master import SHAFT_RADIUS, DispenserMaster
from dispenser.models import FLAT_LENGTH, SHAFT_FLATS

SHAFT_BORE = "shaft bore"
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


@part
def carousel(m: DispenserMaster) -> Printed:
    bottom = Location(m.carousel_bottom)
    hub_bottom = m.shaft_top.offset(-FLAT_LENGTH)
    with BuildPart() as made:
        with Locations(bottom):
            Cylinder(m.rim_radius, m.pocket_height, align=BOTTOM)
        chamfer(made.edges(Select.LAST), m.fits.min_wall / 2)
        with Locations(bottom):
            Cylinder(m.pocket_reach, m.pocket_height, align=BOTTOM, mode=Mode.SUBTRACT)
        with Locations(bottom):
            Cylinder(m.pocket_start, m.pocket_height, align=BOTTOM)
            Cylinder(m.pocket_start - m.wall, m.pocket_height, align=BOTTOM, mode=Mode.SUBTRACT)
        with Locations(*[bottom * spot for spot in m.wall_spots]):
            Box(m.pocket_reach - m.pocket_start + m.wall, m.wall, m.pocket_height, align=BOTTOM)
        with Locations(Location(m.web_bottom)):
            Cylinder(m.pocket_start - m.wall, m.wall, align=BOTTOM)
        with Locations(Location(hub_bottom)):
            Cylinder(m.hub_radius, between(hub_bottom, m.web_bottom), align=BOTTOM)
        extrude(front_sector(m, bottom), amount=m.wall)
        with BuildSketch(Location(hub_bottom)) as d_bore:
            Circle(m.fits.printed(2 * SHAFT_RADIUS) / 2)
            Rectangle(m.fits.printed(SHAFT_FLATS), 2 * SHAFT_RADIUS + m.wall, mode=Mode.INTERSECT)
        rise = FLAT_LENGTH + m.fits.sliding
        extrude(d_bore.sketch, amount=rise, mode=Mode.SUBTRACT)
        register(SHAFT_BORE, hub_bottom, [FacesOn(plane=hub_bottom)])
    return Printed(
        name="carousel",
        pose=Location(),
        body=built(made),
        bed="-z",
        material=m.material,
        print_settings=m.print_settings,
    )
