from dataclasses import replace

from build123d import Axis, Location, Plane, Pos
from cad.assembly.tree import Assembly, job
from cad.cables.models import Cable, CutToFit, Discrete, Plug, Route, RoutePoint, Wire
from cad.library.bought.boards import (
    MOUNTING_HOLES,
    MountingHoles,
    board_connectors,
    mounting_hole_seats,
    mounting_holes,
)
from cad.library.bought.catalogue import NO_BILL, Bill, Catalogue
from cad.library.bought.vendor import Bought, vendor_shape
from cad.library.derived import derived
from cad.library.features.boards import BOARD_ROLE, board_inserts, board_screws
from cad.library.features.hardware import (
    INSERTS,
    LIPS,
    Anchor,
    Fastening,
    Hole,
    held_by,
    insert_seats,
    screwed,
    seated,
    set_in,
    together,
)
from cad.library.features.planes import axis_along, crossing, foot_on, parallel
from cad.library.mates import Connector, Kind, Mate
from cad.library.shapes import OUTSIDE, Seat, round_faces, seat_of
from cad.library.turns import UPSIDE_DOWN

from fan import models
from fan.master import (
    BUMPER,
    BUTTON,
    DRIVER,
    FAN,
    MASTER,
    ROTOR,
    STATOR,
    STEPPER_TAB_HOLE,
    STEPPER_TABS,
    TAPE,
    XIAO,
    FanMaster,
    xiao_five_volt_pad,
)
from fan.models import SWEEP
from fan.parts.cover import cover
from fan.parts.floor import DRIVER_INSERTS, FEET, TAPE_SEAT, floor
from fan.parts.head import FAN_SEAT, SHAFT_BORE, head
from fan.parts.puck import BUTTON_HOLE, STEPPER_INSERTS, puck

FAN_NAME = "Delta AFB0805L fan"
STEPPER_NAME = "Adafruit 858 28BYJ-48 stepper"
SHAFT_NAME = "Adafruit 858's output shaft, inside the stepper"
SHAFT = "shaft"
XIAO_NAME = "Seeed Studio XIAO RP2040"
TAPE_NAME = "3M VHB 5952 pad"
DRIVER_NAME = "Adafruit DRV8833 breakout"
BUTTON_NAME = "Adafruit 1445 16 mm pushbutton"
BUMPER_NAME = "3M Bumpon SJ5302"


def stepper_tabs() -> MountingHoles:
    return mounting_holes(STATOR, *STEPPER_TAB_HOLE, STEPPER_TABS)


def stepper(m: FanMaster) -> Bought:
    seats = {
        **mounting_hole_seats(stepper_tabs()),
        **wired(STATOR, Pos(*models.STEPPER_LEAD)),
    }
    return Bought(name=STEPPER_NAME, pose=m.stepper_at, item=STATOR, connectors=seats)


def shaft(m: FanMaster) -> Bought:
    seat = seat_of(round_faces(vendor_shape(ROTOR), models.SHAFT_DIAMETER / 2), Location())
    return Bought(
        name=SHAFT_NAME,
        pose=m.stepper_at,
        item=ROTOR,
        connectors={SHAFT: seat},
        ships_with=STEPPER_NAME,
    )


def driver(m: FanMaster) -> Bought:
    pads = Pos(Y=models.DRIVER_WIDTH / 2, Z=models.DRIVER_BOARD_TOP)
    connectors = {**board_connectors(DRIVER, m.driver_mount.holes), **wired(DRIVER, pads)}
    return Bought(name=DRIVER_NAME, pose=m.driver_at, item=DRIVER, connectors=connectors)


def tab_spots(m: FanMaster) -> list[Location]:
    return [m.stepper_at * spot * UPSIDE_DOWN for spot in m.stepper_tab_spots]


def floor_spots(m: FanMaster) -> list[Location]:
    return [spot * UPSIDE_DOWN for spot in m.floor_spots]


def facing_back(m: FanMaster, depth: float) -> list[Location]:
    return [m.facing_back(at, depth) for at in m.fan_screws]


def plane_at(m: FanMaster, depth: float) -> Plane:
    return Plane(m.facing_back(Pos(), depth))


def floor_inserts(m: FanMaster) -> Hole:
    return insert_seats(m.floor_top, floor_spots(m), m.screw, fits=m.fits, stock=m.stock)


def stepper_inserts(m: FanMaster) -> Hole:
    return insert_seats(m.tabs, tab_spots(m), m.screw, fits=m.fits, stock=m.stock)


def cover_inserts(m: FanMaster) -> Hole:
    front = plane_at(m, m.fan_front)
    return insert_seats(front, facing_back(m, m.fan_front), m.screw, fits=m.fits, stock=m.stock)


@derived
def puck_inserts(m: FanMaster) -> Fastening:
    base = puck(m)
    for_floor = set_in(
        floor_inserts(m), Connector(floor(m), LIPS), Connector(base, INSERTS), stock=m.stock
    )
    for_stepper = set_in(
        stepper_inserts(m),
        Connector(stepper(m), MOUNTING_HOLES),
        Connector(base, STEPPER_INSERTS),
        stock=m.stock,
    )
    return together([for_floor, for_stepper])


@derived
def stepper_mounted(m: FanMaster) -> Fastening:
    held = stepper(m)
    tabs = stepper_tabs()
    local = [spot * UPSIDE_DOWN for spot in m.stepper_tab_spots]
    through = Hole(
        face=m.tabs,
        seats=seated(local, tabs.board_top - tabs.board_bottom),
        screw=m.screw,
        anchor=Anchor.CLEARANCE,
    )
    screws = screwed(
        through,
        stepper_inserts(m),
        Connector(held, MOUNTING_HOLES),
        Connector(puck(m), STEPPER_INSERTS),
        stock=m.stock,
    )
    rotor = shaft(m)
    turning = Mate(
        SWEEP,
        Kind.REVOLUTE,
        child=Connector(rotor, SHAFT),
        parent=Connector(held, OUTSIDE),
        at=Location(m.shaft_top),
        limits=m.sweep_range,
        servo=held,
        approach=-Axis.Z,
    )
    return together([screws, Fastening(parts=[rotor], mates=[turning])], [held])


@derived
def button(m: FanMaster) -> Fastening:
    terminals = wired(BUTTON, Pos(Z=-models.BUTTON_TERMINALS))
    held = Bought(name=BUTTON_NAME, pose=m.button_at, item=BUTTON, connectors=terminals)
    mate = Mate(
        f"{BUTTON_NAME} in puck",
        Kind.RIGID,
        child=Connector(held, OUTSIDE),
        parent=Connector(puck(m), BUTTON_HOLE),
        approach=-Axis.Z,
    )
    return Fastening(parts=[held], mates=[mate])


@derived
def turning_head(m: FanMaster) -> Fastening:
    made = head(m)
    on_shaft = Mate(
        f"head on {SHAFT_NAME}",
        Kind.RIGID,
        child=Connector(made, SHAFT_BORE),
        parent=Connector(SHAFT_NAME, SHAFT),
        approach=-Axis.Z,
    )
    inserts = set_in(
        cover_inserts(m), Connector(cover(m), LIPS), Connector(made, INSERTS), stock=m.stock
    )
    return Fastening(parts=[made, *inserts.parts], mates=[on_shaft, *inserts.mates])


@derived
def fan(m: FanMaster) -> Fastening:
    lead = wired(FAN, m.fan_origin * Pos(X=m.fan_side / 2, Y=-(m.fan_depth + m.lead_reach / 2)))
    held = Bought(name=FAN_NAME, pose=m.fan_at, item=FAN, connectors=lead)
    mate = Mate(
        f"{FAN_NAME} in head",
        Kind.RIGID,
        child=Connector(held, OUTSIDE),
        parent=Connector(head(m), FAN_SEAT),
        approach=-Axis.Y,
    )
    return Fastening(parts=[held], mates=[mate])


@derived
def closed_head(m: FanMaster) -> Fastening:
    back = cover(m)
    through = Hole(
        face=plane_at(m, m.fan_back),
        seats=seated(facing_back(m, m.fan_back), m.wall),
        screw=m.screw,
        anchor=Anchor.CLEARANCE,
    )
    holder = Connector(head(m), INSERTS)
    screws = screwed(through, cover_inserts(m), Connector(back, LIPS), holder, stock=m.stock)
    return together([screws], [back])


@derived
def floor_inserts_set(m: FanMaster) -> Fastening:
    plate = floor(m)
    posts = board_inserts(m.driver_mount, m.driver_at, fits=m.fits, stock=m.stock)
    held = Connector(driver(m), MOUNTING_HOLES)
    inserts = set_in(posts, held, Connector(plate, DRIVER_INSERTS), BOARD_ROLE, stock=m.stock)
    return together([inserts], [plate])


@derived
def driver_mounted(m: FanMaster) -> Fastening:
    board = driver(m)
    posts = board_inserts(m.driver_mount, m.driver_at, fits=m.fits, stock=m.stock)
    holder = Connector(floor(m), DRIVER_INSERTS)
    screws = board_screws(board, m.driver_mount, Location(), posts, holder, stock=m.stock)
    return together([screws], [board])


def tape(m: FanMaster) -> Bought:
    return Bought(name=TAPE_NAME, pose=m.tape_at, item=TAPE)


@derived
def tape_pad(m: FanMaster) -> Fastening:
    pad = tape(m)
    mates = held_by([pad], OUTSIDE, Connector(floor(m), TAPE_SEAT))
    return Fastening(parts=[pad], mates=[replace(mate, approach=-Axis.Z) for mate in mates])


@derived
def taped_board(m: FanMaster) -> Fastening:
    pads = wired(XIAO, xiao_five_volt_pad() * Pos(Z=models.XIAO_TOP))
    board = Bought(name=XIAO_NAME, pose=m.xiao_at, item=XIAO, connectors=pads)
    mates = held_by([board], OUTSIDE, Connector(tape(m), OUTSIDE))
    return Fastening(parts=[board], mates=[replace(mate, approach=-Axis.Z) for mate in mates])


@derived
def feet(m: FanMaster) -> Fastening:
    pads = [Bought(name=BUMPER_NAME, pose=at, item=BUMPER) for at in m.feet_at]
    mates = held_by(pads, OUTSIDE, Connector(floor(m), FEET))
    return Fastening(parts=pads, mates=[replace(mate, approach=Axis.Z) for mate in mates])


@derived
def closed(m: FanMaster) -> Fastening:
    through = Hole(
        face=m.floor_top,
        seats=seated(floor_spots(m), m.wall),
        screw=m.screw,
        anchor=Anchor.CLEARANCE,
    )
    holder = Connector(puck(m), INSERTS)
    return screwed(through, floor_inserts(m), Connector(floor(m), LIPS), holder, stock=m.stock)


WIRED = "wired end"
BUTTON_WIRES = ("switch", "ground")
DRIVER_WIRES = ("AIN1", "AIN2", "BIN1", "BIN2", "VM", "GND")


def hook_up(name: str, wires: tuple[str, ...], ends: tuple[str, str]) -> Cable:
    return Cable(
        name=name,
        wires=tuple(Wire(name=wire, diameter=models.WIRE_26_AWG, colour=wire) for wire in wires),
        plugs=tuple(Plug(name=end, model=None, pinout=wires) for end in ends),
        construction=Discrete(),
        twist_rating=0.0,
        length=CutToFit(),
        bill=NO_BILL,
    )


BUTTON_LEADS = hook_up(
    "button leads, 2 x 26 AWG silicone wire", BUTTON_WIRES, ("button terminals", "XIAO pads")
)
DRIVER_LEADS = hook_up(
    "driver leads, 6 x 26 AWG silicone wire", DRIVER_WIRES, ("driver pads", "XIAO pads")
)


FAN_WIRES = ("+5V", "GND")
STEPPER_WIRES = ("A", "B", "C", "D", "common")


def shipped_lead(
    name: str, wires: tuple[str, ...], diameter: float, length: float, ships_with: str
) -> Cable:
    return Cable(
        name=name,
        wires=tuple(Wire(name=wire, diameter=diameter, colour=wire) for wire in wires),
        plugs=(
            Plug(name=ships_with, model=None, pinout=wires),
            Plug(name="soldered end", model=None, pinout=wires),
        ),
        construction=Discrete(),
        twist_rating=0.0,
        length=length,
        bill=Bill(ships_with=ships_with),
    )


FAN_LEAD = shipped_lead(
    "fan lead", FAN_WIRES, models.FAN_LEAD_WIRE, models.FAN_LEAD_LENGTH, FAN_NAME
)
STEPPER_LEAD = shipped_lead(
    "stepper lead",
    STEPPER_WIRES,
    models.STEPPER_LEAD_WIRE,
    models.STEPPER_LEAD_LENGTH,
    STEPPER_NAME,
)


def wired(item: Catalogue, at: Location) -> dict[str, Seat]:
    return {WIRED: seat_of(vendor_shape(item).faces(), at)}


def abreast(along: Location, of: Location) -> RoutePoint:
    lane = axis_along(Axis.Y.direction, through=along)
    return RoutePoint(part="puck", at=crossing(parallel(Plane.XZ, through=of), lane))


def harness(m: FanMaster) -> list[Route]:
    behind = abreast(m.harness_lane, of=m.xiao_at * Pos(Y=-models.XIAO_LENGTH))
    driver_edge = m.driver_at * Pos(Y=models.DRIVER_WIDTH / 2)
    xiao = Connector(XIAO_NAME, WIRED)
    driver_pads = Connector(DRIVER_NAME, WIRED)
    return [
        Route(
            cable=BUTTON_LEADS,
            plugged=(Connector(BUTTON_NAME, WIRED), xiao),
            through=((abreast(m.harness_lane, of=m.button_at), behind),),
        ),
        Route(
            cable=DRIVER_LEADS,
            plugged=(driver_pads, xiao),
            through=(
                (
                    RoutePoint(part="puck", at=foot_on(m.tabs, of=driver_edge)),
                    abreast(m.harness_lane, of=driver_edge),
                    behind,
                ),
            ),
        ),
        Route(
            cable=FAN_LEAD,
            plugged=(Connector(FAN_NAME, WIRED), xiao),
            through=(
                (
                    RoutePoint(part="head", at=Location(m.neck_bottom) * m.lead_way),
                    RoutePoint(part="puck", at=m.under_neck),
                    abreast(m.harness_lane, of=m.lead_way),
                    behind,
                ),
            ),
        ),
        Route(
            cable=STEPPER_LEAD,
            plugged=(Connector(STEPPER_NAME, WIRED), driver_pads),
            through=((abreast(m.stepper_lane, of=m.stepper_at * Pos(*models.STEPPER_LEAD)),),),
        ),
    ]


PRODUCT = Assembly(
    "fan",
    Assembly(
        "puck",
        job(puck, MASTER),
        job(puck_inserts, MASTER),
        job(stepper_mounted, MASTER),
        job(button, MASTER),
    ),
    Assembly("head", job(turning_head, MASTER), job(fan, MASTER), job(closed_head, MASTER)),
    Assembly(
        "floor",
        job(floor_inserts_set, MASTER),
        job(driver_mounted, MASTER),
        job(tape_pad, MASTER),
        job(taped_board, MASTER),
        bench=True,
    ),
    job(closed, MASTER),
    job(feet, MASTER),
    cables=lambda: harness(MASTER),
)
