from collections.abc import Callable

from build123d import Axis, Location, Pos
from cad.assembly.tree import Assembly, Job, job
from cad.cables.models import Cable, CutToFit, Discrete, Plug, Route, RoutePoint, Splice, Wire
from cad.library.bought.catalogue import NO_BILL, Bill
from cad.library.bought.vendor import Bought
from cad.library.derived import derived
from cad.library.features.hardware import Fastening, insert_seat
from cad.library.mates import Connector, Kind, Mate, meshing
from cad.library.shapes import OUTSIDE, Part
from cad.library.standard.fasteners import DOWEL, UNDER_HEAD, Pin, Screw, ThreadedInsert

from v8.master import (
    BATTERY_HOLDER,
    CELL,
    CRANK,
    CYLINDERS,
    JOURNALS,
    LEFT_BANK_DEG,
    MASTER,
    MOTOR,
    MOTOR_OUTPUT,
    REST_TURN_DEG,
    RIGHT_BANK_DEG,
    SLEEVE,
    SWITCH,
    VALVES,
    CrankPiece,
    Cylinder,
    V8Master,
    Valve,
)
from v8.models import wire
from v8.parts.block import BLOCK, REAR_PLATE, block, motor_cap, rear_plate
from v8.parts.crank import crank
from v8.parts.moving import PISTON, piston, rod
from v8.parts.valvetrain import (
    BATTERY_TRAY,
    CAMSHAFT,
    CRANK_GEAR,
    LEFT_HEAD,
    LEFT_RAIL,
    RIGHT_HEAD,
    RIGHT_RAIL,
    battery_tray,
    camshaft,
    crank_gear,
    left_head,
    left_header,
    left_keeper,
    left_rail,
    lifter,
    lobe,
    pushrod,
    right_head,
    right_header,
    right_keeper,
    right_rail,
    rocker,
    spark_plug,
    strap,
    toggle_link,
    valve_cap,
    valve_stem,
)

MOTOR_NAME = "Pololu 3069 298:1 Micro Metal Gearmotor HPCB 6V"
HOLDER_NAME = "MPD BC4AAW 4-AA battery holder"
SWITCH_NAME = "E-Switch RD11131121 rocker switch"
SLEEVE_NAME = "TE Raychem RNF-100-3/32-BK heat-shrink sleeve"
CELL_NAME = "Energizer EN91 AA cell"
FROM_THE_REAR = -Axis.Y
FROM_THE_FRONT = Axis.Y
FROM_ABOVE = -Axis.Z
ALONG_THE_LAYERS = Axis.Y
RED, BLACK = wire.CONDUCTORS
SPLICE = "black splice"
LEADS_LENGTH_MM = 150.0


def holder_leads(m: V8Master) -> Cable:
    return Cable(
        name="battery holder leads",
        wires=tuple(
            Wire(name=name, diameter=m.holder_leads.diameter, colour=name)
            for name in wire.CONDUCTORS
        ),
        plugs=(
            Plug(name="holder", model=None, pinout=wire.CONDUCTORS),
            Plug(name="switch", model=None, pinout=(RED,)),
            Plug(name=SPLICE, model=None, pinout=(BLACK,)),
        ),
        construction=Discrete(),
        twist_rating=0.0,
        length=LEADS_LENGTH_MM,
        bill=Bill(ships_with=HOLDER_NAME),
    )


def switch_leads(trunk: Cable) -> Cable:
    return Cable(
        name="switch leads",
        wires=tuple(
            Wire(name=name, diameter=wire.DIAMETER, colour=name) for name in wire.CONDUCTORS
        ),
        plugs=(
            Plug(name="switch", model=None, pinout=(RED,)),
            Plug(name="motor", model=None, pinout=wire.CONDUCTORS),
            Plug(name=SPLICE, model=Splice(into=trunk), pinout=(BLACK,)),
        ),
        construction=Discrete(),
        twist_rating=0.0,
        length=CutToFit(),
        bill=NO_BILL,
    )


def on(part: Part | str) -> Connector:
    return Connector(part, OUTSIDE)


def fixed(child: Connector, parent: Connector, approach: Axis = FROM_THE_REAR) -> Mate:
    names = [
        each.part if isinstance(each.part, str) else each.part.name for each in (child, parent)
    ]
    return Mate(
        f"{names[0]} on {names[1]}", Kind.RIGID, child=child, parent=parent, approach=approach
    )


def insert_at(name: str, m: V8Master, spot: Location) -> ThreadedInsert:
    return ThreadedInsert(
        name=name,
        pose=insert_seat(spot, m.screw, fits=m.fits, stock=m.stock),
        designation=m.stock.inserts[m.screw],
        maker=m.stock.insert_maker,
    )


def screw_at(name: str, m: V8Master, at: Location, length: float) -> Screw:
    return Screw(name=name, pose=at, size=m.screw, length=length, grade=m.stock.fastener_grade)


def inward(spot: Location) -> Axis:
    return -Axis(spot)


def inserts_on(name: str, m: V8Master, spots: tuple[Location, ...], into: Part | str) -> Fastening:
    made = [insert_at(name, m, spot) for spot in spots]
    return Fastening(
        parts=list(made),
        mates=[
            numbered(fixed(on(each), on(into), inward(spot)), n)
            for n, (each, spot) in enumerate(zip(made, spots, strict=True))
        ],
    )


def screws_at(
    name: str,
    m: V8Master,
    spots: tuple[Location, ...],
    held: Part | str,
    rise: float,
    length: float | None = None,
) -> Fastening:
    made = [screw_at(name, m, spot * Pos(Z=rise), length or m.long_screw) for spot in spots]
    return Fastening(
        parts=list(made),
        mates=[
            numbered(fixed(Connector(each, UNDER_HEAD), on(held), inward(spot)), n)
            for n, (each, spot) in enumerate(zip(made, spots, strict=True))
        ],
    )


def numbered(mate: Mate, n: int) -> Mate:
    return Mate(
        f"{mate.name} {n}",
        mate.kind,
        child=mate.child,
        parent=mate.parent,
        approach=mate.approach,
    )


@derived
def the_block(m: V8Master) -> Fastening:
    made = block(m)
    inserts = [insert_at("rear plate insert", m, spot) for spot in m.plate_spots]
    spots = tuple(
        spot
        for deg in (LEFT_BANK_DEG, RIGHT_BANK_DEG)
        for spot in (*m.head_spots(deg), *m.rail_spots(deg), *m.keeper_spots(deg))
    )
    top = inserts_on("block insert", m, spots, made)
    return Fastening(
        parts=[made, *inserts, *top.parts],
        mates=[*(fixed(on(each), on(made), Axis.Y) for each in inserts), *top.mates],
    )


@derived
def piston_unit(m: V8Master, cylinder: Cylinder) -> Fastening:
    wrist = m.wrist(cylinder, REST_TURN_DEG)
    head = piston(m, wrist, cylinder.number)
    return Fastening(
        parts=[head],
        mates=[
            Mate(
                f"{cylinder.name} piston",
                Kind.PRISMATIC,
                child=on(head),
                parent=on(BLOCK),
                at=wrist,
                approach=-Axis(wrist),
            ),
        ],
    )


@derived
def rod_unit(m: V8Master, cylinder: Cylinder) -> Fastening:
    wrist = m.wrist(cylinder, REST_TURN_DEG)
    down = -Axis(wrist)
    arm = rod(m, m.rod_frame(cylinder))
    pin = m.crank_pin(cylinder.journal, REST_TURN_DEG, m.cylinder_y(cylinder))
    journal_piece = m.crank_pieces[cylinder.journal + 1].name
    name = cylinder.name
    dowel = Pin(
        name="wrist pin",
        pose=m.wrist_pin_at(cylinder),
        diameter=m.wrist_pin_diameter,
        length=m.wrist_pin_length,
        standard=DOWEL,
    )
    return Fastening(
        parts=[arm, dowel],
        mates=[
            Mate(
                f"{name} wrist",
                Kind.REVOLUTE,
                child=on(arm),
                parent=on(f"{PISTON} {cylinder.number}"),
                at=m.hinge_at(wrist),
                approach=-down,
            ),
            Mate(
                f"{name} big end",
                Kind.REVOLUTE,
                child=on(arm),
                parent=on(journal_piece),
                at=m.hinge_at(pin),
                closes=True,
                approach=down,
            ),
            fixed(on(dowel), on(f"{PISTON} {cylinder.number}")),
        ],
    )


def journal_jobs(m: V8Master, journal: int) -> list[Job]:
    return [
        job(unit, m, each) for each in CYLINDERS if each.journal == journal for unit in (rod_unit,)
    ]


@derived
def crank_piece(m: V8Master, piece: CrankPiece) -> Fastening:
    made = crank(m, piece)
    parts: list[Part] = [made]
    mates: list[Mate] = []
    if piece.low is None:
        nose = inserts_on("nose insert", m, m.nose_spots, made)
        parts += nose.parts
        mates += nose.mates
        mates.append(
            Mate(
                CRANK,
                Kind.REVOLUTE,
                child=on(made),
                parent=on(BLOCK),
                at=m.crank_turn,
                servo=MOTOR_NAME,
                approach=FROM_THE_REAR,
            )
        )
    else:
        below = m.crank_pieces[piece.index - 1]
        spot = m.crank_frame(piece) * m.pin_spot(piece, piece.low)
        screw = screw_at(f"{piece.name} pin screw", m, spot, m.pin_screw_length)
        parts.append(screw)
        mates += [fixed(on(made), on(below.name)), fixed(Connector(screw, UNDER_HEAD), on(made))]
    if piece.high is not None:
        face = m.crank_frame(piece) * m.pin_spot(piece, piece.high) * Pos(Z=m.arm)
        insert = insert_at(f"{piece.name} pin insert", m, face)
        parts.append(insert)
        mates.append(fixed(on(insert), on(made)))
    return Fastening(parts=parts, mates=mates)


@derived
def closing_plate(m: V8Master) -> Fastening:
    plate = rear_plate(m)
    screws = [
        screw_at("rear plate screw", m, m.plate_screw_at(spot), m.plate_screw_length)
        for spot in m.plate_spots
    ]
    return Fastening(
        parts=[plate, *screws],
        mates=[
            fixed(on(plate), on(BLOCK)),
            *(fixed(Connector(each, UNDER_HEAD), on(plate)) for each in screws),
        ],
    )


@derived
def motor_in_plate(m: V8Master) -> Fastening:
    motor = Bought(name=MOTOR_NAME, pose=m.motor_at, item=MOTOR)
    shaft = Bought(
        name=f"{MOTOR_NAME} shaft", pose=m.motor_at, item=MOTOR_OUTPUT, ships_with=MOTOR_NAME
    )
    return Fastening(
        parts=[motor, shaft],
        mates=[
            fixed(on(motor), on(REAR_PLATE)),
            fixed(on(shaft), on(m.crank_pieces[-1].name)),
            Mate(
                "crank on the motor",
                Kind.REVOLUTE,
                child=on(shaft),
                parent=on(motor),
                at=m.crank_turn,
                closes=True,
                approach=FROM_THE_REAR,
            ),
        ],
    )


@derived
def cap_inserts(m: V8Master) -> Fastening:
    spots = (*m.cap_spots, *m.tray_spots)
    inserts = [insert_at("rear plate outer insert", m, spot) for spot in spots]
    return Fastening(
        parts=list(inserts), mates=[fixed(on(each), on(REAR_PLATE)) for each in inserts]
    )


@derived
def capped(m: V8Master) -> Fastening:
    cap = motor_cap(m)
    screws = [
        screw_at("motor cap screw", m, spot * Pos(Z=m.cap_flange), m.plate_screw_length)
        for spot in m.cap_spots
    ]
    return Fastening(
        parts=[cap, *screws],
        mates=[
            fixed(on(cap), on(REAR_PLATE)),
            *(fixed(Connector(each, UNDER_HEAD), on(cap)) for each in screws),
        ],
    )


def journals(m: V8Master, journal: int) -> Assembly:
    return Assembly(
        f"journal {journal + 1}",
        Assembly(
            f"journal {journal + 1} pistons",
            *(job(piston_unit, m, each) for each in CYLINDERS if each.journal == journal),
            stress_analysed=False,
        ),
        *journal_jobs(m, journal),
        job(crank_piece, m, m.crank_pieces[journal + 1]),
    )


def head_name(valve: Valve) -> str:
    return LEFT_HEAD if valve.cylinder.bank_deg == LEFT_BANK_DEG else RIGHT_HEAD


def rail_name(valve: Valve) -> str:
    return LEFT_RAIL if valve.cylinder.bank_deg == LEFT_BANK_DEG else RIGHT_RAIL


def bank_builders(deg: float) -> tuple[Callable[[V8Master], Part], Callable[[V8Master], Part]]:
    return (left_head, left_rail) if deg == LEFT_BANK_DEG else (right_head, right_rail)


@derived
def stem(m: V8Master, valve: Valve) -> Fastening:
    made = valve_stem(m, valve)
    frame = m.valve_frame(valve)
    return Fastening(
        parts=[made],
        mates=[
            Mate(
                f"{valve.name} valve",
                Kind.PRISMATIC,
                child=on(made),
                parent=on(head_name(valve)),
                at=frame,
                approach=Axis(frame),
            )
        ],
    )


@derived
def the_head(m: V8Master, deg: float) -> Fastening:
    head_part = bank_builders(deg)[0](m)
    inserts = inserts_on("header insert", m, m.header_spots(deg), head_part)
    return Fastening(
        parts=[head_part, *inserts.parts],
        mates=[
            fixed(on(head_part), on(BLOCK), -Axis(m.bank(deg, 0.0))),
            *inserts.mates,
        ],
    )


@derived
def head_screws(m: V8Master, deg: float) -> Fastening:
    name = LEFT_HEAD if deg == LEFT_BANK_DEG else RIGHT_HEAD
    return screws_at("head screw", m, m.head_spots(deg), name, m.head_height)


@derived
def the_rail(m: V8Master, deg: float) -> Fastening:
    made = bank_builders(deg)[1](m)
    bolts = screws_at("rail screw", m, m.rail_spots(deg), made, m.rail_height)
    return Fastening(
        parts=[made, *bolts.parts],
        mates=[fixed(on(made), on(BLOCK), -Axis(m.bank(deg, 0.0))), *bolts.mates],
    )


@derived
def lower_column(m: V8Master, valve: Valve) -> Fastening:
    fitted = FROM_ABOVE
    name = valve.name
    cam, band, lift = lobe(m, valve), strap(m, valve), lifter(m, valve)
    return Fastening(
        parts=[lift, cam, band],
        mates=[
            Mate(
                f"{name} lifter",
                Kind.PRISMATIC,
                child=on(lift),
                parent=on(rail_name(valve)),
                at=m.lifter_frame(valve),
                approach=fitted,
            ),
            fixed(on(cam), on(CAMSHAFT), fitted),
            Mate(
                f"{name} strap",
                Kind.REVOLUTE,
                child=on(band),
                parent=on(cam),
                at=m.hinge_on(m.lobe_centre(valve, REST_TURN_DEG)),
                approach=ALONG_THE_LAYERS,
            ),
            Mate(
                f"{name} strap pin",
                Kind.REVOLUTE,
                child=on(band),
                parent=on(lift),
                at=m.hinge_on(m.lifter_pin(valve, REST_TURN_DEG)),
                closes=True,
                approach=ALONG_THE_LAYERS,
            ),
        ],
    )


@derived
def upper_column(m: V8Master, valve: Valve) -> Fastening:
    fitted = -Axis(m.bank_of(valve, 0.0))
    name = valve.name
    rock, link, cap = rocker(m, valve), toggle_link(m, valve), valve_cap(m, valve)
    return Fastening(
        parts=[rock, cap, link],
        mates=[
            Mate(
                f"{name} rocker",
                Kind.REVOLUTE,
                child=on(rock),
                parent=on(head_name(valve)),
                at=m.hinge_on(m.rocker_pivot(valve)),
                approach=fitted,
            ),
            fixed(on(cap), on(f"{name} stem"), fitted),
            Mate(
                f"{name} link",
                Kind.REVOLUTE,
                child=on(link),
                parent=on(rock),
                at=m.link_frame(valve),
                approach=ALONG_THE_LAYERS,
            ),
            Mate(
                f"{name} link pin",
                Kind.REVOLUTE,
                child=on(link),
                parent=on(cap),
                at=m.hinge_on(m.valve_tip(valve, REST_TURN_DEG)),
                closes=True,
                approach=ALONG_THE_LAYERS,
            ),
        ],
    )


@derived
def the_pushrod(m: V8Master, valve: Valve) -> Fastening:
    name = valve.name
    made = pushrod(m, valve)
    return Fastening(
        parts=[made],
        mates=[
            Mate(
                f"{name} pushrod",
                Kind.REVOLUTE,
                child=on(made),
                parent=on(f"{name} lifter"),
                at=m.pushrod_frame(valve),
                approach=ALONG_THE_LAYERS,
            ),
            Mate(
                f"{name} pushrod pin",
                Kind.REVOLUTE,
                child=on(made),
                parent=on(f"{name} rocker"),
                at=m.hinge_on(m.rocker_end(valve, REST_TURN_DEG)),
                closes=True,
                approach=ALONG_THE_LAYERS,
            ),
        ],
    )


@derived
def the_camshaft(m: V8Master) -> Fastening:
    cam = camshaft(m)
    return Fastening(
        parts=[cam],
        mates=[
            Mate(
                CAMSHAFT,
                Kind.REVOLUTE,
                child=on(cam),
                parent=on(BLOCK),
                at=m.cam_turn,
                approach=FROM_THE_FRONT,
            ),
            meshing(CRANK_GEAR, CAMSHAFT),
        ],
    )


@derived
def the_crank_gear(m: V8Master) -> Fastening:
    made = crank_gear(m)
    bolts = screws_at("crank gear screw", m, m.nose_spots, made, m.timing_width + m.pulley_width)
    return Fastening(
        parts=[made, *bolts.parts],
        mates=[
            fixed(on(made), on(m.crank_pieces[0].name), FROM_THE_FRONT),
            *bolts.mates,
        ],
    )


@derived
def the_keeper(m: V8Master, deg: float) -> Fastening:
    made = (left_keeper if deg == LEFT_BANK_DEG else right_keeper)(m)
    bolts = screws_at("keeper screw", m, m.keeper_spots(deg), made, m.rail_height)
    return Fastening(
        parts=[made, *bolts.parts],
        mates=[fixed(on(made), on(BLOCK), FROM_ABOVE), *bolts.mates],
    )


@derived
def rocker_shafts(m: V8Master, deg: float) -> Fastening:
    name = LEFT_HEAD if deg == LEFT_BANK_DEG else RIGHT_HEAD
    at = m.rocker_shaft_at(deg)
    shaft = Pin(
        name="rocker shaft",
        pose=at,
        diameter=m.rocker_shaft,
        length=m.rocker_shaft_length,
        standard=DOWEL,
    )
    return Fastening(parts=[shaft], mates=[fixed(on(shaft), on(name), FROM_THE_FRONT)])


@derived
def plugs_and_header(m: V8Master, deg: float) -> Fastening:
    name = LEFT_HEAD if deg == LEFT_BANK_DEG else RIGHT_HEAD
    collector = (left_header if deg == LEFT_BANK_DEG else right_header)(m)
    parts: list[Part] = []
    mates: list[Mate] = []
    for n, cylinder in enumerate(each for each in CYLINDERS if each.bank_deg == deg):
        plug = spark_plug(m, m.plug_at(cylinder))
        parts.append(plug)
        mates.append(numbered(fixed(on(plug), on(name), -Axis(m.bank(deg, 0.0))), n))
    bolts = screws_at("header screw", m, m.header_spots(deg), collector, m.header_diameter)
    return Fastening(
        parts=[*parts, collector, *bolts.parts],
        mates=[
            *mates,
            fixed(on(collector), on(name), inward(m.header_spots(deg)[0])),
            *bolts.mates,
        ],
    )


@derived
def the_tray(m: V8Master) -> Fastening:
    tray = battery_tray(m)
    bolts = screws_at("tray screw", m, m.tray_spots, tray, m.tab_thickness, m.plate_screw_length)
    rocker = Bought(name=SWITCH_NAME, pose=m.switch_at, item=SWITCH)
    splice = Bought(name=SLEEVE_NAME, pose=m.sleeve_at, item=SLEEVE)
    return Fastening(
        parts=[tray, *bolts.parts, rocker, splice],
        mates=[
            fixed(on(tray), on(REAR_PLATE), FROM_THE_REAR),
            *bolts.mates,
            fixed(on(rocker), on(tray), inward(m.switch_at)),
            fixed(on(splice), on(rocker), inward(m.switch_at)),
        ],
    )


@derived
def the_holder(m: V8Master) -> Fastening:
    holder = Bought(name=HOLDER_NAME, pose=m.holder_at, item=BATTERY_HOLDER)
    cells = [
        Bought(name=f"{CELL_NAME} {k + 1}", pose=spot, item=CELL)
        for k, spot in enumerate(m.cell_spots)
    ]
    return Fastening(
        parts=[holder, *cells],
        mates=[
            fixed(on(holder), on(BATTERY_TRAY), FROM_ABOVE),
            *(fixed(on(each), on(holder), FROM_ABOVE) for each in cells),
        ],
    )


def cylinder_columns(m: V8Master, cylinder: Cylinder) -> Assembly:
    valves = [each for each in VALVES if each.cylinder is cylinder]
    return Assembly(
        f"{cylinder.name} valves",
        *(
            Assembly(
                f"{each.name} column",
                Assembly(f"{each.name} cam end", job(lower_column, m, each), bench=True),
                Assembly(f"{each.name} valve end", job(upper_column, m, each), bench=True),
                job(the_pushrod, m, each),
            )
            for each in sorted(valves, key=lambda each: -m.valve_y_at(each))
        ),
    )


def bank_jobs(m: V8Master, deg: float) -> Assembly:
    cylinders = [each for each in CYLINDERS if each.bank_deg == deg]
    return Assembly(
        f"bank {deg:g}",
        Assembly(
            f"head {deg:g}",
            job(the_head, m, deg),
            *(job(stem, m, each) for each in VALVES if each.cylinder.bank_deg == deg),
            bench=True,
        ),
        job(head_screws, m, deg),
        job(the_rail, m, deg),
        *(
            cylinder_columns(m, each)
            for each in sorted(cylinders, key=lambda each: -m.cylinder_y(each))
        ),
        job(rocker_shafts, m, deg),
        job(plugs_and_header, m, deg),
    )


def battery_leads(m: V8Master, find: Callable[[str], Part]) -> list[Route]:
    holder, rocker, motor = find(HOLDER_NAME), find(SWITCH_NAME), find(MOTOR_NAME)
    trunk = holder_leads(m)
    splice = RoutePoint(part=rocker, at=rocker.pose.inverse() * m.lead_over_the_switch)
    return [
        Route(
            cable=trunk,
            plugged=(
                RoutePoint(part=holder, at=holder.pose.inverse() * m.holder_leads_out),
                RoutePoint(part=rocker, at=m.switch_ends.supply),
                splice,
            ),
            through=((), ()),
        ),
        Route(
            cable=switch_leads(trunk),
            plugged=(
                RoutePoint(part=rocker, at=m.switch_ends.load),
                RoutePoint(part=motor, at=motor.pose.inverse() * m.lead_end),
                splice,
            ),
            through=(
                (
                    splice,
                    RoutePoint(part=holder, at=holder.pose.inverse() * m.lead_above),
                ),
                (),
            ),
        ),
    ]


BANKS = (LEFT_BANK_DEG, RIGHT_BANK_DEG)


V8 = Assembly(
    "v8",
    Assembly("block", job(the_block, MASTER), job(crank_piece, MASTER, MASTER.crank_pieces[0])),
    *(journals(MASTER, journal) for journal in JOURNALS),
    Assembly(
        "closing",
        job(closing_plate, MASTER),
        job(motor_in_plate, MASTER),
        job(cap_inserts, MASTER),
        job(capped, MASTER),
    ),
    Assembly("crank gear", job(the_crank_gear, MASTER)),
    Assembly(
        "valvetrain",
        *(bank_jobs(MASTER, deg) for deg in BANKS),
        *(job(the_keeper, MASTER, deg) for deg in BANKS),
        job(the_camshaft, MASTER),
        stress_analysed=False,
    ),
    Assembly("power", job(the_tray, MASTER), job(the_holder, MASTER)),
    cables=lambda find: battery_leads(MASTER, find),
)
