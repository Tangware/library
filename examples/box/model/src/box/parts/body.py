from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    Location,
    Locations,
    Mode,
    Plane,
    Pos,
    Select,
    fillet,
)

from box.master import BoxMaster
from cad.design.parts import part
from cad.library.features.boards import insert_posts
from cad.library.features.cuts import disc_seat
from cad.library.features.hardware import INSERTS, insert_holes
from cad.library.features.planes import foot_on
from cad.library.provenance import step
from cad.library.shapes import Printed, RoundFaces, SeatQuery, built, register_each
from cad.library.why import Why

BOARD_INSERTS = "board inserts"
MAGNETS = "magnets"
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)
WHY = {
    "body": [
        Why(
            "Magnets pressed into pockets under the floor",
            "The box hangs on steel by its base, so the pull runs straight through the floor it"
            " sits on; a press fit holds them with no glue, screw or extra part.",
            requirements=(2,),
        )
    ]
}


@part
def body(m: BoxMaster) -> Printed:
    outside, inside = m.outside, m.inside
    with BuildPart() as made:
        with step("shell"), Locations(outside.at):
            Box(outside.width, outside.depth, outside.height, align=BOTTOM)
        with step("rounded corners"):
            fillet(made.edges(Select.LAST).filter_by(Axis.Z), m.wall)
        with step("hollow"), Locations(inside.at):
            Box(inside.width, inside.depth, inside.height, align=BOTTOM, mode=Mode.SUBTRACT)
        with step("screw bosses"), Locations(*[foot_on(m.floor, of=spot) for spot in m.lid_spots]):
            side = 2 * m.lid_land
            Box(side, side, inside.height, align=BOTTOM)
        with step("lid inserts"):
            insert_holes(m.rim, m.lid_spots, m.lid_screw, INSERTS, fits=m.fits, stock=m.stock)
        with step("board posts"):
            insert_posts(m.mount, m.board_at, m.floor, BOARD_INSERTS, fits=m.fits, stock=m.stock)
        with step("USB opening"):
            keepout = m.usb_keepout.block
            grown = keepout.at * Pos(Z=-m.fits.sliding)
            with Locations(grown):
                Box(
                    keepout.width + 2 * m.fits.sliding,
                    keepout.depth,
                    keepout.height + 2 * m.fits.sliding,
                    align=BOTTOM,
                    mode=Mode.SUBTRACT,
                )
        with step("magnet pockets"):
            disc_seat(m.magnet, m.magnet_seats, fits=m.fits)
            pockets = [
                SeatQuery(
                    frame=seat,
                    faces=[
                        RoundFaces(axis=Axis(seat), radius=m.fits.pressed(m.magnet.diameter) / 2)
                    ],
                )
                for seat in m.magnet_seats
            ]
            register_each(MAGNETS, Location(Plane.XY), pockets)
    return Printed(
        name="body", pose=Location(), body=built(made), bed="-z", print_settings=m.print_settings
    )
