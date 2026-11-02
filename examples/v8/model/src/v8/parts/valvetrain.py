from build123d import (
    Align,
    Box,
    BuildPart,
    Cylinder,
    Location,
    Locations,
    Mode,
    Pos,
    Rot,
    add,
    extrude,
)
from cad.design.parts import part
from cad.library.features.hardware import insert_cut
from cad.library.gears import Gear, gear_solid, spur_teeth
from cad.library.shapes import OUTSIDE, Outside, Printed, built

from v8.features import MATERIAL, bore, d_shape, web
from v8.master import CYLINDERS, REST_TURN_DEG, VALVES, V8Master, Valve

LEFT_HEAD = "left head"
RIGHT_HEAD = "right head"
LEFT_RAIL = "left lifter rail"
RIGHT_RAIL = "right lifter rail"
LEFT_KEEPER = "left lifter keeper"
RIGHT_KEEPER = "right lifter keeper"
LEFT_HEADER = "left exhaust header"
RIGHT_HEADER = "right exhaust header"
CAMSHAFT = "camshaft"
CRANK_GEAR = "crank gear"
LOBE = "cam lobe"
STRAP = "strap"
LIFTER = "lifter"
PUSHROD = "pushrod"
ROCKER = "rocker"
LINK = "toggle link"
VALVE = "valve"
VALVE_CAP = "valve cap"
SPARK_PLUG = "spark plug"
BATTERY_TRAY = "battery tray"
UP_FROM = (Align.CENTER, Align.CENTER, Align.MIN)
HANGING = (Align.CENTER, Align.CENTER, Align.MAX)
FLOOR_LEFT = (Align.MIN, Align.CENTER, Align.MIN)
FLOOR_RIGHT = (Align.MAX, Align.CENTER, Align.MIN)
ACROSS_THE_FACE = Rot(X=-90.0)
FLAT = 0.5


def printed(
    m: V8Master, name: str, made: BuildPart, pose: Location, bed: str = "-z", supports: str = ""
) -> Printed:
    body = built(made)
    return Printed(
        name=name,
        pose=pose,
        body=body,
        bed=bed,
        supports=supports,
        material=MATERIAL,
        print_settings=m.print_settings,
        connectors={OUTSIDE: Outside(body)},
    )


def gear(m: V8Master, name: str, made: BuildPart, pose: Location, teeth: int) -> Gear:
    body = built(made)
    return Gear(
        name=name,
        pose=pose,
        body=body,
        bed="-z",
        material=MATERIAL,
        print_settings=m.print_settings,
        teeth=teeth,
        module=m.timing_module,
        width=m.timing_width,
        connectors={OUTSIDE: Outside(body)},
    )


def stub(m: V8Master, at: Location) -> None:
    thin = m.layer - 2 * m.fits.sliding
    with Locations(at * Pos(Z=thin / 2)):
        Cylinder(m.pin_diameter / 2, m.layer, align=UP_FROM)


@part
def lobe(m: V8Master, valve: Valve) -> Printed:
    centre = m.cam_axis * Pos(Y=m.plane_a(valve))
    frame = m.hinge_on(centre, m.lobe_centre(valve, REST_TURN_DEG))
    thin = m.layer - 2 * m.fits.sliding
    turned = m.flat_turn(frame)
    with BuildPart() as made:
        with Locations(Pos(X=m.throw_cam)):
            Cylinder(m.lobe_radius, thin)
        flat = Pos(Z=-thin / 2) * Rot(Z=turned) * d_shape(m.cam_bore / 2, FLAT)
        extrude(flat, amount=thin, mode=Mode.SUBTRACT)
    return printed(m, LOBE, made, frame)


@part
def strap(m: V8Master, valve: Valve) -> Printed:
    centre = m.lobe_centre(valve, REST_TURN_DEG)
    pin = m.lifter_pin(valve, REST_TURN_DEG)
    frame = m.hinge_on(centre, pin)
    small = Pos(X=m.strap_length)
    with BuildPart() as made:
        web([(Location(), m.strap_radius), (small, m.eye)], m.layer - 2 * m.fits.sliding)
        bore(Location(), m.fits.printed(2 * m.lobe_radius))
        stub(m, small)
    return printed(m, STRAP, made, frame)


@part
def lifter(m: V8Master, valve: Valve) -> Printed:
    frame = m.lifter_frame(valve)
    thin = m.layer - 2 * m.fits.sliding
    with BuildPart() as made:
        with Locations(Pos(Z=-m.eye)):
            Box(2 * m.eye, thin, m.lifter_span + 2 * m.eye, align=UP_FROM)
        for z in (0.0, m.lifter_span):
            bore(Pos(Z=z) * ACROSS_THE_FACE, m.stub_hole)
    return printed(m, f"{valve.name} lifter", made, frame)


@part
def pushrod(m: V8Master, valve: Valve) -> Printed:
    frame = m.pushrod_frame(valve)
    end = Pos(X=m.pushrod_length(valve))
    with BuildPart() as made:
        web([(Location(), m.eye), (end, m.eye)], m.layer - 2 * m.fits.sliding)
        stub(m, Location())
        stub(m, end)
    return printed(m, PUSHROD, made, frame)


@part
def rocker(m: V8Master, valve: Valve) -> Printed:
    frame = m.rocker_frame(valve)
    arm = Pos(X=m.rocker_arm)
    nose = Rot(Z=m.nose_bend(valve)) * Pos(X=m.rocker_nose)
    with BuildPart() as made:
        web([(arm, m.eye), (Location(), m.eye), (nose, m.eye)], m.layer - 2 * m.fits.sliding)
        bore(Location(), m.fits.printed(m.rocker_shaft))
        bore(arm, m.stub_hole)
        bore(nose, m.stub_hole)
    return printed(m, f"{valve.name} rocker", made, frame)


@part
def toggle_link(m: V8Master, valve: Valve) -> Printed:
    frame = m.link_frame(valve)
    end = Pos(X=m.link_length)
    with BuildPart() as made:
        web([(Location(), m.eye), (end, m.eye)], m.layer - 2 * m.fits.sliding)
        stub(m, Location())
        stub(m, end)
    return printed(m, LINK, made, frame)


@part
def valve_stem(m: V8Master, valve: Valve) -> Printed:
    frame = m.valve_frame(valve)
    length = m.stem_length(valve)
    with BuildPart() as made:
        with Locations(Pos(Z=-length)):
            Cylinder(m.stem_diameter / 2, length - 2 * m.eye, align=UP_FROM)
        with Locations(Pos(Z=-length)):
            Cylinder(m.valve_head, m.valve_head_thickness, align=HANGING)
    return printed(m, f"{valve.name} stem", made, frame)


@part
def valve_cap(m: V8Master, valve: Valve) -> Printed:
    frame = m.valve_frame(valve)
    thin = m.layer - 2 * m.fits.sliding
    with BuildPart() as made:
        with Locations(Pos(Z=-m.eye)):
            Box(2 * m.eye, thin, 2 * m.eye, align=UP_FROM)
            Box(2 * m.eye, thin, 2 * m.eye, align=HANGING)
        bore(ACROSS_THE_FACE, m.stub_hole)
        with Locations(Pos(Z=-2 * m.eye)):
            Cylinder(m.stem_diameter / 2, m.eye, align=HANGING, mode=Mode.SUBTRACT)
    return printed(m, VALVE_CAP, made, frame)


def bank_valves(deg: float) -> list[Valve]:
    return [each for each in VALVES if each.cylinder.bank_deg == deg]


def head(m: V8Master, deg: float, name: str) -> Printed:
    frame = m.head_frame(deg)
    width = m.bank_width
    with BuildPart() as made:
        with Locations(Pos(X=m.head_overhang / 2)):
            Box(width + m.head_overhang, m.length, m.head_height, align=UP_FROM)
        for cylinder in CYLINDERS:
            if cylinder.bank_deg == deg:
                at = m.bank(deg, m.cylinder_y(cylinder)) * Pos(Z=m.deck)
                with Locations(frame.inverse() * at):
                    Cylinder(m.bore / 2, m.chamber, align=UP_FROM, mode=Mode.SUBTRACT)
        for y in m.post_ys(deg):
            at = m.bank(deg, y) * Pos(X=m.pivot_x, Z=m.deck + m.head_height)
            with Locations(frame.inverse() * at):
                Box(2 * m.eye, m.post_width, m.pivot_rise + m.eye, align=UP_FROM)
        for y in m.post_ys(deg):
            at = m.bank(deg, y) * Pos(X=m.pivot_x, Z=m.deck + m.head_height + m.pivot_rise)
            bore(frame.inverse() * at * ACROSS_THE_FACE, m.pressed_shaft)
        for valve in bank_valves(deg):
            at = m.in_plane(valve, m.valve_y_at(valve), m.valve_x, m.deck)
            bore(frame.inverse() * at, m.fits.printed(m.stem_diameter))
        for cylinder in CYLINDERS:
            if cylinder.bank_deg == deg:
                bore(frame.inverse() * m.plug_at(cylinder), m.fits.printed(m.plug_diameter))
        for spot in m.head_spots(deg):
            bore(frame.inverse() * spot, m.pivot_bore)
        for spot in m.header_spots(deg):
            insert_cut(frame.inverse() * spot, m.screw, fits=m.fits, stock=m.stock)
    return printed(m, name, made, frame, "+z")


@part
def left_head(m: V8Master) -> Printed:
    return head(m, m.left_bank, LEFT_HEAD)


@part
def right_head(m: V8Master) -> Printed:
    return head(m, m.right_bank, RIGHT_HEAD)


def guide(
    m: V8Master, deg: float, name: str, x: float, align: tuple[Align, Align, Align]
) -> Printed:
    frame = m.bank(deg, (m.front + m.rear) / 2) * Pos(X=m.lifter_x, Z=m.rail_low)
    spots = m.rail_spots(deg) if x < 0 else m.keeper_spots(deg)
    with BuildPart() as made:
        Box(m.rail_width, m.length, m.rail_height, align=align)
        for valve in bank_valves(deg):
            at = m.bank_of(valve, m.valve_y_at(valve)) * Pos(X=m.lifter_x, Z=m.rail_low)
            with Locations(frame.inverse() * at):
                Box(
                    2 * m.eye + 2 * m.fits.sliding,
                    m.layer,
                    m.rail_height,
                    align=UP_FROM,
                    mode=Mode.SUBTRACT,
                )
        for spot in spots:
            bore(frame.inverse() * spot, m.pivot_bore)
    return printed(m, name, made, frame, supports="under the overhangs")


@part
def left_rail(m: V8Master) -> Printed:
    return guide(m, m.left_bank, LEFT_RAIL, -1.0, FLOOR_RIGHT)


@part
def right_rail(m: V8Master) -> Printed:
    return guide(m, m.right_bank, RIGHT_RAIL, -1.0, FLOOR_RIGHT)


@part
def left_keeper(m: V8Master) -> Printed:
    return guide(m, m.left_bank, LEFT_KEEPER, 1.0, FLOOR_LEFT)


@part
def right_keeper(m: V8Master) -> Printed:
    return guide(m, m.right_bank, RIGHT_KEEPER, 1.0, FLOOR_LEFT)


@part
def camshaft(m: V8Master) -> Gear:
    frame = m.cam_pose
    with BuildPart() as made:
        add(gear_solid(m.cam_teeth, m.timing_width, m.timing_module))
        spur_teeth()
        turned = m.flat_turn(frame)
        flat = Rot(Z=turned) * d_shape(m.cam_diameter / 2, FLAT)
        extrude(flat, amount=m.camshaft_length)
    return gear(m, CAMSHAFT, made, frame, m.cam_teeth)


@part
def crank_gear(m: V8Master) -> Gear:
    frame = m.crank_gear_frame
    with BuildPart() as made:
        add(gear_solid(m.crank_teeth, m.timing_width, m.timing_module))
        spur_teeth()
        Cylinder(m.pulley_radius, m.pulley_width, align=HANGING)
        for spot in m.nose_spots:
            bore(frame.inverse() * spot, m.pivot_bore)
    return gear(m, CRANK_GEAR, made, frame, m.crank_teeth)


@part
def spark_plug(m: V8Master, at: Location) -> Printed:
    with BuildPart() as made:
        Cylinder(m.plug_diameter / 2, m.plug_length, align=UP_FROM)
    return printed(m, SPARK_PLUG, made, at)


def header(m: V8Master, deg: float, name: str) -> Printed:
    frame = m.header_frame(deg)
    with BuildPart() as made:
        Cylinder(m.header_diameter / 2, m.length, rotation=(90.0, 0.0, 0.0))
        for spot in m.header_spots(deg):
            bore(frame.inverse() * spot, m.pivot_bore)
    return printed(m, name, made, frame)


@part
def left_header(m: V8Master) -> Printed:
    return header(m, m.left_bank, LEFT_HEADER)


@part
def right_header(m: V8Master) -> Printed:
    return header(m, m.right_bank, RIGHT_HEADER)


@part
def battery_tray(m: V8Master) -> Printed:
    frame = m.tray_frame
    t = m.tray_thickness
    with BuildPart() as made:
        with Locations(Pos(Y=m.tray_length / 2)):
            Box(m.tray_width, m.tray_length, t, align=UP_FROM)
        with Locations(Pos(Y=m.tab_thickness / 2)):
            Box(m.tab_width, m.tab_thickness, m.tab_height, align=UP_FROM)
        for spot in m.tray_spots:
            bore(frame.inverse() * spot, m.pivot_bore)
    return printed(m, BATTERY_TRAY, made, frame)
