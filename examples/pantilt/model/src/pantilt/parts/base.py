from build123d import (
    Align,
    Axis,
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
    chamfer,
    extrude,
)
from cad.design.parts import part
from cad.library.bought.boards import BoardMount
from cad.library.features.boards import on_the_posts, post_tops
from cad.library.features.cuts import extrude_to
from cad.library.features.hardware import insert_holes, insert_land
from cad.library.features.planes import axis_along, between, crossing
from cad.library.provenance import step
from cad.library.shapes import Printed, built, edges_on
from cad.library.turns import UPSIDE_DOWN

from pantilt.master import ProductMaster

LID_INSERTS = "lid inserts"
DRIVER_INSERTS = "driver inserts"
USB_C_INSERTS = "USB-C inserts"
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)
TOP = (Align.CENTER, Align.CENTER, Align.MAX)


def board_posts(m: ProductMaster, mount: BoardMount, boards: list[Location], name: str) -> None:
    with BuildSketch(*[spot for at in boards for spot in mount.underside(at)]) as posts:
        Circle(insert_land(m.board_screw, fits=m.fits, stock=m.stock))
    tops = on_the_posts(mount, boards[0])
    extrude_to(tops * UPSIDE_DOWN, m.floor, sketch=posts)
    spots = [spot for at in boards for spot in post_tops(mount, at)]
    insert_holes(Plane(tops), spots, m.board_screw, name, fits=m.fits, stock=m.stock)


@part
def base(m: ProductMaster) -> Printed:
    with BuildPart() as made:
        with step("cup"), Locations(Location(m.ground)):
            Cylinder(m.radius, between(m.ground, m.base_top), align=BOTTOM)
        with step("edge break"):
            chamfer(edges_on(built(made), m.ground), m.fits.min_wall)
        with step("hollow"), Locations(Location(m.base_top)):
            Cylinder(
                m.inside_radius,
                between(m.floor, m.base_top),
                align=TOP,
                mode=Mode.SUBTRACT,
            )
        with step("lid bosses"), BuildSketch(*m.lid_screws) as bosses:
            Circle(insert_land(m.screw, fits=m.fits, stock=m.stock))
        with step("lid bosses"):
            extrude(bosses.sketch, amount=-m.screw_plate - m.standoff)
        with step("lid inserts"):
            insert_holes(
                m.pan_flange, m.lid_screws, m.screw, LID_INSERTS, fits=m.fits, stock=m.stock
            )
        with step("driver posts"):
            board_posts(m, m.driver_mount, m.drivers_at, DRIVER_INSERTS)
        with step("USB-C posts"):
            board_posts(m, m.usb_mount, [m.usb_board_at], USB_C_INSERTS)
        with step("USB-C opening"):
            plug = m.usb_plug.block
            inside = Plane.XZ.offset(-m.inside_radius)
            mouth = crossing(inside, axis_along(Axis.Y.direction, through=plug.at))
            with Locations(mouth * Pos(Z=-m.fits.sliding)):
                Box(
                    plug.width + 2 * m.fits.sliding,
                    2 * m.wall,
                    plug.height + 2 * m.fits.sliding,
                    align=BOTTOM,
                    mode=Mode.SUBTRACT,
                )
    return Printed(
        name="base",
        pose=Location(),
        body=built(made),
        bed="-z",
        material="PAHT-CF black",
        print_settings=m.print_settings,
    )
