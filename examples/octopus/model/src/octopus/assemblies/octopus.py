from collections.abc import Callable

from build123d import Axis, Location, Pos
from cad.assembly.tree import Assembly, job
from cad.cables.models import Cable, CutToFit, Jacketed, Plug, Route, RoutePoint, Wire
from cad.library.bought.catalogue import NO_BILL, Bill
from cad.library.bought.vendor import Bought
from cad.library.derived import derived
from cad.library.features.hardware import Fastening, insert_seat
from cad.library.mates import Connector, Kind, Mate, named
from cad.library.shapes import OUTSIDE, Part
from cad.library.standard.fasteners import UNDER_HEAD, Screw, ThreadedInsert

from octopus.master import (
    ARMS,
    BATTERY_HOLDER,
    CELL,
    HIGH_ARMS,
    LOW_ARMS,
    MASTER,
    MOTOR,
    MOTOR_OUTPUT,
    SWITCH,
    OctopusMaster,
    crank_joint,
)
from octopus.parts.arm import (
    EVEN,
    crank,
    crank_name,
    drive_rod,
    rod,
    segment,
    segment_name,
)
from octopus.parts.body import BODY, body, mantle, motor_cap

MOTOR_NAME = "Pololu 3069 298:1 Micro Metal Gearmotor HPCB 6V"
HOLDER_NAME = "MPD BC4AAW 4-AA battery holder"
SWITCH_NAME = "E-Switch RD11131121 rocker switch"
CELL_NAME = "Energizer E91 AA cell"
FROM_ABOVE = -Axis.Z
LEAD_WIRES = ("red", "black")
AWG_24_MM = 0.511
AWG_26_MM = 0.405
LEADS_BUNDLE_MM = 1.8
LEADS_LENGTH_MM = 150.0
LEADS = Cable(
    name="battery holder leads",
    wires=tuple(Wire(name=name, diameter=AWG_26_MM, colour=name) for name in LEAD_WIRES),
    plugs=(
        Plug(name="holder", model=None, pinout=LEAD_WIRES),
        Plug(name="switch", model=None, pinout=LEAD_WIRES),
    ),
    construction=Jacketed(diameter=LEADS_BUNDLE_MM),
    twist_rating=0.0,
    length=LEADS_LENGTH_MM,
    bill=Bill(ships_with=HOLDER_NAME),
)


def lead(arm: int) -> Cable:
    return Cable(
        name=f"arm {arm + 1} lead",
        wires=tuple(Wire(name=name, diameter=AWG_24_MM, colour=name) for name in LEAD_WIRES),
        plugs=(
            Plug(name="switch", model=None, pinout=LEAD_WIRES),
            Plug(name="motor", model=None, pinout=LEAD_WIRES),
        ),
        construction=Jacketed(diameter=LEADS_BUNDLE_MM),
        twist_rating=0.0,
        length=CutToFit(),
        bill=NO_BILL,
    )


def on(part: Part | str) -> Connector:
    return Connector(part, OUTSIDE)


def fixed(child: Connector, parent: Connector, approach: Axis, n: int | None = None) -> Mate:
    first, second = (named(each.part) for each in (child, parent))
    mark = "" if n is None else f" {n}"
    return Mate(
        f"{first} on {second}{mark}", Kind.RIGID, child=child, parent=parent, approach=approach
    )


def inward(spot: Location) -> Axis:
    return -Axis(spot)


def insert_at(name: str, m: OctopusMaster, spot: Location) -> ThreadedInsert:
    return ThreadedInsert(
        name=name,
        pose=insert_seat(spot, m.screw, fits=m.fits, stock=m.stock),
        designation=m.stock.inserts[m.screw],
        maker=m.stock.insert_maker,
    )


def screw_at(name: str, m: OctopusMaster, at: Location) -> Screw:
    return Screw(
        name=name, pose=at, size=m.screw, length=m.short_screw, grade=m.stock.fastener_grade
    )


def hinge_joint(arm: int, k: int) -> str:
    return f"arm {arm + 1} hinge {k}"


@derived
def the_body(m: OctopusMaster) -> Fastening:
    made = body(m)
    spots = (*(spot for arm in ARMS for spot in m.saddle_spots(arm)), *m.mantle_spots)
    inserts = [insert_at("body insert", m, spot) for spot in spots]
    return Fastening(
        parts=[made, *inserts],
        mates=[
            fixed(on(each), on(made), inward(spot), n)
            for n, (each, spot) in enumerate(zip(inserts, spots, strict=True))
        ],
    )


@derived
def motor_unit(m: OctopusMaster, arm: int) -> Fastening:
    motor = Bought(name=f"{MOTOR_NAME} {arm + 1}", pose=m.motor_at(arm), item=MOTOR)
    return Fastening(
        parts=[motor], mates=[fixed(on(motor), on(BODY), inward(m.saddle_spots(arm)[0]))]
    )


@derived
def crank_unit(m: OctopusMaster, arm: int) -> Fastening:
    motor = f"{MOTOR_NAME} {arm + 1}"
    shaft = Bought(
        name=f"{MOTOR_NAME} shaft {arm + 1}",
        pose=m.motor_at(arm),
        item=MOTOR_OUTPUT,
        ships_with=motor,
    )
    made = crank(m, arm)
    frame = m.drive_frame(arm)
    way = -m.forward(arm)
    return Fastening(
        parts=[made, shaft],
        mates=[
            Mate(
                crank_joint(arm),
                Kind.REVOLUTE,
                child=on(made),
                parent=on(BODY),
                at=frame,
                servo=motor,
                approach=way,
            ),
            fixed(on(shaft), on(made), way),
            Mate(
                f"arm {arm + 1} crank on its motor",
                Kind.REVOLUTE,
                child=on(shaft),
                parent=on(motor),
                at=frame,
                closes=True,
                approach=way,
            ),
        ],
    )


@derived
def cap_unit(m: OctopusMaster, arm: int) -> Fastening:
    cap = motor_cap(m, arm)
    spots = m.saddle_spots(arm)
    way = inward(spots[0])
    screws = [screw_at("cap screw", m, spot * Pos(Z=m.cap_thickness)) for spot in spots]
    return Fastening(
        parts=[cap, *screws],
        mates=[
            fixed(on(cap), on(BODY), way),
            *(fixed(Connector(each, UNDER_HEAD), on(cap), way, n) for n, each in enumerate(screws)),
        ],
    )


@derived
def arm_chain(m: OctopusMaster, arm: int) -> Fastening:
    ahead = m.forward(arm)
    pieces = [segment(m, arm, k) for k in (1, 2, 3, 4)]
    links = [rod(m, arm, k) for k in (2, 3)]
    first, *rest = pieces
    mates = [
        Mate(
            hinge_joint(arm, 1),
            Kind.REVOLUTE,
            child=on(first),
            parent=on(BODY),
            at=m.hinge(arm, 1, m.segment_y(0)),
            approach=-ahead,
        )
    ]
    for k, (each, holder) in enumerate(zip(rest, pieces, strict=False), start=2):
        mates.append(
            Mate(
                hinge_joint(arm, k),
                Kind.REVOLUTE,
                child=on(each),
                parent=on(holder),
                at=m.hinge(arm, k, m.segment_y(k)),
                approach=ahead if k in EVEN else -ahead,
            )
        )
    for k, link in zip((2, 3), links, strict=True):
        way = -ahead if k in EVEN else ahead
        mates += [
            Mate(
                f"arm {arm + 1} rod {k} low",
                Kind.REVOLUTE,
                child=on(link),
                parent=on(pieces[k - 2]),
                at=m.hinge(arm, k, m.rod_y(k), m.offset),
                approach=way,
            ),
            Mate(
                f"arm {arm + 1} rod {k} high",
                Kind.REVOLUTE,
                child=on(link),
                parent=on(pieces[k]),
                at=m.hinge(arm, k + 1, m.rod_y(k), -m.low_offset),
                closes=True,
                approach=way,
            ),
        ]
    return Fastening(parts=[*pieces, *links], mates=mates)


@derived
def first_rod(m: OctopusMaster, arm: int) -> Fastening:
    link = rod(m, arm, 1)
    ahead = m.forward(arm)
    return Fastening(
        parts=[link],
        mates=[
            Mate(
                f"arm {arm + 1} rod 1 low",
                Kind.REVOLUTE,
                child=on(link),
                parent=on(BODY),
                at=m.hinge(arm, 1, m.rod_y(1), m.offset),
                approach=ahead,
            ),
            Mate(
                f"arm {arm + 1} rod 1 high",
                Kind.REVOLUTE,
                child=on(link),
                parent=on(segment_name(arm, 2)),
                at=m.hinge(arm, 2, m.rod_y(1), -m.low_offset),
                closes=True,
                approach=ahead,
            ),
        ],
    )


@derived
def the_drive_rod(m: OctopusMaster, arm: int) -> Fastening:
    link = drive_rod(m, arm)
    way = -m.forward(arm)
    frame = m.drive_rod_frame(arm)
    return Fastening(
        parts=[link],
        mates=[
            Mate(
                f"arm {arm + 1} lever",
                Kind.REVOLUTE,
                child=on(link),
                parent=on(segment_name(arm, 1)),
                at=m.lever_pin(arm, m.drive_rod_y),
                approach=way,
            ),
            Mate(
                f"arm {arm + 1} crank pin",
                Kind.REVOLUTE,
                child=on(link),
                parent=on(crank_name(arm)),
                at=frame,
                closes=True,
                approach=way,
            ),
        ],
    )


@derived
def the_mantle(m: OctopusMaster) -> Fastening:
    holder = Bought(name=HOLDER_NAME, pose=m.holder_at, item=BATTERY_HOLDER)
    cells = [
        Bought(name=f"{CELL_NAME} {k + 1}", pose=spot, item=CELL)
        for k, spot in enumerate(m.cell_spots)
    ]
    shell = mantle(m)
    rocker = Bought(name=SWITCH_NAME, pose=m.switch_at, item=SWITCH)
    screws = [screw_at("mantle screw", m, spot * Pos(Z=m.flange)) for spot in m.mantle_spots]
    return Fastening(
        parts=[holder, *cells, shell, rocker, *screws],
        mates=[
            fixed(on(holder), on(BODY), FROM_ABOVE),
            *(fixed(on(each), on(holder), FROM_ABOVE) for each in cells),
            fixed(on(shell), on(BODY), FROM_ABOVE),
            fixed(on(rocker), on(shell), inward(m.switch_at)),
            *(
                fixed(Connector(each, UNDER_HEAD), on(shell), FROM_ABOVE, n)
                for n, each in enumerate(screws)
            ),
        ],
    )


def arm_jobs(m: OctopusMaster, arm: int) -> Assembly:
    name = f"arm {arm + 1}"
    return Assembly(
        name,
        Assembly(f"{name} chain", job(arm_chain, m, arm), bench=True),
        job(first_rod, m, arm),
    )


def battery_leads(m: OctopusMaster, find: Callable[[str], Part]) -> list[Route]:
    holder, rocker = find(HOLDER_NAME), find(SWITCH_NAME)

    def from_holder(at: Location) -> RoutePoint:
        return RoutePoint(part=holder, at=holder.pose.inverse() * at)

    from_switch = RoutePoint(part=rocker, at=rocker.pose.inverse() * m.switch_terminals)
    routes = [
        Route(
            cable=LEADS,
            plugged=(from_holder(m.holder_leads_out), from_switch),
            through=((),),
        )
    ]
    for arm in ARMS:
        motor = find(f"{MOTOR_NAME} {arm + 1}")
        routes.append(
            Route(
                cable=lead(arm),
                plugged=(
                    from_switch,
                    RoutePoint(part=motor, at=motor.pose.inverse() * m.lead_end(arm)),
                ),
                through=(
                    (
                        from_holder(m.lead_up()),
                        from_holder(m.lead_over(arm)),
                        from_holder(m.lead_hole(arm)),
                        *((from_holder(m.lead_low(arm)),) if arm in LOW_ARMS else ()),
                    ),
                ),
            )
        )
    return routes


OCTOPUS = Assembly(
    "octopus",
    Assembly("body", job(the_body, MASTER)),
    Assembly(
        "motors",
        *(
            Assembly(
                f"motor {arm + 1}",
                job(motor_unit, MASTER, arm),
                job(cap_unit, MASTER, arm),
            )
            for arm in (*LOW_ARMS, *HIGH_ARMS)
        ),
        *(job(crank_unit, MASTER, arm) for arm in (*LOW_ARMS, *HIGH_ARMS)),
    ),
    *(arm_jobs(MASTER, arm) for arm in ARMS),
    Assembly("drive rods", *(job(the_drive_rod, MASTER, arm) for arm in ARMS)),
    Assembly("mantle", job(the_mantle, MASTER), stress_analysed=False),
    cables=lambda find: battery_leads(MASTER, find),
)
