from build123d import Axis, GridLocations, Location, Locations, Plane, Pos
from cad.assembly.tree import Assembly, job
from cad.library.bought.boards import MOUNTING_HOLES, BoardMount, board_connectors
from cad.library.bought.vendor import Bought
from cad.library.derived import derived
from cad.library.extension_spring import HIGH_HOOK, LOW_HOOK, ExtensionSpring
from cad.library.features.boards import BOARD_ROLE, board_inserts, board_screws
from cad.library.features.hardware import (
    LIPS,
    Anchor,
    Fastening,
    Hole,
    Screws,
    anchors_of,
    clamp_screws,
    held_by,
    insert_seat,
    insert_seats,
    screwed,
    screwed_on,
    screws_at,
    seated,
    set_in,
    together,
)
from cad.library.mates import Connector, JointRange, Kind, Mate
from cad.library.shapes import OUTSIDE, Part, Seat, clamp_face, faces_on, round_faces, seat_of
from cad.library.standard.fasteners import UNDER_HEAD
from cad.library.why import Why

from pantilt.assemblies.harness import harness
from pantilt.master import (
    CAMERA_BOARD,
    DRIVER,
    JAW,
    MASTER,
    PAN,
    ROTOR,
    STATOR,
    TILT,
    USB_C_BOARD,
    ProductMaster,
)
from pantilt.models import stepper
from pantilt.parts.arm import CAP_INSERTS, PAN_BORE, PAN_CLAMP, arm
from pantilt.parts.base import DRIVER_INSERTS, LID_INSERTS, USB_C_INSERTS, base
from pantilt.parts.cap import cap
from pantilt.parts.cradle import (
    CAMERA_POCKET,
    JAW_GUIDE,
    SPRING_POST,
    TILT_BORE,
    TILT_CLAMP,
    cradle,
)
from pantilt.parts.jaw import SPRING_LUG, STEM, jaw
from pantilt.parts.lid import lid

WHY = {
    "pantilt/base": [
        Why(
            "Steppers on the motor shaft, driven silently, turn both axes directly",
            "Smooth and silent motion rules out gear noise and backlash; the phone's load is a "
            "fraction of a pancake stepper's holding torque, so no reduction is needed",
            (4, 5),
        ),
        Why(
            "The base is a cup closed by a lid that carries the pan motor",
            "The boards go in from above and the lid carries the motor's load straight into "
            "the cup's wall; one part fewer than a separate floor and top",
        ),
    ],
    "pantilt/arm": [
        Why(
            "The phone sits off the pan axis, away from the tilt drum",
            "The drum and its motor sit beyond the end of the phone; offsetting the phone the "
            "other way keeps the centre of mass over a base no wider than the phone",
            (5,),
        ),
    ],
    "pantilt/cradle": [
        Why(
            "A camera board of its own rides the cradle under the phone",
            "A video call holds the phone's camera, so the stand must see the face itself; "
            "riding the cradle it looks where the phone looks; one window, never two",
            (6,),
        ),
        Why(
            "A jaw sliding in a channel behind the cradle, pulled down by a stock spring",
            "The jaw meets every phone's top edge square, from the narrowest to the widest, "
            "and the spring hides in the channel behind the phone",
            (1,),
        ),
    ],
}
SHAFT = "shaft"
LID_ROLE = "base"
LEAD = "motor lead"
HEADER = "driver header"
TERMINAL = "driver terminal"
PINS = "USB-C pins"
CAMERA_PINS = "camera pins"
FACE = "face"
PAN_MOTOR = "pan motor, StepperOnline 17HS08-1004S"
TILT_MOTOR = "tilt motor, StepperOnline 17HS08-1004S"
PAN_ROTOR = "pan motor's rotor, inside the 17HS08-1004S"
TILT_ROTOR = "tilt motor's rotor, inside the 17HS08-1004S"
DRIVER_NAME = "Adafruit 6121 TMC2209 driver"
USB_C_NAME = "Adafruit 4090 USB-C breakout"
CAMERA_NAME = "Seeed XIAO ESP32S3 Sense"
FROM_ABOVE = -Axis.Z
FROM_THE_OUTSIDE = Axis((0, 0, 0), (-1, 0, 0))
FROM_THE_PHONE = Axis.X
FROM_BEHIND = -Axis.Y


def plug(m: ProductMaster, name: str) -> Seat:
    return seat_of([], m.board_plugs[name])


def stator(name: str, at: Location) -> Bought:
    flange = seat_of(faces_on(stepper.stator(), Plane.XY), Location())
    connectors = {FACE: flange, clamp_face(FACE): flange, LEAD: plug(MASTER, LEAD)}
    return Bought(name=name, pose=at, item=STATOR, connectors=connectors)


def rotor(name: str, at: Location, inside: str) -> Bought:
    shaft = seat_of(round_faces(stepper.rotor(), stepper.SHAFT_DIAMETER / 2), Location())
    return Bought(name=name, pose=at, item=ROTOR, connectors={SHAFT: shaft}, ships_with=inside)


def motor(
    m: ProductMaster,
    names: tuple[str, str],
    at: Location,
    spots: list[Location],
    mount: Part,
    joint: tuple[str, JointRange],
) -> Fastening:
    body, shaft = stator(names[0], at), rotor(names[1], at, names[0])
    through = Hole(
        face=Plane(at), seats=seated(spots, m.wall), screw=m.screw, anchor=Anchor.CLEARANCE
    )
    with Locations(Pos(Z=-stepper.TAPPED_DEPTH)):
        threads = GridLocations(stepper.HOLE_SPACING, stepper.HOLE_SPACING, 2, 2).locations
    into = Hole(face=Plane.XY, seats=threads, screw=m.screw, anchor=Anchor.TAPPED)
    fitted = screwed_on(through, into, Connector(mount, LIPS), Connector(body, FACE), stock=m.stock)
    name, limits = joint
    turning = Mate(
        name,
        Kind.REVOLUTE,
        child=Connector(shaft, SHAFT),
        parent=Connector(body, FACE),
        at=at,
        limits=limits,
        approach=-Axis(at),
    )
    return together([Fastening(parts=[body, shaft], mates=[turning]), fitted])


def clamp_insert(m: ProductMaster, holder: Part, spot: Location, seat: str) -> Fastening:
    into = Hole(
        face=Plane(spot),
        seats=[insert_seat(spot, m.screw, fits=m.fits, stock=m.stock)],
        screw=m.screw,
        anchor=Anchor.INSERT,
    )
    inserts = anchors_of(into, holder.pose, f"{holder.name} shaft", holder.name, stock=m.stock)
    return Fastening(parts=inserts, mates=held_by(inserts, OUTSIDE, Connector(holder, seat)))


def clamp_screw(m: ProductMaster, holder: Part, spot: Location, seat: str) -> Fastening:
    screws = screws_at(
        f"{holder.name} shaft clamp",
        holder.pose,
        Screws(seats=[spot], size=m.screw, length=m.clamp_screw_length),
        stock=m.stock,
    )
    on = Connector(holder, clamp_face(seat))
    return Fastening(parts=screws, mates=held_by(screws, UNDER_HEAD, on))


def driver(m: ProductMaster, at: Location) -> Bought:
    connectors = {
        **board_connectors(DRIVER, m.driver_mount.holes),
        HEADER: plug(m, HEADER),
        TERMINAL: plug(m, TERMINAL),
    }
    return Bought(name=DRIVER_NAME, pose=at, item=DRIVER, connectors=connectors)


def usb_board(m: ProductMaster) -> Bought:
    connectors = {**board_connectors(USB_C_BOARD, m.usb_mount.holes), PINS: plug(m, PINS)}
    return Bought(name=USB_C_NAME, pose=m.usb_board_at, item=USB_C_BOARD, connectors=connectors)


def on_the_floor(m: ProductMaster) -> list[tuple[BoardMount, Bought, str]]:
    return [
        *((m.driver_mount, driver(m, at), DRIVER_INSERTS) for at in m.drivers_at),
        (m.usb_mount, usb_board(m), USB_C_INSERTS),
    ]


@derived
def base_inserts(m: ProductMaster) -> Fastening:
    cup = base(m)
    lid_into = insert_seats(m.pan_flange, m.lid_screws, m.screw, fits=m.fits, stock=m.stock)
    made = [set_in(lid_into, Connector(lid(m), LIPS), Connector(cup, LID_INSERTS), stock=m.stock)]
    for mount, board, name in on_the_floor(m):
        into = board_inserts(mount, board.pose, fits=m.fits, stock=m.stock)
        held = Connector(board, MOUNTING_HOLES)
        made.append(set_in(into, held, Connector(cup, name), BOARD_ROLE, stock=m.stock))
    return together(made)


@derived
def boards(m: ProductMaster) -> Fastening:
    cup = base(m)
    floor = on_the_floor(m)
    made = []
    for mount, board, name in floor:
        into = board_inserts(mount, board.pose, fits=m.fits, stock=m.stock)
        on = Connector(cup, name)
        made.append(board_screws(board, mount, Location(), into, on, stock=m.stock))
    return together(made, [board for _, board, _ in floor])


@derived
def pan_motor(m: ProductMaster) -> Fastening:
    names = (PAN_MOTOR, PAN_ROTOR)
    return motor(m, names, m.pan_motor_at, m.pan_motor_screws, lid(m), (PAN, m.pan_range))


@derived
def lid_on_base(m: ProductMaster) -> Fastening:
    top = lid(m)
    seated_on = Mate(
        "lid on base",
        Kind.RIGID,
        child=Connector(top, clamp_face(LIPS)),
        parent=Connector(base(m), clamp_face(LID_INSERTS)),
        approach=FROM_ABOVE,
    )
    return Fastening(parts=[top], mates=[seated_on])


@derived
def lid_screws(m: ProductMaster) -> Fastening:
    through = Hole(
        face=m.pan_flange,
        seats=seated(m.lid_screws, m.wall),
        screw=m.screw,
        anchor=Anchor.CLEARANCE,
    )
    into = insert_seats(m.pan_flange, m.lid_screws, m.screw, fits=m.fits, stock=m.stock)
    top = lid(m)
    screws = clamp_screws(through, into, top.pose, base(m).pose, top.name, LID_ROLE, stock=m.stock)
    return Fastening(parts=screws, mates=held_by(screws, UNDER_HEAD, Connector(top, LIPS)))


@derived
def arm_on_pan_motor(m: ProductMaster) -> Fastening:
    turning = arm(m)
    mate = Mate(
        f"arm on {PAN_ROTOR}",
        Kind.RIGID,
        child=Connector(turning, PAN_BORE),
        parent=Connector(PAN_ROTOR, SHAFT),
        approach=FROM_ABOVE,
    )
    return Fastening(parts=[turning], mates=[mate])


@derived
def pan_clamp_insert(m: ProductMaster) -> Fastening:
    return clamp_insert(m, arm(m), m.pan_clamp, PAN_CLAMP)


@derived
def pan_clamp_screw(m: ProductMaster) -> Fastening:
    return clamp_screw(m, arm(m), m.pan_clamp, PAN_CLAMP)


@derived
def cap_inserts(m: ProductMaster) -> Fastening:
    into = insert_seats(m.cap_rim, m.cap_screws, m.screw, fits=m.fits, stock=m.stock)
    return set_in(into, Connector(cap(m), LIPS), Connector(arm(m), CAP_INSERTS), stock=m.stock)


@derived
def tilt_motor(m: ProductMaster) -> Fastening:
    names = (TILT_MOTOR, TILT_ROTOR)
    return motor(m, names, m.tilt_motor_at, m.tilt_motor_screws, arm(m), (TILT, m.tilt_range))


@derived
def cap_on_arm(m: ProductMaster) -> Fastening:
    end = cap(m)
    through = Hole(
        face=m.cap_rim, seats=seated(m.cap_screws, m.wall), screw=m.screw, anchor=Anchor.CLEARANCE
    )
    into = insert_seats(m.cap_rim, m.cap_screws, m.screw, fits=m.fits, stock=m.stock)
    held = screwed(
        through, into, Connector(end, LIPS), Connector(arm(m), CAP_INSERTS), stock=m.stock
    )
    return together([held], [end])


@derived
def cradle_on_tilt_motor(m: ProductMaster) -> Fastening:
    held = cradle(m)
    mate = Mate(
        f"cradle on {TILT_ROTOR}",
        Kind.RIGID,
        child=Connector(held, TILT_BORE),
        parent=Connector(TILT_ROTOR, SHAFT),
        approach=FROM_THE_PHONE,
    )
    return Fastening(parts=[held], mates=[mate])


@derived
def tilt_clamp_insert(m: ProductMaster) -> Fastening:
    return clamp_insert(m, cradle(m), m.tilt_clamp, TILT_CLAMP)


@derived
def tilt_clamp_screw(m: ProductMaster) -> Fastening:
    return clamp_screw(m, cradle(m), m.tilt_clamp, TILT_CLAMP)


@derived
def camera(m: ProductMaster) -> Fastening:
    pins = {CAMERA_PINS: plug(m, CAMERA_PINS)}
    board = Bought(name=CAMERA_NAME, pose=m.camera_at, item=CAMERA_BOARD, connectors=pins)
    mate = Mate(
        f"{CAMERA_NAME} in cradle",
        Kind.RIGID,
        child=Connector(board, OUTSIDE),
        parent=Connector(cradle(m), CAMERA_POCKET),
        approach=FROM_BEHIND,
    )
    return Fastening(parts=[board], mates=[mate])


@derived
def jaw_spring(m: ProductMaster) -> Fastening:
    spring = ExtensionSpring.hooked(
        name="jaw spring", spring=m.spring, low=m.spring_post_at, high=m.spring_lug_at
    )
    hooked = Mate(
        "jaw spring on cradle",
        Kind.RIGID,
        child=Connector(spring, LOW_HOOK),
        parent=Connector(cradle(m), SPRING_POST),
        approach=FROM_ABOVE,
    )
    pulling = Mate(
        "jaw spring on jaw",
        Kind.RIGID,
        child=Connector(spring, HIGH_HOOK),
        parent=Connector(jaw(m), SPRING_LUG),
        closes=True,
    )
    return Fastening(parts=[spring], mates=[hooked, pulling])


@derived
def jaw_on_cradle(m: ProductMaster) -> Fastening:
    sliding = jaw(m)
    mate = Mate(
        JAW,
        Kind.PRISMATIC,
        child=Connector(sliding, STEM),
        parent=Connector(cradle(m), JAW_GUIDE),
        at=m.stem_at,
        limits=m.jaw_range,
        approach=FROM_ABOVE,
    )
    return Fastening(parts=[sliding], mates=[mate])


PRODUCT = Assembly(
    "pantilt",
    Assembly(
        "base",
        job(base, MASTER),
        job(base_inserts, MASTER),
        job(boards, MASTER),
        Assembly(
            "lid and pan motor",
            job(lid_on_base, MASTER),
            job(pan_motor, MASTER),
            bench=True,
        ),
        job(lid_screws, MASTER),
    ),
    Assembly(
        "arm",
        job(arm_on_pan_motor, MASTER),
        job(pan_clamp_insert, MASTER),
        job(pan_clamp_screw, MASTER),
        job(cap_inserts, MASTER),
        job(tilt_motor, MASTER),
        job(cap_on_arm, MASTER),
    ),
    Assembly(
        "cradle",
        job(cradle_on_tilt_motor, MASTER),
        job(tilt_clamp_insert, MASTER),
        job(tilt_clamp_screw, MASTER),
        job(camera, MASTER),
        job(jaw_spring, MASTER),
        job(jaw_on_cradle, MASTER),
    ),
    cables=lambda: harness(MASTER),
)
