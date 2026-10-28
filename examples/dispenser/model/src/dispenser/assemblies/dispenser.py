from dataclasses import replace

from build123d import Axis, Location, Plane, Pos
from cad.assembly.tree import Assembly, job
from cad.cables.models import (
    Cable,
    CutToFit,
    Discrete,
    Jacketed,
    Plug,
    Route,
    RoutePoint,
    Wire,
)
from cad.library.bought.boards import (
    MOUNTING_HOLES,
    BoardMount,
    MountingHoles,
    board_connectors,
    mounting_hole_seats,
    mounting_holes,
)
from cad.library.bought.catalogue import NO_BILL, Bill, Catalogue
from cad.library.bought.vendor import Bought, vendor_block, vendor_shape
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
from cad.library.features.planes import (
    corner,
    crossing,
    foot_on,
    normal_to,
    parallel,
    reach,
    through_the_middle,
)
from cad.library.mates import Connector, JointRange, Kind, Mate
from cad.library.shapes import OUTSIDE, Part, round_faces, seat_of
from cad.library.turns import UPSIDE_DOWN
from cad.library.why import Why

from dispenser import models
from dispenser.master import (
    ACTUATOR,
    BUZZER,
    CAROUSEL_TURN,
    DRAWER_SLIDE,
    DRIVER,
    LED,
    MASTER,
    PICO,
    PICO_USB,
    REED,
    REED_HOLE,
    REED_HOLES,
    ROTOR,
    STATOR,
    STEPPER_TAB_HOLE,
    STEPPER_TABS,
    DispenserMaster,
)
from dispenser.parts.base import (
    DRAWER_WAY,
    DRIVER_INSERTS,
    LIGHT_HOLE,
    PICO_INSERTS,
    RIM,
    SENSOR_INSERTS,
    STEPPER_INSERTS,
    base,
)
from dispenser.parts.carousel import SHAFT_BORE, carousel
from dispenser.parts.drawer import ACTUATOR_POCKET, RUNNER, drawer
from dispenser.parts.lid import SEAT, lid
from dispenser.parts.plate import BUZZER_BORE, FEET, plate

STEPPER_NAME = "Adafruit 858 28BYJ-48 stepper"
SHAFT_NAME = "Adafruit 858's output shaft, inside the stepper"
SHAFT = "shaft"
PICO_NAME = "Raspberry Pi Pico 2 W"
DRIVER_NAME = "Adafruit 3297 DRV8833 breakout"
REED_NAME = "Littelfuse 59140-1-S-02-A reed sensor"
ACTUATOR_NAME = "Littelfuse 57140-000 actuator"
BUZZER_NAME = "Soberton WST-1205S buzzer"
LED_NAME = "Kingbright WP7113ID5V LED"
POWER_NAME = "Raspberry Pi SC0623 12.5 W micro-USB power supply"
AWG_18_MM = 1.024  # ASTM B258, 18 AWG conductor; the SC0623 brief gives 18 AWG
POWER_JACKET_MM = 4.0  # estimate: the SC0623 brief gives no cable diameter
POWER_CABLE_MM = 1500.0  # SC0623 product brief: 1.5 m captive cable
SOLDER_CLEAR_MM = 1.0  # estimate: a lead leaves its solder joint this far out from the part
HOOKUP_MM = 0.405  # ASTM B258, 26 AWG conductor
AWG_24_MM = 0.511  # ASTM B258, 24 AWG conductor; the Littelfuse 59140 datasheet gives 24 AWG
REED_LEAD_MM = 300.0  # Littelfuse 59140 datasheet, lead option 02
STEPPER_LEAD_MM = 230.0  # Adafruit product 858 page: 23 cm cable
WHY = {
    "carousel": [
        Why(
            "Bottomless pockets turning over one gate in a fixed floor",
            "Only the pocket over the gate can empty, so a wrong dose cannot be released; the"
            " closed home sector shuts the gate between doses, and the pills ride on the fixed"
            " floor so the motor carries friction only, not the doses' weight.",
            requirements=(1, 9),
        )
    ],
    REED_NAME: [
        Why(
            "A reed sensor over a magnet in the drawer, not a lever switch",
            "Nothing touches the drawer, so the sensor cannot wear or be jammed by a pill, and"
            " the drawer slides out whole; the lever switch's maker CAD is behind a login.",
            requirements=(5,),
        )
    ],
    "plate": [
        Why(
            "The buzzer pressed into the bottom plate",
            "Sound leaves under the drum, so no grille breaks the faces, and the buzzer is fitted"
            " on the bench before the plate closes the base.",
            requirements=(4,),
        )
    ],
}
BUMPER_NAME = "3M Bumpon SJ5302"
BUMPER = Catalogue(file="bumper", grams=models.BUMPER_GRAMS, model=models.bumper)


def stepper_tabs() -> MountingHoles:
    return mounting_holes(STATOR, *STEPPER_TAB_HOLE, STEPPER_TABS)


def stepper(m: DispenserMaster) -> Bought:
    seats = mounting_hole_seats(stepper_tabs())
    return Bought(name=STEPPER_NAME, pose=m.stepper_at, item=STATOR, connectors=seats)


def shaft(m: DispenserMaster) -> Bought:
    seat = seat_of(round_faces(vendor_shape(ROTOR), models.SHAFT_DIAMETER / 2), Location())
    return Bought(
        name=SHAFT_NAME,
        pose=m.stepper_at,
        item=ROTOR,
        connectors={SHAFT: seat},
        ships_with=STEPPER_NAME,
    )


def under(spots: list[Location]) -> list[Location]:
    return [spot * UPSIDE_DOWN for spot in spots]


def inserts_under(m: DispenserMaster, spots: list[Location]) -> Hole:
    turned = under(spots)
    return insert_seats(Plane(turned[0]), turned, m.screw, fits=m.fits, stock=m.stock)


def stepper_inserts(m: DispenserMaster) -> Hole:
    return inserts_under(m, m.stepper_spots)


def plate_inserts(m: DispenserMaster) -> Hole:
    return inserts_under(m, m.plate_spots)


def reed_holes() -> MountingHoles:
    return mounting_holes(REED, *REED_HOLE, REED_HOLES)


def reed(m: DispenserMaster) -> Bought:
    seats = mounting_hole_seats(reed_holes())
    return Bought(name=REED_NAME, pose=m.reed_at, item=REED, connectors=seats)


def reed_inserts(m: DispenserMaster) -> Hole:
    return inserts_under(m, m.reed_spots)


def pico(m: DispenserMaster) -> Bought:
    connectors = board_connectors(PICO, m.pico_mount.holes)
    return Bought(name=PICO_NAME, pose=m.pico_at, item=PICO, connectors=connectors)


def driver(m: DispenserMaster) -> Bought:
    connectors = board_connectors(DRIVER, m.driver_mount.holes)
    return Bought(name=DRIVER_NAME, pose=m.driver_at, item=DRIVER, connectors=connectors)


def mounted_boards(m: DispenserMaster) -> list[tuple[Bought, BoardMount, Location, str]]:
    return [
        (pico(m), m.pico_mount, m.pico_at, PICO_INSERTS),
        (driver(m), m.driver_mount, m.driver_at, DRIVER_INSERTS),
    ]


@derived
def board_posts(m: DispenserMaster) -> Fastening:
    made = []
    for board, mount, at, seat in mounted_boards(m):
        posts = board_inserts(mount, at, fits=m.fits, stock=m.stock)
        held = Connector(board, MOUNTING_HOLES)
        made.append(set_in(posts, held, Connector(base(m), seat), BOARD_ROLE, stock=m.stock))
    return together(made)


@derived
def boards(m: DispenserMaster) -> Fastening:
    made = []
    for board, mount, at, seat in mounted_boards(m):
        posts = board_inserts(mount, at, fits=m.fits, stock=m.stock)
        holder = Connector(base(m), seat)
        screws = board_screws(board, mount, Location(), posts, holder, stock=m.stock)
        made.append(together([screws], [board]))
    return together(made)


@derived
def sensor_mounted(m: DispenserMaster) -> Fastening:
    held = reed(m)
    holes = reed_holes()
    local = [foot_on(Plane.XY, of=spot) for spot in holes.spots]
    through = Hole(
        face=Plane(local[0]),
        seats=seated(local, holes.board_top - holes.board_bottom),
        screw=m.screw,
        anchor=Anchor.CLEARANCE,
    )
    screws = screwed(
        through,
        reed_inserts(m),
        Connector(held, MOUNTING_HOLES),
        Connector(base(m), SENSOR_INSERTS),
        stock=m.stock,
    )
    return together([screws], [held])


@derived
def light(m: DispenserMaster) -> Fastening:
    held = Bought(name=LED_NAME, pose=m.led_at, item=LED)
    mates = held_by([held], OUTSIDE, Connector(base(m), LIGHT_HOLE))
    return Fastening(parts=[held], mates=[replace(mate, approach=-Axis.Y) for mate in mates])


@derived
def buzzer(m: DispenserMaster) -> Fastening:
    held = Bought(name=BUZZER_NAME, pose=m.buzzer_at, item=BUZZER)
    mates = held_by([held], OUTSIDE, Connector(plate(m), BUZZER_BORE))
    return Fastening(parts=[held], mates=[replace(mate, approach=-Axis.Z) for mate in mates])


@derived
def actuator(m: DispenserMaster) -> Fastening:
    held = Bought(name=ACTUATOR_NAME, pose=m.actuator_at, item=ACTUATOR)
    mates = held_by([held], OUTSIDE, Connector(drawer(m), ACTUATOR_POCKET))
    return Fastening(parts=[held], mates=[replace(mate, approach=-Axis.Z) for mate in mates])


@derived
def base_inserts(m: DispenserMaster) -> Fastening:
    made = base(m)
    for_stepper = set_in(
        stepper_inserts(m),
        Connector(stepper(m), MOUNTING_HOLES),
        Connector(made, STEPPER_INSERTS),
        stock=m.stock,
    )
    for_plate = set_in(
        plate_inserts(m), Connector(plate(m), LIPS), Connector(made, INSERTS), stock=m.stock
    )
    for_sensor = set_in(
        reed_inserts(m),
        Connector(reed(m), MOUNTING_HOLES),
        Connector(made, SENSOR_INSERTS),
        stock=m.stock,
    )
    return together([for_stepper, for_plate, for_sensor])


@derived
def stepper_mounted(m: DispenserMaster) -> Fastening:
    held = stepper(m)
    tabs = stepper_tabs()
    local = under([foot_on(Plane.XY, of=spot) for spot in tabs.spots])
    through = Hole(
        face=Plane(local[0]),
        seats=seated(local, tabs.board_top - tabs.board_bottom),
        screw=m.screw,
        anchor=Anchor.CLEARANCE,
    )
    screws = screwed(
        through,
        stepper_inserts(m),
        Connector(held, MOUNTING_HOLES),
        Connector(base(m), STEPPER_INSERTS),
        stock=m.stock,
    )
    rotor = shaft(m)
    turning = Mate(
        CAROUSEL_TURN,
        Kind.REVOLUTE,
        child=Connector(rotor, SHAFT),
        parent=Connector(held, OUTSIDE),
        at=Location(m.shaft_top),
        limits=JointRange(low=0.0, high=360.0),
        servo=held,
        approach=-Axis.Z,
    )
    return together([screws, Fastening(parts=[rotor], mates=[turning])], [held])


@derived
def turning_carousel(m: DispenserMaster) -> Fastening:
    made = carousel(m)
    on_shaft = Mate(
        f"carousel on {SHAFT_NAME}",
        Kind.RIGID,
        child=Connector(made, SHAFT_BORE),
        parent=Connector(SHAFT_NAME, SHAFT),
        approach=-Axis.Z,
    )
    return Fastening(parts=[made], mates=[on_shaft])


@derived
def closed_lid(m: DispenserMaster) -> Fastening:
    made = lid(m)
    seat = Mate(
        "lid on base",
        Kind.RIGID,
        child=Connector(made, SEAT),
        parent=Connector(base(m), RIM),
        approach=-Axis.Z,
    )
    return Fastening(parts=[made], mates=[seat])


@derived
def feet(m: DispenserMaster) -> Fastening:
    pads = [Bought(name=BUMPER_NAME, pose=at, item=BUMPER) for at in m.feet_at]
    mates = held_by(pads, OUTSIDE, Connector(plate(m), FEET))
    return Fastening(parts=pads, mates=[replace(mate, approach=Axis.Z) for mate in mates])


@derived
def closed_plate(m: DispenserMaster) -> Fastening:
    made = plate(m)
    heads = under(m.plate_spots)
    through = Hole(
        face=Plane(heads[0]),
        seats=seated(heads, m.plate_thickness),
        screw=m.screw,
        anchor=Anchor.CLEARANCE,
    )
    return screwed(
        through,
        plate_inserts(m),
        Connector(made, LIPS),
        Connector(base(m), INSERTS),
        stock=m.stock,
    )


@derived
def sliding_drawer(m: DispenserMaster) -> Fastening:
    made = drawer(m)
    slide = Mate(
        DRAWER_SLIDE,
        Kind.PRISMATIC,
        child=Connector(made, RUNNER),
        parent=Connector(base(m), DRAWER_WAY),
        at=m.drawer_way,
        limits=JointRange(low=0.0, high=m.drawer_travel),
        approach=Axis.Y,
    )
    return Fastening(parts=[], mates=[slide])


CUT_TO_FIT = CutToFit()


def lead(
    name: str,
    wires: tuple[str, ...],
    diameter: float = HOOKUP_MM,
    length: float | CutToFit = CUT_TO_FIT,
    bill: Bill = NO_BILL,
) -> Cable:
    return Cable(
        name=name,
        wires=tuple(Wire(name=wire, diameter=diameter, colour=wire) for wire in wires),
        plugs=(
            Plug(name="from", model=None, pinout=wires),
            Plug(name="to", model=None, pinout=wires),
        ),
        construction=Discrete(),
        twist_rating=0.0,
        length=length,
        bill=bill,
    )


POWER_CABLE = Cable(
    name=POWER_NAME,
    wires=tuple(Wire(name=name, diameter=AWG_18_MM, colour=name) for name in ("VBUS", "GND")),
    plugs=(
        Plug(name="micro-B", model=None, pinout=("VBUS", "GND")),
        Plug(name="mains", model=None, pinout=("VBUS", "GND")),
    ),
    construction=Jacketed(diameter=POWER_JACKET_MM),
    twist_rating=0.0,
    length=POWER_CABLE_MM,
    bill=NO_BILL,
)
LEADS = {
    DRIVER_NAME: lead("driver leads, 26 AWG", ("VM", "GND", "AIN1", "AIN2", "BIN1", "BIN2")),
    BUZZER_NAME: lead("buzzer leads, 26 AWG, with its 2N3904 switch", ("BUZZ", "VBUS")),
    LED_NAME: lead("light leads, 26 AWG", ("LIGHT", "GND")),
}
SHIPPED = {
    STEPPER_NAME: lead(
        "28BYJ-48 lead",
        ("blue", "pink", "yellow", "orange", "red"),
        length=STEPPER_LEAD_MM,
        bill=Bill(ships_with=STEPPER_NAME),
    ),
    REED_NAME: lead(
        "59140 leads",
        ("SENSE", "GND"),
        diameter=AWG_24_MM,
        length=REED_LEAD_MM,
        bill=Bill(ships_with=REED_NAME),
    ),
}


def at(part: Part, point: Location) -> RoutePoint:
    return RoutePoint(part=part, at=part.pose.inverse() * point)


def beside(part: Bought, toward: Axis) -> RoutePoint:
    block = vendor_block(part.item, part.pose)
    face = reach([block], toward=normal_to(toward.direction, through=Location()))
    middle = through_the_middle([block], along=face)
    return at(part, crossing(face.offset(SOLDER_CLEAR_MM), middle))


def across(of: Location) -> Plane:
    return parallel(Plane.XZ, through=of)


def harness(m: DispenserMaster) -> list[Route]:
    power = Route(
        cable=POWER_CABLE,
        plugged=(
            Connector(pico(m), PICO_USB.name),
            RoutePoint(part=base(m), at=m.cable_on_counter),
        ),
        through=((RoutePoint(part=base(m), at=m.cable_exit),),),
    )
    shell, board = base(m), pico(m)
    run = parallel(Plane.XY, through=m.light_at)
    side = Plane.YZ.offset(m.pocket_start)
    drawer_back = Pos(Y=-m.drawer_back)
    up_the_side = (
        at(shell, corner(across(m.reed_at), side, run)),
        at(shell, corner(across(drawer_back), side, run)),
    )
    led = Bought(name=LED_NAME, pose=m.led_at, item=LED)
    sounder = Bought(name=BUZZER_NAME, pose=m.buzzer_at, item=BUZZER)
    tail = beside(led, Axis.Y)
    to_board = beside(board, -Axis.X)
    leads = [
        Route(
            cable=LEADS[LED_NAME],
            plugged=(tail, beside(board, Axis.X)),
            through=((at(shell, corner(across(tail.frame), side, run)), *up_the_side),),
        ),
        Route(
            cable=LEADS[DRIVER_NAME],
            plugged=(beside(driver(m), Axis.X), to_board),
            through=(
                (
                    at(
                        shell,
                        corner(
                            run, parallel(Plane.YZ, through=to_board.frame), across(m.driver_at)
                        ),
                    ),
                ),
            ),
        ),
        Route(
            cable=LEADS[BUZZER_NAME],
            plugged=(beside(sounder, Axis.Z), beside(board, -Axis.Z)),
            through=((),),
        ),
    ]
    stepper_lead = Route(
        cable=SHIPPED[STEPPER_NAME],
        plugged=(beside(stepper(m), Axis.Y), beside(driver(m), -Axis.Y)),
        through=((),),
    )
    reed_leads = Route(
        cable=SHIPPED[REED_NAME],
        plugged=(beside(reed(m), Axis.X), beside(board, Axis.X)),
        through=(up_the_side,),
    )
    return [power, *leads, stepper_lead, reed_leads]


PRODUCT = Assembly(
    "dispenser",
    Assembly(
        "base",
        job(base, MASTER),
        job(base_inserts, MASTER),
        job(board_posts, MASTER),
        job(light, MASTER),
        job(stepper_mounted, MASTER),
        job(sensor_mounted, MASTER),
        job(boards, MASTER),
    ),
    Assembly("plate", job(plate, MASTER), job(buzzer, MASTER), job(feet, MASTER), bench=True),
    job(closed_plate, MASTER),
    Assembly("carousel", job(turning_carousel, MASTER), job(closed_lid, MASTER)),
    Assembly("drawer", job(drawer, MASTER), job(actuator, MASTER), bench=True),
    job(sliding_drawer, MASTER),
    cables=lambda: harness(MASTER),
)
