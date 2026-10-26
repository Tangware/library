from build123d import Align, Box, BuildPart, Cylinder, Location, Locations, Mode, Plane, Pos, fillet
from cad.design.parts import part
from cad.library.features.hardware import INSERTS, insert_holes
from cad.library.features.planes import between, foot_on
from cad.library.provenance import step
from cad.library.shapes import FacesOn, Printed, built, edges_on, register
from cad.library.turns import UPSIDE_DOWN

from fan.master import FanMaster

STEPPER_INSERTS = "stepper inserts"
BUTTON_HOLE = "button hole"
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)
BUTTON_CUTOUT = 16.0  # Adafruit 1445: Ø16 panel cut-out (estimate, no drawing published)


@part
def puck(m: FanMaster) -> Printed:
    rise = between(m.floor_top, m.top)
    inside = between(m.floor_top, m.top_under)
    with BuildPart() as made:
        with step("shell"), Locations(Location(m.floor_top)):
            Cylinder(m.puck_radius, rise, align=BOTTOM)
        with step("rounded top edge"):
            fillet(edges_on(built(made), m.top), m.wall)
        with step("hollow"), Locations(Location(m.floor_top)):
            Cylinder(m.inside_radius, inside, align=BOTTOM, mode=Mode.SUBTRACT)
        with step("floor bosses"), Locations(*m.floor_spots):
            Cylinder(m.screw_land, inside, align=BOTTOM)
        with step("floor inserts"):
            under = [spot * UPSIDE_DOWN for spot in m.floor_spots]
            insert_holes(Plane(under[0]), under, m.screw, INSERTS, fits=m.fits, stock=m.stock)
        with step("stepper bosses"):
            tabs = [m.stepper_at * spot for spot in m.stepper_tab_spots]
            with Locations(*tabs):
                Cylinder(m.screw_land, m.insert_depth, align=BOTTOM)
        with step("stepper inserts"):
            under = [spot * UPSIDE_DOWN for spot in tabs]
            insert_holes(
                Plane(under[0]), under, m.screw, STEPPER_INSERTS, fits=m.fits, stock=m.stock
            )
        with step("neck opening"), Locations(Location(m.top_under)):
            Cylinder(m.neck_opening, m.wall, align=BOTTOM, mode=Mode.SUBTRACT)
        with step("button hole"), Locations(foot_on(m.top_under, of=m.button_at)):
            Cylinder(m.fits.printed(BUTTON_CUTOUT) / 2, m.wall, align=BOTTOM, mode=Mode.SUBTRACT)
            register(BUTTON_HOLE, m.top, [FacesOn(plane=m.top)])
        with step("USB-C opening"):
            keepout = m.usb_keepout.block
            with Locations(keepout.at * Pos(Z=-m.fits.sliding)):
                Box(
                    keepout.width + 2 * m.fits.sliding,
                    keepout.depth,
                    keepout.height + 2 * m.fits.sliding,
                    align=BOTTOM,
                    mode=Mode.SUBTRACT,
                )
    return Printed(
        name="puck", pose=Location(), body=built(made), bed="+z", print_settings=m.print_settings
    )
