from contextvars import Context

from build123d import (
    Align,
    Box,
    BuildPart,
    Circle,
    Cylinder,
    Hole,
    Location,
    Locations,
    Mode,
    Plane,
    Pos,
    Rectangle,
    Rot,
    add,
    extrude,
)
from cad.design.parts import part
from cad.library.features.hardware import insert_cut
from cad.library.gears import Gear, gear_solid, spur_teeth
from cad.library.shapes import OUTSIDE, Outside, Printed, built

from cessna.features import bore, break_edges, cut_outline, outline
from cessna.master import (
    MOTOR_SHAFT,
    MOTOR_SHAFT_DIAMETER,
    MOTOR_SHAFT_FLAT,
    SIDES,
    CessnaMaster,
    side_name,
)

OUTPUT_SHAFT = "output shaft"
RACK = "rack"
MOTOR_PINION = "motor pinion"
SHAFT_YOKE = "shaft yoke"
SPIDER = "spider"
SIDE_TUBE = "side tube"
SPRING_LEG = "spring leg"
WHEEL = "wheel"
UP_FROM = (Align.CENTER, Align.CENTER, Align.MIN)
DOWN_FROM = (Align.CENTER, Align.CENTER, Align.MAX)
SPOKES = 3


def printed(
    m: CessnaMaster,
    name: str,
    made: BuildPart,
    pose: Location,
    bed: str,
    supports: str = "",
    material: str | None = None,
) -> Printed:
    body = built(made)
    return Printed(
        name=name,
        pose=pose,
        body=body,
        bed=bed,
        supports=supports,
        material=m.gear_material if material is None else material,
        print_settings=m.print_settings,
        connectors={OUTSIDE: Outside(body)},
    )


def gear(
    m: CessnaMaster,
    name: str,
    made: BuildPart,
    pose: Location,
    teeth: int,
    width: float,
    supports: str = "",
) -> Gear:
    body = built(made)
    return Gear(
        name=name,
        pose=pose,
        body=body,
        bed="-z",
        supports=supports,
        material=m.gear_material,
        print_settings=m.print_settings,
        teeth=teeth,
        module=m.module,
        width=width,
        connectors={OUTSIDE: Outside(body)},
    )


def fork(m: CessnaMaster, turned: Location, down: float, base: float) -> None:
    span = 2 * (m.fork_half + m.fork_wall)
    length = m.fork_reach + m.fork_boss
    middle = down * (m.fork_reach - m.fork_boss) / 2
    with Locations(turned * Pos(Z=middle)):
        Box(span, m.fork_width, length)
    with Locations(turned * Pos(Z=down * (m.fork_reach + base / 2))):
        Box(span, m.fork_width, base)
    with Locations(turned * Pos(Z=middle)):
        Box(2 * m.fork_half, m.fork_width, length, mode=Mode.SUBTRACT)
    bore(turned * Rot(Y=90.0), m.pivot_bore)


def fork_cheeks(m: CessnaMaster, made: BuildPart) -> None:
    outside = m.fork_half + m.fork_wall
    cheeks = [Plane.YZ.offset(outside), Plane.YZ.offset(-outside)]
    break_edges(made, cheeks, m.fits.min_wall / 2)


@part
def output_shaft(m: CessnaMaster) -> Gear:
    width = m.gear_width
    with BuildPart() as made:
        with Locations(Pos(Z=-width / 2)):
            add(gear_solid(m.output_teeth, width, m.module))
        spur_teeth()
        with Locations(Pos(Z=-m.shaft_half)):
            Cylinder(m.shaft_diameter / 2, 2 * m.shaft_half, align=UP_FROM)
        for side in SIDES:
            bore(m.shaft_frame.inverse() * m.hub_pin(side), m.fits.printed(m.dowel_diameter))
        ends = [Plane.XY.offset(m.shaft_half), Plane.XY.offset(-m.shaft_half)]
        break_edges(made, ends, m.fits.min_wall / 2)
    return gear(m, OUTPUT_SHAFT, made, m.shaft_frame, m.output_teeth, width)


@part
def rack(m: CessnaMaster) -> Gear:
    width = m.rack_width
    radius = m.rack_radius
    start, end = m.rack_ends
    wedge = outline(m.rack_wedge)
    with BuildPart() as made:
        with Locations(Pos(Z=-width / 2)):
            add(gear_solid(m.rack_teeth, width, m.module))
        spur_teeth()
        Cylinder(radius - m.rack_rim, width, mode=Mode.SUBTRACT)
        extrude(Pos(Z=-width / 2) * wedge, amount=width, mode=Mode.INTERSECT)
        Cylinder(2 * m.fork_wall, width)
        for n in range(SPOKES):
            angle = start + n * (end - start) / (SPOKES - 1)
            middle = (radius - m.rack_rim / 2) / 2
            with Locations(Rot(Z=angle) * Pos(X=middle)):
                Box(radius - m.rack_rim / 2, 2 * m.fork_wall, width)
        bore(Location(), m.fits.printed(m.dowel_diameter))
    return gear(m, RACK, made, m.rack_pose, m.rack_teeth, width, "under the overhangs")


@part
def motor_pinion(m: CessnaMaster) -> Gear:
    width = m.gear_width
    with BuildPart() as made:
        with Locations(Pos(Z=-width / 2)):
            add(gear_solid(m.motor_teeth, width, m.module))
        spur_teeth()
        radius = m.fits.printed(MOTOR_SHAFT_DIAMETER) / 2
        flat = Pos(Y=MOTOR_SHAFT_FLAT - MOTOR_SHAFT_DIAMETER)
        d_shape = Context().run(Circle, radius) - flat * Context().run(
            Rectangle, MOTOR_SHAFT_DIAMETER, MOTOR_SHAFT_DIAMETER
        )
        cut_outline(d_shape, Pos(Z=width / 2 - MOTOR_SHAFT) * Rot(Z=-m.pinion_turn), MOTOR_SHAFT)
    return gear(m, MOTOR_PINION, made, m.pinion_pose, m.motor_teeth, width)


@part
def shaft_yoke(m: CessnaMaster, side: float) -> Printed:
    frame = m.yoke(side)
    with BuildPart() as made:
        fork(m, Location(), -1.0, m.fork_base)
        with Locations(Pos(Z=-m.fork_reach)):
            Hole(m.bored / 2, m.fork_base)
        bore(frame.inverse() * m.hub_pin(side), m.fits.pressed(m.dowel_diameter))
        fork_cheeks(m, made)
    return printed(m, side_name(side, SHAFT_YOKE), made, frame, "-z", "under the fork")


@part
def spider(m: CessnaMaster, side: float) -> Printed:
    frame = m.spider_frame(side)
    with BuildPart() as made:
        Box(m.spider, m.spider, m.spider)
        for spot in (*m.yoke_screw_spots(side), *m.tube_screw_spots(side)):
            insert_cut(frame.inverse() * spot, m.screw, fits=m.fits, stock=m.stock)
        faces = [Plane.XY.offset(m.spider / 2), Plane.XY.offset(-m.spider / 2)]
        break_edges(made, faces, m.fits.min_wall / 2)
    return printed(m, side_name(side, SPIDER), made, frame, "-z")


@part
def side_tube(m: CessnaMaster, side: float) -> Printed:
    frame = m.tube(side)
    start = m.fork_reach + m.tube_fork_base
    with BuildPart() as made:
        fork(m, Location(), 1.0, m.tube_fork_base)
        with Locations(Pos(Z=start)):
            Cylinder(
                m.shaft_diameter / 2,
                m.tube_length + m.boss_radius - start,
                align=UP_FROM,
            )
        bore(frame.inverse() * m.leg_pin(side), m.fits.printed(m.dowel_diameter))
        fork_cheeks(m, made)
        tip = Plane.XY.offset(m.tube_length + m.boss_radius)
        break_edges(made, [tip], m.fits.min_wall / 2)
    return printed(m, side_name(side, SIDE_TUBE), made, frame, "-z")


@part
def spring_leg(m: CessnaMaster, side: float) -> Printed:
    root = m.tube_end(side)
    frame = m.leg_frame(side)
    face = m.axle_face(side)
    with BuildPart() as made:
        with Locations(frame.inverse() * root):
            Cylinder(m.boss_radius, m.fork_width)
        Box(m.leg_thickness, m.leg_width, m.leg_reach(side), align=UP_FROM)
        with Locations(frame.inverse() * m.leg_boss(side)):
            Cylinder(m.boss_radius, m.boss_length)
        bore(frame.inverse() * root, m.bored)
        bore(frame.inverse() * m.leg_pin(side), m.fits.pressed(m.dowel_diameter))
        insert_cut(frame.inverse() * face, m.screw, fits=m.fits, stock=m.stock)
    return printed(m, side_name(side, SPRING_LEG), made, frame, "+z")


@part
def wheel(m: CessnaMaster, side: float) -> Printed:
    frame = m.axle(side)
    half = m.wheel_width / 2
    with BuildPart() as made:
        Cylinder(m.wheel_radius, m.wheel_width)
        with Locations(Pos(Z=half)):
            Cylinder(m.wheel_radius / 2, m.head_room, align=DOWN_FROM, mode=Mode.SUBTRACT)
        bore(Location(), m.pivot_bore)
        faces = [Plane.XY.offset(half), Plane.XY.offset(-half)]
        break_edges(made, faces, m.fits.min_wall)
    return printed(
        m, side_name(side, WHEEL), made, frame, "-z", "under the overhangs", m.tyre_material
    )
