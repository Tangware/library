from dataclasses import replace

from build123d import Axis, Location

from box.master import MASTER, PICO_2, PICO_2_USB, BoxMaster
from box.parts.body import BOARD_INSERTS, MAGNETS, body
from box.parts.lid import lid
from cad.assembly.tree import Assembly, job
from cad.cables.models import Cable, Jacketed, Plug, Route, RoutePoint, Wire
from cad.library.bought.catalogue import NO_BILL
from cad.library.bought.boards import MOUNTING_HOLES, board_connectors
from cad.library.bought.vendor import Bought
from cad.library.derived import derived
from cad.library.features.boards import BOARD_ROLE, board_inserts, board_screws
from cad.library.features.hardware import (
    INSERTS,
    LIPS,
    Anchor,
    Fastening,
    Hole,
    discs_in,
    insert_seats,
    screwed,
    seated,
    set_in,
    together,
)
from cad.library.mates import Connector

PICO_2_NAME = "Raspberry Pi Pico 2"
AWG_28_MM = 0.321  # ASTM B258, 28 AWG conductor
AK67501_JACKET_MM = 3.5  # Assmann drawing AK67501-1-R, read in a search summary, not opened
USB_WIRES = ("VBUS", "D-", "D+", "GND")
USB_CABLE = Cable(
    name="Assmann AK67501-1-R USB A to micro-B cable, 1 m",
    wires=tuple(Wire(name=name, diameter=AWG_28_MM, colour=name) for name in USB_WIRES),
    plugs=(
        Plug(name="micro-B", model=None, pinout=USB_WIRES),
        Plug(name="A", model=None, pinout=USB_WIRES),
    ),
    construction=Jacketed(diameter=AK67501_JACKET_MM),
    twist_rating=0.0,
    length=1000.0,
    bill=NO_BILL,
)


def pico(m: BoxMaster) -> Bought:
    connectors = board_connectors(PICO_2, m.mount.holes)
    return Bought(name=PICO_2_NAME, pose=m.board_at, item=PICO_2, connectors=connectors)


def lid_inserts(m: BoxMaster) -> Hole:
    return insert_seats(m.rim, m.lid_spots, m.lid_screw, fits=m.fits, stock=m.stock)


def pico_inserts(m: BoxMaster) -> Hole:
    return board_inserts(m.mount, m.board_at, fits=m.fits, stock=m.stock)


@derived
def inserts(m: BoxMaster) -> Fastening:
    base = body(m)
    for_lid = set_in(
        lid_inserts(m), Connector(lid(m), LIPS), Connector(base, INSERTS), stock=m.stock
    )
    for_board = set_in(
        pico_inserts(m),
        Connector(pico(m), MOUNTING_HOLES),
        Connector(base, BOARD_INSERTS),
        BOARD_ROLE,
        stock=m.stock,
    )
    return together([for_lid, for_board])


@derived
def magnets(m: BoxMaster) -> Fastening:
    made = discs_in(body(m), m.magnet_seats, m.magnet, MAGNETS)
    return replace(made, mates=[replace(mate, approach=Axis.Z) for mate in made.mates])


@derived
def board(m: BoxMaster) -> Fastening:
    held = pico(m)
    holder = Connector(body(m), BOARD_INSERTS)
    screws = board_screws(held, m.mount, Location(), pico_inserts(m), holder, stock=m.stock)
    return together([screws], [held])


@derived
def closed(m: BoxMaster) -> Fastening:
    top = lid(m)
    through = Hole(
        face=m.rim,
        seats=seated(m.lid_spots, m.wall),
        screw=m.lid_screw,
        anchor=Anchor.CLEARANCE,
    )
    holder = Connector(body(m), INSERTS)
    screws = screwed(through, lid_inserts(m), Connector(top, LIPS), holder, stock=m.stock)
    return together([screws], [top])


def usb_cable(m: BoxMaster) -> list[Route]:
    return [
        Route(
            cable=USB_CABLE,
            plugged=(
                Connector(pico(m), PICO_2_USB.name),
                RoutePoint(part=body(m), at=m.cable_on_desk),
            ),
            through=((RoutePoint(part=body(m), at=m.cable_exit),),),
        )
    ]


BOX = Assembly(
    "box",
    Assembly("base", job(body, MASTER), job(inserts, MASTER), job(magnets, MASTER)),
    job(board, MASTER),
    job(closed, MASTER),
    cables=lambda _: usb_cable(MASTER),
)
