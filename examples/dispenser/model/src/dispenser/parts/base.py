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
    Plane,
    Pos,
    Rectangle,
    extrude,
    fillet,
)
from cad.design.parts import part
from cad.library.features.boards import insert_posts
from cad.library.features.hardware import INSERTS, insert_holes
from cad.library.features.planes import between
from cad.library.provenance import step
from cad.library.shapes import FacesOn, Printed, built, edges_on, register
from cad.library.turns import FACING_FRONT, UPSIDE_DOWN

from dispenser import models
from dispenser.features import front_sector
from dispenser.master import DispenserMaster

STEPPER_INSERTS = "stepper inserts"
RIM = "rim"
DRAWER_WAY = "drawer way"
LIGHT_HOLE = "light hole"
SENSOR_INSERTS = "sensor inserts"
PICO_INSERTS = "Pico inserts"
DRIVER_INSERTS = "driver inserts"
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)
FRONT = (Align.CENTER, Align.MAX, Align.MIN)
OUTWARD = (Align.CENTER, Align.CENTER, Align.MAX)


@part
def base(m: DispenserMaster) -> Printed:
    tall = between(m.plate_bottom, m.rim)
    below = between(m.plate_bottom, m.floor_under)
    above = between(m.floor_top, m.rim)
    opening = between(m.plate_top, m.drawer_top) + m.fits.sliding
    light = m.light_at
    with BuildPart() as made:
        with step("drum"), Locations(Location(m.plate_bottom)):
            Cylinder(m.radius, tall, align=BOTTOM)
        with step("broken outside edges"):
            ends = [*edges_on(built(made), m.plate_bottom), *edges_on(built(made), m.rim)]
            fillet(ends, m.fits.min_wall)
        with step("hollow under the floor"), Locations(Location(m.plate_bottom)):
            Cylinder(m.inside_radius, below, align=BOTTOM, mode=Mode.SUBTRACT)
        with step("hollow over the floor"), Locations(Location(m.floor_top)):
            Cylinder(m.inside_radius, above, align=BOTTOM, mode=Mode.SUBTRACT)
        with step("shaft hole"), Locations(Location(m.floor_under)):
            Cylinder(m.shaft_boss_radius, m.wall, align=BOTTOM, mode=Mode.SUBTRACT)
        with step("stepper bosses"), Locations(*[spot * Pos(Z=m.wall) for spot in m.stepper_spots]):
            Cylinder(m.screw_land, m.insert_depth - m.wall, align=BOTTOM)
        with step("stepper inserts"):
            under = [spot * UPSIDE_DOWN for spot in m.stepper_spots]
            insert_holes(
                Plane(under[0]), under, m.screw, STEPPER_INSERTS, fits=m.fits, stock=m.stock
            )
        with step("gate"):
            extrude(front_sector(m, Location(m.floor_under)), amount=m.wall, mode=Mode.SUBTRACT)
        with step("plate bosses"), Locations(*m.plate_spots):
            Cylinder(m.screw_land, between(m.plate_bosses, m.floor_under), align=BOTTOM)
        with step("plate inserts"):
            under = [spot * UPSIDE_DOWN for spot in m.plate_spots]
            insert_holes(Plane(under[0]), under, m.screw, INSERTS, fits=m.fits, stock=m.stock)
        with step("drawer guides"):
            with BuildSketch(Location(m.plate_top)) as guides:
                with Locations(*[Pos(X=x, Y=m.drawer_back) for x in (-m.guide_x, m.guide_x)]):
                    Rectangle(m.wall, m.radius, align=(Align.CENTER, Align.MAX))
                Circle(m.inside_radius + m.wall / 2, mode=Mode.INTERSECT)
            extrude(guides.sketch, amount=below - m.plate_thickness)
        with step("drawer opening"), Locations(Location(m.plate_top) * Pos(Y=m.drawer_back)):
            Box(
                m.drawer_width + 2 * m.fits.sliding,
                m.radius + m.drawer_back,
                opening,
                align=FRONT,
                mode=Mode.SUBTRACT,
            )
        register(DRAWER_WAY, m.drawer_way, [FacesOn(plane=m.drawer_top.offset(m.fits.sliding))])
        sleeve = m.flange_at + m.radius
        with step("light sleeve"), Locations(light * FACING_FRONT):
            Cylinder(m.light_band / 2, sleeve, align=OUTWARD)
        with step("light hole"), Locations(light * FACING_FRONT):
            hole = m.fits.printed(models.LED_BODY) / 2
            Cylinder(hole, sleeve, align=OUTWARD, mode=Mode.SUBTRACT)
            seat = Plane(light * Pos(Y=sleeve) * FACING_FRONT)
            register(LIGHT_HOLE, seat, [FacesOn(plane=-seat)])
        with step("sensor bosses"), Locations(*[spot * Pos(Z=m.wall) for spot in m.reed_spots]):
            Cylinder(m.screw_land, m.insert_depth - m.wall, align=BOTTOM)
        with step("sensor inserts"):
            under = [spot * UPSIDE_DOWN for spot in m.reed_spots]
            insert_holes(
                Plane(under[0]), under, m.screw, SENSOR_INSERTS, fits=m.fits, stock=m.stock
            )
        with step("Pico posts"):
            insert_posts(
                m.pico_mount, m.pico_at, m.floor_under, PICO_INSERTS, fits=m.fits, stock=m.stock
            )
        with step("driver posts"):
            insert_posts(
                m.driver_mount,
                m.driver_at,
                m.floor_under,
                DRIVER_INSERTS,
                fits=m.fits,
                stock=m.stock,
            )
        with step("USB opening"):
            keepout = m.usb_keepout.block
            with Locations(keepout.at * Pos(Z=-m.fits.sliding)):
                Box(
                    keepout.width + 2 * m.fits.sliding,
                    keepout.depth,
                    keepout.height + 2 * m.fits.sliding,
                    align=BOTTOM,
                    mode=Mode.SUBTRACT,
                )
        register(RIM, m.rim, [FacesOn(plane=m.rim)])
    return Printed(
        name="base",
        pose=Location(),
        body=built(made),
        bed="-z",
        material=m.material,
        print_settings=m.print_settings,
    )
