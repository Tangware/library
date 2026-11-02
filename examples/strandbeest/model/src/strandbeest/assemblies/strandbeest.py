from collections.abc import Callable

from build123d import Align, Axis, BuildPart, Cylinder, Location, Pos, Rot
from cad.assembly.tree import Assembly, job
from cad.cables.models import Cable, CutToFit, Discrete, Plug, Route, RoutePoint, Splice, Wire
from cad.library.bought.catalogue import NO_BILL, Bill
from cad.library.bought.vendor import Bought
from cad.library.derived import derived
from cad.library.features.hardware import Fastening, insert_seat
from cad.library.fits import ALUMINIUM_6063_T6
from cad.library.mates import Connector, Kind, Mate
from cad.library.shapes import OUTSIDE, Part, built
from cad.library.standard.fasteners import (
    BEARING_FACE,
    THREAD,
    UNDER_HEAD,
    LockNut,
    Nut,
    Screw,
    ThreadedInsert,
)
from cad.library.standard.profiles import StockTube, ThreadedRod

from strandbeest.master import (
    BATTERY_HOLDER,
    CELL,
    CRANK,
    MASTER,
    MOTOR,
    MOTOR_OUTPUT,
    SLEEVE,
    SWITCH,
    CrankPiece,
    Joints,
    Module,
    StrandbeestMaster,
)
from strandbeest.models import wire
from strandbeest.parts.crank import crank
from strandbeest.parts.frame import (
    DECK,
    LEFT_PLATE,
    RIGHT_PLATE,
    deck,
    left_plate,
    motor_cap,
    right_plate,
    sail,
)
from strandbeest.parts.links import coupler, foot, lower_link, rocker, triangle, upper_link

MOTOR_NAME = "Pololu 3069 298:1 Micro Metal Gearmotor HPCB 6V"
HOLDER_NAME = "MPD BC4AAW 4-AA battery holder"
SWITCH_NAME = "E-Switch RD11131121 rocker switch"
SLEEVE_NAME = "TE Raychem RNF-100-3/32-BK heat-shrink sleeve"
CELL_NAME = "Energizer EN91 AA cell"
FROM_THE_RIGHT = -Axis.Y
FROM_ABOVE = -Axis.Z
FOOT_LAYER_MIDDLE = 2.0
INNER_LAYER = 0.5
OUTER_LAYER = 1.5
FORE, AFT = True, False
RED, BLACK = wire.CONDUCTORS
SPLICE = "black splice"
LEADS_LENGTH_MM = 150.0


def holder_leads(m: StrandbeestMaster) -> Cable:
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


def tube_name(x: float) -> str:
    return "fore frame tube" if x > 0 else "aft frame tube"


def rod_name(x: float) -> str:
    return "fore frame rod" if x > 0 else "aft frame rod"


def fixed(
    child: Connector, parent: Connector, closes: bool = False, approach: Axis = FROM_THE_RIGHT
) -> Mate:
    return Mate(
        f"{child.part if isinstance(child.part, str) else child.part.name}"
        f" on {parent.part if isinstance(parent.part, str) else parent.part.name}",
        Kind.RIGID,
        child=child,
        parent=parent,
        closes=closes,
        approach=approach,
    )


def on(part: Part | str) -> Connector:
    return Connector(part, OUTSIDE)


def tube_xs(m: StrandbeestMaster) -> tuple[float, float]:
    x = m.a * m.scale
    return -x, x


@derived
def frame_rods(m: StrandbeestMaster) -> Fastening:
    grade = ALUMINIUM_6063_T6
    parts: list[Part] = []
    mates: list[Mate] = []
    plate = left_plate(m)
    rod_length = m.rod_length
    for x in tube_xs(m):
        tube = StockTube(
            name=tube_name(x),
            pose=m.along_y(x, -m.half_width),
            size=m.tube,
            length=m.tube_length,
            grade=grade,
        )
        with BuildPart() as made:
            Cylinder(
                m.rod.diameter / 2,
                rod_length,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        rod = ThreadedRod(
            name=rod_name(x),
            pose=m.along_y(x, -rod_length / 2),
            body=built(made),
            size=m.rod,
            length=rod_length,
            grade=m.stock.fastener_grade,
        )
        parts += [tube, rod]
        mates.append(fixed(on(tube), on(plate)))
        mates.append(fixed(Connector(rod, THREAD), on(tube)))
    return Fastening(parts=[plate, *parts], mates=mates)


def pivot_screw(m: StrandbeestMaster, at: Location) -> Screw:
    return Screw(
        name="pivot screw",
        pose=at,
        size=m.screw,
        length=m.screw_length,
        grade=m.stock.fastener_grade,
    )


def lock_nut(m: StrandbeestMaster, at: Location) -> LockNut:
    return LockNut(name="pivot nut", pose=at, size=m.screw, grade=m.stock.fastener_grade)


def hinge(
    name: str,
    child: Part | str,
    parent: Part | str,
    at: Location,
    closes: bool = False,
    approach: Axis = FROM_THE_RIGHT,
) -> Mate:
    return Mate(
        name,
        Kind.REVOLUTE,
        child=on(child),
        parent=on(parent),
        at=at,
        closes=closes,
        approach=approach,
    )


def linked(m: StrandbeestMaster, placing: Location, at: Joints) -> dict[str, Part]:
    def frame(start: Location, end: Location, layer: float) -> Location:
        return placing * m.level(layer) * m.link_frame(start, end)

    foot_middle = FOOT_LAYER_MIDDLE + m.foot_thickness / 2 / m.layer
    return {
        "lower": lower_link(m, frame(at.crank_pin, at.lower, INNER_LAYER)),
        "upper": upper_link(m, frame(at.crank_pin, at.upper, OUTER_LAYER)),
        "triangle": triangle(m, frame(at.frame_pivot, at.upper, INNER_LAYER)),
        "rocker": rocker(m, frame(at.frame_pivot, at.lower, OUTER_LAYER)),
        "coupler": coupler(m, frame(at.outer, at.knee, OUTER_LAYER)),
        "foot": foot(m, frame(at.lower, at.knee, foot_middle)),
    }


@derived
def leg(m: StrandbeestMaster, module: Module, fore: bool) -> Fastening:
    placing = m.on_module(module, fore)
    at = m.joints(module.fore_phase if fore else module.phase)
    links = linked(m, placing, at)
    side = "fore" if fore else "aft"
    name = f"module {module.index + 1} {side}"
    tube = tube_name(tube_xs(m)[1 if fore else 0])
    pin = m.crank_pieces[module.index].name

    def hinged(joint: Location) -> Location:
        return m.hinge(placing, joint)

    nuts_free = m.two_layers
    screws = {
        "upper": pivot_screw(m, m.pivot_screw(placing, at.upper)),
        "outer": pivot_screw(m, m.pivot_screw(placing, at.outer)),
        "lower": pivot_screw(m, m.pivot_screw(placing, at.lower)),
        "knee": pivot_screw(m, m.pivot_screw(placing, at.knee)),
    }
    nuts = {
        "upper": lock_nut(m, m.pivot_nut(placing, at.upper, nuts_free)),
        "outer": lock_nut(m, m.pivot_nut(placing, at.outer, nuts_free)),
        "lower": lock_nut(m, m.foot_nut(placing, at, at.lower)),
        "knee": lock_nut(m, m.foot_nut(placing, at, at.knee)),
    }
    toward_the_middle = -FROM_THE_RIGHT if fore else FROM_THE_RIGHT
    mates = [
        hinge(f"{name} triangle", links["triangle"], tube, hinged(at.frame_pivot)),
        hinge(f"{name} rocker", links["rocker"], tube, hinged(at.frame_pivot)),
        hinge(f"{name} upper link", links["upper"], pin, hinged(at.crank_pin)),
        hinge(f"{name} lower link", links["lower"], pin, hinged(at.crank_pin)),
        hinge(
            f"{name} coupler",
            links["coupler"],
            links["triangle"],
            hinged(at.outer),
            approach=toward_the_middle,
        ),
        hinge(
            f"{name} foot",
            links["foot"],
            links["rocker"],
            hinged(at.lower),
            approach=toward_the_middle,
        ),
        hinge(
            f"{name} upper closes",
            links["upper"],
            links["triangle"],
            hinged(at.upper),
            closes=True,
        ),
        hinge(
            f"{name} lower closes",
            links["lower"],
            links["rocker"],
            hinged(at.lower),
            closes=True,
        ),
        hinge(f"{name} knee closes", links["coupler"], links["foot"], hinged(at.knee), closes=True),
    ]
    holders = {
        "upper": links["triangle"],
        "outer": links["triangle"],
        "lower": links["foot"],
        "knee": links["foot"],
    }
    for joint, screw in screws.items():
        mates.append(
            Mate(
                f"{name} {joint} screw",
                Kind.RIGID,
                child=Connector(screw, UNDER_HEAD),
                parent=on(holders[joint]),
            )
        )
        mates.append(
            Mate(
                f"{name} {joint} nut",
                Kind.RIGID,
                child=Connector(nuts[joint], BEARING_FACE),
                parent=Connector(screw, THREAD),
                approach=toward_the_middle,
            )
        )
    order = ("rocker", "upper", "triangle", "lower", "coupler", "foot")
    return Fastening(
        parts=[*(links[each] for each in order), *screws.values(), *nuts.values()], mates=mates
    )


def insert_at(name: str, m: StrandbeestMaster, spot: Location) -> ThreadedInsert:
    return ThreadedInsert(
        name=name,
        pose=insert_seat(spot, m.screw, fits=m.fits, stock=m.stock),
        designation=m.stock.inserts[m.screw],
        maker=m.stock.insert_maker,
    )


def screw_at(name: str, m: StrandbeestMaster, at: Location, length: float) -> Screw:
    return Screw(name=name, pose=at, size=m.screw, length=length, grade=m.stock.fastener_grade)


@derived
def crank_piece(m: StrandbeestMaster, piece: CrankPiece) -> Fastening:
    made = crank(m, piece)
    parts: list[Part] = [made]
    mates: list[Mate] = []
    if piece.index == 0:
        mates.append(
            Mate(
                CRANK,
                Kind.REVOLUTE,
                child=on(made),
                parent=on(LEFT_PLATE),
                at=m.against_the_crank,
                servo=MOTOR_NAME,
                approach=FROM_THE_RIGHT,
            )
        )
    else:
        below = m.crank_pieces[piece.index - 1]
        spot = m.crank_frame(piece) * m.pin_spot(below.high)
        screw = screw_at(f"{piece.name} pin screw", m, spot, m.pin_screw_length)
        parts.append(screw)
        mates += [
            fixed(on(made), on(below.name)),
            fixed(Connector(screw, UNDER_HEAD), on(made)),
        ]
    if piece.high is not None:
        tip = m.crank_frame(piece) * m.pin_spot(piece.high) * Pos(Z=m.crank_arm + m.two_layers)
        insert = insert_at(f"{piece.name} pin insert", m, tip)
        parts.append(insert)
        mates.append(fixed(on(insert), on(made)))
    return Fastening(parts=parts, mates=mates)


@derived
def closing_plate(m: StrandbeestMaster) -> Fastening:
    plate = right_plate(m)
    low, high = tube_xs(m)
    right, left = [], []
    for x in (low, high):
        right.append(
            Nut(
                name="frame rod nut",
                pose=m.along_y(x, m.plate_outer_y),
                size=m.rod,
                grade=m.stock.fastener_grade,
            )
        )
        left.append(
            Nut(
                name="frame rod nut",
                pose=m.along_y(x, -m.plate_outer_y) * Rot(X=180.0),
                size=m.rod,
                grade=m.stock.fastener_grade,
            )
        )
    return Fastening(
        parts=[plate, *right, *left],
        mates=[
            fixed(on(plate), on(tube_name(high))),
            fixed(on(plate), on(tube_name(low)), closes=True),
            *(
                fixed(Connector(nut, BEARING_FACE), Connector(rod_name(x), THREAD))
                for nut, x in zip(right, (low, high), strict=True)
            ),
            *(
                fixed(Connector(nut, BEARING_FACE), Connector(rod_name(x), THREAD), approach=Axis.Y)
                for nut, x in zip(left, (low, high), strict=True)
            ),
        ],
    )


@derived
def motor_in_plate(m: StrandbeestMaster) -> Fastening:
    motor = Bought(name=MOTOR_NAME, pose=m.motor_at, item=MOTOR)
    shaft = Bought(
        name=f"{MOTOR_NAME} shaft", pose=m.motor_at, item=MOTOR_OUTPUT, ships_with=MOTOR_NAME
    )
    last = m.crank_pieces[-1].name
    return Fastening(
        parts=[motor, shaft],
        mates=[
            fixed(on(motor), on(RIGHT_PLATE)),
            fixed(on(shaft), on(last)),
            hinge("crank on the motor", shaft, motor, m.against_the_crank, closes=True),
        ],
    )


@derived
def cap_inserts(m: StrandbeestMaster) -> Fastening:
    inserts = [insert_at("motor cap insert", m, spot) for spot in m.cap_spots]
    return Fastening(
        parts=list(inserts),
        mates=[fixed(on(each), on(RIGHT_PLATE)) for each in inserts],
    )


@derived
def capped(m: StrandbeestMaster) -> Fastening:
    cap = motor_cap(m)
    screws = [
        screw_at("motor cap screw", m, spot * Pos(Z=m.cap_flange), m.screw_length)
        for spot in m.cap_spots
    ]
    return Fastening(
        parts=[cap, *screws],
        mates=[
            fixed(on(cap), on(RIGHT_PLATE)),
            *(fixed(Connector(each, UNDER_HEAD), on(cap)) for each in screws),
        ],
    )


@derived
def deck_inserts(m: StrandbeestMaster) -> Fastening:
    inserts = [insert_at("deck insert", m, spot) for spot in m.deck_spots]
    plates = (LEFT_PLATE, LEFT_PLATE, RIGHT_PLATE, RIGHT_PLATE)
    return Fastening(
        parts=list(inserts),
        mates=[
            Mate(
                f"{each.name} {n} in {plate}",
                Kind.RIGID,
                child=on(each),
                parent=on(plate),
                approach=FROM_ABOVE,
            )
            for n, (each, plate) in enumerate(zip(inserts, plates, strict=True))
        ],
    )


@derived
def top(m: StrandbeestMaster) -> Fastening:
    sheet = deck(m)
    holder = Bought(name=HOLDER_NAME, pose=m.holder_at, item=BATTERY_HOLDER)
    cells = [
        Bought(name=f"{CELL_NAME} {k + 1}", pose=spot, item=CELL)
        for k, spot in enumerate(m.cell_spots)
    ]
    rocker = Bought(name=SWITCH_NAME, pose=m.switch_at, item=SWITCH)
    splice = Bought(name=SLEEVE_NAME, pose=m.sleeve_at, item=SLEEVE)
    screws = [
        screw_at("deck screw", m, spot * Pos(Z=m.deck_thickness), m.deck_screw_length)
        for spot in m.deck_spots
    ]
    return Fastening(
        parts=[sheet, holder, *cells, rocker, splice, *screws],
        mates=[
            Mate(
                f"{DECK} on {RIGHT_PLATE}",
                Kind.RIGID,
                child=on(sheet),
                parent=on(RIGHT_PLATE),
                approach=FROM_ABOVE,
            ),
            Mate(
                f"{DECK} on {LEFT_PLATE}",
                Kind.RIGID,
                child=on(sheet),
                parent=on(LEFT_PLATE),
                closes=True,
                approach=FROM_ABOVE,
            ),
            *(
                Mate(
                    f"{each.name} {n}",
                    Kind.RIGID,
                    child=Connector(each, UNDER_HEAD),
                    parent=on(sheet),
                    approach=FROM_ABOVE,
                )
                for n, each in enumerate(screws)
            ),
            Mate(
                f"{HOLDER_NAME} on {DECK}",
                Kind.RIGID,
                child=on(holder),
                parent=on(sheet),
                approach=FROM_ABOVE,
            ),
            *(
                Mate(
                    f"{each.name} in the holder",
                    Kind.RIGID,
                    child=on(each),
                    parent=on(holder),
                    approach=FROM_ABOVE,
                )
                for each in cells
            ),
            Mate(
                f"{SWITCH_NAME} on {DECK}",
                Kind.RIGID,
                child=on(rocker),
                parent=on(sheet),
                approach=-Axis(m.switch_at),
            ),
            Mate(
                f"{SLEEVE_NAME} on {SWITCH_NAME}",
                Kind.RIGID,
                child=on(splice),
                parent=on(rocker),
                approach=-Axis(m.switch_at),
            ),
        ],
    )


@derived
def sails(m: StrandbeestMaster) -> Fastening:
    made = [sail(m, module) for module in m.modules]
    return Fastening(
        parts=list(made),
        mates=[
            Mate(
                f"sail {n} on {DECK}",
                Kind.RIGID,
                child=on(each),
                parent=on(DECK),
                approach=FROM_ABOVE,
            )
            for n, each in enumerate(made)
        ],
    )


def battery_leads(m: StrandbeestMaster, find: Callable[[str], Part]) -> list[Route]:
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
                    RoutePoint(part=holder, at=holder.pose.inverse() * m.lead_over_the_edge),
                    RoutePoint(part=holder, at=holder.pose.inverse() * m.lead_above_the_cap),
                ),
                (),
            ),
        ),
    ]


def module_jobs(m: StrandbeestMaster, module: Module) -> Assembly:
    number = module.index + 1
    return Assembly(
        f"module {number}",
        Assembly(f"module {number} fore leg", job(leg, m, module, FORE), bench=True),
        Assembly(f"module {number} aft leg", job(leg, m, module, AFT), bench=True),
        job(crank_piece, m, m.crank_pieces[module.index + 1]),
    )


STRANDBEEST = Assembly(
    "strandbeest",
    Assembly("frame", job(frame_rods, MASTER), job(crank_piece, MASTER, MASTER.crank_pieces[0])),
    *(module_jobs(MASTER, module) for module in MASTER.modules),
    Assembly(
        "closing",
        job(closing_plate, MASTER),
        job(motor_in_plate, MASTER),
        job(cap_inserts, MASTER),
        job(capped, MASTER),
        job(deck_inserts, MASTER),
        job(top, MASTER),
    ),
    Assembly("sails", job(sails, MASTER), stress_analysed=False),
    cables=lambda find: battery_leads(MASTER, find),
)
