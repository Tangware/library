from collections.abc import Callable

from build123d import Axis, Location, Pos
from cad.assembly.tree import Assembly, job
from cad.cables.models import Cable, Jacketed, Plug, Route, RoutePoint, Wire
from cad.library.bought.catalogue import Bill
from cad.library.bought.vendor import Bought
from cad.library.derived import derived
from cad.library.features.hardware import Fastening, insert_seat
from cad.library.mates import Connector, JointRange, Kind, Mate, meshing, named
from cad.library.shapes import OUTSIDE, Part
from cad.library.standard.fasteners import DOWEL, UNDER_HEAD, Pin, Screw, ThreadedInsert

from cessna.master import (
    BATTERY_HOLDER,
    DRIVE,
    LEFT,
    MASTER,
    MOTOR,
    MOTOR_OUTPUT,
    RETRACTED_DEG,
    RIGHT,
    CessnaMaster,
    side_name,
)
from cessna.models.motor import GEARMOTOR, Gearmotor
from cessna.parts.moving import (
    MOTOR_PINION,
    OUTPUT_SHAFT,
    RACK,
    SHAFT_YOKE,
    SIDE_TUBE,
    SPIDER,
    SPRING_LEG,
    motor_pinion,
    output_shaft,
    rack,
    shaft_yoke,
    side_tube,
    spider,
    spring_leg,
    wheel,
)
from cessna.parts.structure import (
    MAIN_PLATE,
    MOTOR_SADDLE,
    PILLOW_BLOCK,
    PIVOT_BRACKET,
    STAND,
    main_plate,
    motor_saddle,
    pillow_block,
    pivot_bracket,
    stand,
    tube_hanger,
)

MOTOR_NAME = "Pololu 3069 298:1 Micro Metal Gearmotor HPCB 6V"
HOLDER_NAME = "Pololu 1159 4-AA battery holder with switch"
FROM_ABOVE = -Axis.Z
FROM_BELOW = Axis.Z
FROM_THE_LEFT = Axis.X
LEAD_WIRES = ("red", "black")
AWG_24_MM = 0.511
LEADS_BUNDLE_MM = 3.0
LEADS_LENGTH_MM = 200.0
LEADS = Cable(
    name="battery holder leads",
    wires=tuple(Wire(name=name, diameter=AWG_24_MM, colour=name) for name in LEAD_WIRES),
    plugs=(
        Plug(name="holder", model=None, pinout=LEAD_WIRES),
        Plug(name="motor", model=None, pinout=LEAD_WIRES),
    ),
    construction=Jacketed(diameter=LEADS_BUNDLE_MM),
    twist_rating=0.0,
    length=LEADS_LENGTH_MM,
    bill=Bill(ships_with=HOLDER_NAME),
)


def on(part: Part | str) -> Connector:
    return Connector(part, OUTSIDE)


def fixed(child: Connector, parent: Connector, approach: Axis, n: int | None = None) -> Mate:
    first, second = (named(each.part) for each in (child, parent))
    mark = "" if n is None else f" {n}"
    return Mate(
        f"{first} on {second}{mark}", Kind.RIGID, child=child, parent=parent, approach=approach
    )


def insert_at(name: str, m: CessnaMaster, spot: Location) -> ThreadedInsert:
    return ThreadedInsert(
        name=name,
        pose=insert_seat(spot, m.screw, fits=m.fits, stock=m.stock),
        designation=m.stock.inserts[m.screw],
        maker=m.stock.insert_maker,
    )


def screw_at(name: str, m: CessnaMaster, at: Location, length: float) -> Screw:
    return Screw(name=name, pose=at, size=m.screw, length=length, grade=m.stock.fastener_grade)


def dowel_at(name: str, m: CessnaMaster, at: Location, length: float) -> Pin:
    return Pin(name=name, pose=at, diameter=m.dowel_diameter, length=length, standard=DOWEL)


def inward(spot: Location) -> Axis:
    return -Axis(spot)


def inserts_on(name: str, m: CessnaMaster, spots: tuple[Location, ...], into: Part) -> Fastening:
    made = [insert_at(name, m, spot) for spot in spots]
    return Fastening(
        parts=list(made),
        mates=[
            fixed(on(each), on(into), inward(spot), n)
            for n, (each, spot) in enumerate(zip(made, spots, strict=True))
        ],
    )


def screws_at(
    name: str,
    m: CessnaMaster,
    spots: tuple[Location, ...],
    held: Part | str,
    rise: float,
    length: float,
) -> Fastening:
    made = [screw_at(name, m, spot * Pos(Z=rise), length) for spot in spots]
    return Fastening(
        parts=list(made),
        mates=[
            fixed(Connector(each, UNDER_HEAD), on(held), inward(spot), n)
            for n, (each, spot) in enumerate(zip(made, spots, strict=True))
        ],
    )


def toward_the_middle(side: float) -> Axis:
    return Axis((0.0, 0.0, 0.0), (-side, 0.0, 0.0))


def along_the_tube(m: CessnaMaster, side: float) -> Axis:
    return -Axis(m.tube(side))


@derived
def the_stand(m: CessnaMaster) -> Fastening:
    made = stand(m)
    holder = Bought(name=HOLDER_NAME, pose=m.holder_at, item=BATTERY_HOLDER)
    spots = (*m.column_spots(m.fore_column_y), *m.column_spots(m.aft_column_y))
    inserts = inserts_on("column insert", m, spots, made)
    return Fastening(
        parts=[made, holder, *inserts.parts],
        mates=[fixed(on(holder), on(made), FROM_ABOVE), *inserts.mates],
    )


@derived
def the_plate(m: CessnaMaster) -> Fastening:
    plate = main_plate(m)
    spots = (*m.column_spots(m.fore_column_y), *m.column_spots(m.aft_column_y))
    bolts = screws_at("column screw", m, spots, plate, m.plate_thickness, m.short_screw)
    return Fastening(
        parts=[plate, *bolts.parts],
        mates=[fixed(on(plate), on(STAND), FROM_ABOVE), *bolts.mates],
    )


@derived
def left_pillow(m: CessnaMaster) -> Fastening:
    block = pillow_block(m, LEFT)
    inserts = inserts_on("pillow block insert", m, m.pillow_spots(LEFT), block)
    return Fastening(
        parts=[block, *inserts.parts],
        mates=[fixed(on(block), on(MAIN_PLATE), FROM_BELOW), *inserts.mates],
    )


@derived
def the_shaft(m: CessnaMaster) -> Fastening:
    shaft = output_shaft(m)
    return Fastening(
        parts=[shaft],
        mates=[
            Mate(
                OUTPUT_SHAFT,
                Kind.REVOLUTE,
                child=on(shaft),
                parent=on(side_name(LEFT, PILLOW_BLOCK)),
                at=m.shaft_frame,
                approach=toward_the_middle(RIGHT),
            )
        ],
    )


@derived
def right_pillow(m: CessnaMaster) -> Fastening:
    block = pillow_block(m, RIGHT)
    inserts = inserts_on("pillow block insert", m, m.pillow_spots(RIGHT), block)
    return Fastening(
        parts=[block, *inserts.parts],
        mates=[
            fixed(on(block), on(side_name(LEFT, PILLOW_BLOCK)), toward_the_middle(RIGHT)),
            *inserts.mates,
        ],
    )


@derived
def the_bracket(m: CessnaMaster) -> Fastening:
    bracket = pivot_bracket(m)
    return Fastening(parts=[bracket], mates=[fixed(on(bracket), on(MAIN_PLATE), FROM_ABOVE)])


@derived
def the_rack(m: CessnaMaster) -> Fastening:
    sector = rack(m)
    pin = dowel_at("rack pivot", m, m.pivot_dowel_at, m.pivot_dowel)
    return Fastening(
        parts=[sector, pin],
        mates=[
            Mate(
                RACK,
                Kind.REVOLUTE,
                child=on(sector),
                parent=on(PIVOT_BRACKET),
                at=m.rack_frame,
                approach=FROM_BELOW,
            ),
            fixed(on(pin), on(PIVOT_BRACKET), FROM_THE_LEFT),
            meshing(RACK, OUTPUT_SHAFT),
        ],
    )


@derived
def bracket_screws(m: CessnaMaster) -> Fastening:
    spots = (*m.pillow_spots(LEFT), *m.pillow_spots(RIGHT))
    return screws_at("bracket screw", m, spots, PIVOT_BRACKET, 2 * m.plate_thickness, m.long_screw)


@derived
def the_motor(m: CessnaMaster) -> Fastening:
    saddle = motor_saddle(m)
    motor = Gearmotor(
        name=MOTOR_NAME, pose=m.motor_at, item=MOTOR, model=GEARMOTOR, stress_analysed=True
    )
    shaft = Bought(
        name=f"{MOTOR_NAME} shaft", pose=m.motor_at, item=MOTOR_OUTPUT, ships_with=MOTOR_NAME
    )
    pinion = motor_pinion(m)
    inserts = inserts_on("motor saddle insert", m, m.saddle_spots, saddle)
    return Fastening(
        parts=[saddle, *inserts.parts, motor, shaft, pinion],
        mates=[
            fixed(on(saddle), on(MAIN_PLATE), FROM_BELOW),
            *inserts.mates,
            fixed(on(motor), on(saddle), FROM_ABOVE),
            Mate(
                DRIVE,
                Kind.REVOLUTE,
                child=on(pinion),
                parent=on(saddle),
                at=m.drive_frame,
                servo=MOTOR_NAME,
                limits=JointRange(0.0, m.drive_turn(RETRACTED_DEG)),
                approach=FROM_THE_LEFT,
            ),
            fixed(on(shaft), on(pinion), FROM_THE_LEFT),
            Mate(
                "pinion on the motor",
                Kind.REVOLUTE,
                child=on(shaft),
                parent=on(motor),
                at=m.drive_frame,
                closes=True,
                approach=FROM_THE_LEFT,
            ),
            meshing(MOTOR_PINION, RACK),
        ],
    )


@derived
def motor_screws(m: CessnaMaster) -> Fastening:
    return screws_at(
        "motor saddle screw", m, m.saddle_spots, MOTOR_SADDLE, m.plate_thickness, m.short_screw
    )


@derived
def the_yoke(m: CessnaMaster, side: float) -> Fastening:
    yoke = shaft_yoke(m, side)
    return Fastening(
        parts=[yoke], mates=[fixed(on(yoke), on(OUTPUT_SHAFT), toward_the_middle(side))]
    )


@derived
def the_spider(m: CessnaMaster, side: float) -> Fastening:
    cross = spider(m, side)
    spots = (*m.yoke_screw_spots(side), *m.tube_screw_spots(side))
    inserts = inserts_on(f"{side_name(side, 'spider')} insert", m, spots, cross)
    return Fastening(
        parts=[cross, *inserts.parts],
        mates=[
            Mate(
                side_name(side, "first pin"),
                Kind.REVOLUTE,
                child=on(cross),
                parent=on(side_name(side, SHAFT_YOKE)),
                at=m.first_pin(side),
                approach=toward_the_middle(side),
            ),
            *inserts.mates,
        ],
    )


@derived
def first_pin_screws(m: CessnaMaster, side: float) -> Fastening:
    return screws_at(
        "first pin screw",
        m,
        m.yoke_screw_spots(side),
        side_name(side, SPIDER),
        m.fork_wall + m.fits.sliding,
        m.short_screw,
    )


@derived
def the_tube(m: CessnaMaster, side: float) -> Fastening:
    tube = side_tube(m, side)
    return Fastening(
        parts=[tube],
        mates=[
            Mate(
                side_name(side, "second pin"),
                Kind.REVOLUTE,
                child=on(tube),
                parent=on(side_name(side, SPIDER)),
                at=m.second_pin(side),
                approach=along_the_tube(m, side),
            )
        ],
    )


@derived
def second_pin_screws(m: CessnaMaster, side: float) -> Fastening:
    return screws_at(
        "second pin screw",
        m,
        m.tube_screw_spots(side),
        side_name(side, SPIDER),
        m.fork_wall + m.fits.sliding,
        m.short_screw,
    )


@derived
def the_hanger(m: CessnaMaster, side: float) -> Fastening:
    hanger = tube_hanger(m, side)
    inserts = inserts_on("tube hanger insert", m, m.hanger_spots(side), hanger)
    return Fastening(
        parts=[hanger, *inserts.parts],
        mates=[
            fixed(on(hanger), on(MAIN_PLATE), toward_the_middle(side)),
            Mate(
                side_name(side, "tube in its hanger"),
                Kind.REVOLUTE,
                child=on(side_name(side, SIDE_TUBE)),
                parent=on(hanger),
                at=m.hanger(side),
                closes=True,
                approach=along_the_tube(m, side),
            ),
            *inserts.mates,
        ],
    )


@derived
def the_leg(m: CessnaMaster, side: float) -> Fastening:
    leg = spring_leg(m, side)
    pin = dowel_at(side_name(side, "leg pin"), m, m.leg_pin(side), m.leg_dowel)
    axle_insert = insert_at("axle insert", m, m.axle_face(side))
    return Fastening(
        parts=[leg, axle_insert, pin],
        mates=[
            fixed(on(leg), on(side_name(side, SIDE_TUBE)), along_the_tube(m, side)),
            fixed(on(axle_insert), on(leg), inward(m.axle_face(side))),
            fixed(on(pin), on(leg), -Axis(m.leg_pin(side))),
        ],
    )


@derived
def the_wheel(m: CessnaMaster, side: float) -> Fastening:
    rolling = wheel(m, side)
    screw = screw_at("axle screw", m, m.axle_screw_at(side), m.long_screw)
    from_outside = -Axis(m.axle(side))
    return Fastening(
        parts=[rolling, screw],
        mates=[
            Mate(
                side_name(side, "wheel"),
                Kind.REVOLUTE,
                child=on(rolling),
                parent=on(side_name(side, SPRING_LEG)),
                at=m.axle(side),
                approach=from_outside,
            ),
            fixed(Connector(screw, UNDER_HEAD), on(rolling), from_outside),
        ],
    )


@derived
def side_fixings(m: CessnaMaster, side: float) -> Fastening:
    pin = dowel_at(side_name(side, "yoke pin"), m, m.hub_pin(side), m.short_dowel)
    bolts = screws_at(
        "tube hanger screw",
        m,
        m.hanger_spots(side),
        MAIN_PLATE,
        m.plate_thickness,
        m.short_screw,
    )
    return Fastening(
        parts=[pin, *bolts.parts],
        mates=[
            fixed(on(pin), on(side_name(side, SHAFT_YOKE)), -Axis(m.hub_pin(side))),
            *bolts.mates,
        ],
    )


def battery_leads(m: CessnaMaster, find: Callable[[str], Part]) -> list[Route]:
    holder, motor = find(HOLDER_NAME), find(MOTOR_NAME)
    return [
        Route(
            cable=LEADS,
            plugged=(
                RoutePoint(part=holder, at=holder.pose.inverse() * m.lead_start),
                RoutePoint(part=motor, at=motor.pose.inverse() * m.lead_end),
            ),
            through=(
                (
                    RoutePoint(part=holder, at=holder.pose.inverse() * m.lead_off_the_holder),
                    RoutePoint(part=holder, at=holder.pose.inverse() * m.lead_up_the_column),
                    RoutePoint(part=holder, at=holder.pose.inverse() * m.lead_under_the_motor),
                    RoutePoint(part=holder, at=holder.pose.inverse() * m.lead_behind_the_motor),
                ),
            ),
        )
    ]


def side_jobs(m: CessnaMaster, side: float) -> Assembly:
    name = side_name(side, "gear")
    return Assembly(
        name,
        Assembly(
            f"{name} unit",
            job(the_yoke, m, side),
            Assembly(f"{name} spider", job(the_spider, m, side), bench=True),
            job(first_pin_screws, m, side),
            job(the_tube, m, side),
            job(second_pin_screws, m, side),
            job(the_hanger, m, side),
            job(the_leg, m, side),
            job(the_wheel, m, side),
            bench=True,
        ),
        job(side_fixings, m, side),
    )


CESSNA = Assembly(
    "cessna",
    Assembly("stand", job(the_stand, MASTER)),
    Assembly("plate", job(the_plate, MASTER)),
    Assembly(
        "output shaft",
        job(left_pillow, MASTER),
        job(the_shaft, MASTER),
        job(right_pillow, MASTER),
        bench=True,
    ),
    Assembly("bracket", job(the_bracket, MASTER), job(the_rack, MASTER), bench=True),
    job(bracket_screws, MASTER),
    Assembly("motor", job(the_motor, MASTER), bench=True),
    job(motor_screws, MASTER),
    *(side_jobs(MASTER, side) for side in (LEFT, RIGHT)),
    cables=lambda find: battery_leads(MASTER, find),
    stress_analysed=False,
)
