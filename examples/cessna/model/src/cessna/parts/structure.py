from build123d import (
    Align,
    Box,
    BuildPart,
    Cylinder,
    Hole,
    Location,
    Locations,
    Mode,
    Plane,
    Pos,
    Rot,
    extrude,
)
from cad.design.parts import part
from cad.library.features.hardware import insert_cut
from cad.library.shapes import OUTSIDE, Outside, Printed, built

from cessna.features import bore, break_edges, outline
from cessna.master import SIDES, CessnaMaster, side_name
from cessna.models import switch

STAND = "stand"
MAIN_PLATE = "main plate"
PILLOW_BLOCK = "pillow block"
TUBE_HANGER = "tube hanger"
PIVOT_BRACKET = "pivot bracket"
MOTOR_SADDLE = "motor saddle"
FLOOR_UP = (Align.CENTER, Align.CENTER, Align.MIN)
HANGING = (Align.CENTER, Align.CENTER, Align.MAX)
ALONG_THE_SHAFT = Rot(Y=90.0)


def printed(
    m: CessnaMaster,
    name: str,
    made: BuildPart,
    pose: Location,
    bed: str,
    supports: str = "",
    exterior: bool = False,
) -> Printed:
    body = built(made)
    return Printed(
        name=name,
        pose=pose,
        body=body,
        bed=bed,
        supports=supports,
        exterior=exterior,
        material=m.structure_material,
        print_settings=m.print_settings,
        connectors={OUTSIDE: Outside(body)},
    )


@part
def stand(m: CessnaMaster) -> Printed:
    fore, aft = m.fore_column_y, m.aft_column_y
    length = aft - fore + m.column_depth
    with BuildPart() as made:
        with Locations(Pos(Y=(fore + aft) / 2)):
            Box(m.base_width, length, m.base_thickness, align=FLOOR_UP)
        with Locations(Pos(Y=fore), Pos(Y=aft)):
            Box(m.column_width, m.column_depth, m.plate_bottom, align=FLOOR_UP)
        with Locations(m.holder_at):
            Box(
                m.holder_length + 2 * m.fits.sliding,
                m.holder_width + 2 * m.fits.sliding,
                m.holder_recess,
                align=FLOOR_UP,
                mode=Mode.SUBTRACT,
            )
        with Locations(m.switch_face):
            Box(m.holder_width, m.holder_height, m.switch_panel, align=HANGING)
            Box(
                m.switch_cutout,
                switch.CUTOUT_WIDTH,
                m.switch_panel,
                align=HANGING,
                mode=Mode.SUBTRACT,
            )
        for y in (fore, aft):
            for spot in m.column_spots(y):
                insert_cut(spot, m.screw, fits=m.fits, stock=m.stock)
        break_edges(made, [Plane.XY], m.fits.min_wall)
    return printed(m, STAND, made, Location(), "-z")


@part
def main_plate(m: CessnaMaster) -> Printed:
    frame = Location((0.0, 0.0, m.plate_bottom))
    t = m.plate_thickness
    holes = (
        *m.column_spots(m.fore_column_y),
        *m.column_spots(m.aft_column_y),
        *(spot for side in SIDES for spot in (*m.pillow_spots(side), *m.hanger_spots(side))),
        *m.saddle_spots,
    )
    with BuildPart() as made:
        extrude(outline(m.plate_outline), amount=t)
        with Locations(Pos(X=-m.rail_x, Z=t), Pos(X=m.rail_x, Z=t)):
            Box(m.rail_thickness, m.rail_length, m.rail_height, align=FLOOR_UP)
        pitch = m.rail_length / (m.rail_holes + 1)
        for n in range(m.rail_holes):
            y = (n + 1) * pitch - m.rail_length / 2
            bore(Pos(Y=y, Z=t + m.rail_height / 2) * ALONG_THE_SHAFT, m.rail_height / 2)
        with Locations(Pos(Z=t / 2)):
            Box(m.gear_width + 2 * m.fits.sliding, 2 * m.rack_radius, t, mode=Mode.SUBTRACT)
        with Locations(*(frame.inverse() * spot * Pos(Z=t) for spot in holes)):
            Hole(m.pivot_bore / 2, t)
        break_edges(made, [Plane.XY], m.fits.min_wall)
    return printed(m, MAIN_PLATE, made, frame, "-z", exterior=True)


@part
def pillow_block(m: CessnaMaster, side: float) -> Printed:
    frame = m.pillow(side)
    wall = m.fits.structural_wall
    drop = m.plate_rise + m.bored / 2 + wall
    with BuildPart() as made:
        Box(m.pillow_width, m.pillow_depth, drop, align=HANGING)
        bore(frame.inverse() * m.shaft_at * ALONG_THE_SHAFT, m.bored)
        for spot in m.pillow_spots(side):
            insert_cut(frame.inverse() * spot, m.screw, fits=m.fits, stock=m.stock)
        break_edges(made, [Plane.XY.offset(-drop)], m.fits.min_wall)
    return printed(m, side_name(side, PILLOW_BLOCK), made, frame, "+z")


@part
def tube_hanger(m: CessnaMaster, side: float) -> Printed:
    at = m.hanger(side)
    frame = m.hanger_top(side)
    radius = m.bored / 2 + m.fits.structural_wall
    drop = m.hanger_drop(side)
    with BuildPart() as made:
        Box(2 * radius, m.pillow_depth, drop, align=HANGING)
        with Locations(frame.inverse() * at):
            Cylinder(radius, m.hanger_length)
        bore(frame.inverse() * at, m.bored)
        for spot in m.hanger_spots(side):
            insert_cut(frame.inverse() * spot, m.screw, fits=m.fits, stock=m.stock)
    return printed(m, side_name(side, TUBE_HANGER), made, frame, "+z")


@part
def pivot_bracket(m: CessnaMaster) -> Printed:
    frame = Location((0.0, 0.0, m.plate_top))
    t = m.plate_thickness
    gap = m.rack_width / 2 + m.fits.sliding
    height = m.bracket_height
    with BuildPart() as made:
        Box(2 * (m.pillow_x + m.pillow_width / 2), m.bracket_depth, t, align=FLOOR_UP)
        with Locations(
            *(Pos(X=sign * (gap + m.bracket_thickness / 2)) for sign in (-1.0, 1.0)),
        ):
            Box(m.bracket_thickness, m.bracket_depth, height, align=FLOOR_UP)
        with Locations(Pos(Z=height - t)):
            Box(2 * gap, m.bracket_depth, t, align=FLOOR_UP)
        Box(2 * gap, m.bracket_depth, t, align=FLOOR_UP, mode=Mode.SUBTRACT)
        with Locations(
            *(
                frame.inverse() * spot * Pos(Z=m.plate_thickness + t)
                for side in SIDES
                for spot in m.pillow_spots(side)
            )
        ):
            Hole(m.pivot_bore / 2, t)
        bore(frame.inverse() * m.pivot * ALONG_THE_SHAFT, m.fits.pressed(m.dowel_diameter))
        break_edges(made, [Plane.XY], m.fits.min_wall)
    return printed(m, PIVOT_BRACKET, made, frame, "-z", "under the top bar")


@part
def motor_saddle(m: CessnaMaster) -> Printed:
    frame = m.saddle
    length = m.motor_length + 2 * m.fits.structural_wall
    depth = m.motor_height + 2 * m.fits.structural_wall
    pocket = m.motor_width + 2 * m.fits.sliding
    with BuildPart() as made:
        with Locations(Pos(X=m.motor_length / 2 + m.fits.structural_wall)):
            Box(length, m.saddle_width, depth, align=HANGING)
        with Locations(Pos(X=m.motor_length / 2 + m.fits.structural_wall)):
            Box(
                m.motor_length + 2 * m.fits.structural_wall,
                pocket,
                m.motor_height + 2 * m.fits.sliding,
                align=HANGING,
                mode=Mode.SUBTRACT,
            )
        for spot in m.saddle_spots:
            insert_cut(frame.inverse() * spot, m.screw, fits=m.fits, stock=m.stock)
        break_edges(made, [Plane.XY.offset(-depth)], m.fits.min_wall)
    return printed(m, MOTOR_SADDLE, made, frame, "+z", "in the motor pocket", exterior=True)
