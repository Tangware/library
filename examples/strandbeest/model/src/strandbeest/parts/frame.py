from contextvars import Context

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
    Polygon,
    Pos,
    Rot,
    extrude,
)
from cad.design.parts import part
from cad.library.features.hardware import insert_cut
from cad.library.shapes import OUTSIDE, Outside, Printed, built

from strandbeest.features import break_edges
from strandbeest.master import LEFT, RIGHT, Module, StrandbeestMaster
from strandbeest.models import switch

LEFT_PLATE = "left plate"
RIGHT_PLATE = "right plate"
DECK = "deck"
SAIL = "sail"
MOTOR_CAP = "motor cap"
FLOOR_UP = (Align.CENTER, Align.CENTER, Align.MIN)
FACE_DOWN = (Align.CENTER, Align.CENTER, Align.MAX)


def printed(
    m: StrandbeestMaster,
    name: str,
    made: BuildPart,
    pose: Location,
    bed: str,
    supports: str = "",
    exterior: bool = False,
    material: str | None = None,
) -> Printed:
    body = built(made)
    return Printed(
        name=name,
        pose=pose,
        body=body,
        bed=bed,
        supports=supports,
        exterior=exterior,
        material=m.frame_material if material is None else material,
        print_settings=m.print_settings,
        connectors={OUTSIDE: Outside(body)},
    )


def plate(m: StrandbeestMaster, side: float, name: str) -> Printed:
    frame = m.plate_frame(side)
    t = m.plate_thickness
    top, bottom = m.deck_level - m.axle_height, m.axle_height - m.plate_bottom
    outside = -t if side == LEFT else t
    with BuildPart() as made:
        with Locations(Pos(Y=(bottom - top) / 2, Z=outside / 2)):
            Box(2 * m.plate_half_length, top + bottom, t)
        with Locations(
            *(Pos(X=x, Y=m.height_offset * m.scale, Z=t) for x in (-m.a * m.scale, m.a * m.scale))
        ):
            Hole(m.rod_hole / 2, 2 * t)
        if side == LEFT:
            with Locations(Pos(Z=t)):
                Hole(m.pin_bore / 2, 2 * t)
        else:
            with Locations(Pos(Z=t / 2)):
                Box(m.motor_pocket_width, m.motor_pocket_height, t, mode=Mode.SUBTRACT)
            for spot in m.cap_spots:
                insert_cut(frame.inverse() * spot, m.screw, fits=m.fits, stock=m.stock)
        for spot in m.deck_spots_on(side):
            local = frame.inverse() * spot
            with Locations(local):
                Hole(m.pivot_bore / 2, m.deck_screw_length - m.deck_thickness + m.fits.sliding)
            insert_cut(local, m.screw, fits=m.fits, stock=m.stock)
        break_edges(made, [Plane.XY], m.fits.min_wall)
    return printed(m, name, made, frame, "-z", exterior=True)


@part
def left_plate(m: StrandbeestMaster) -> Printed:
    return plate(m, LEFT, LEFT_PLATE)


@part
def right_plate(m: StrandbeestMaster) -> Printed:
    return plate(m, RIGHT, RIGHT_PLATE)


@part
def deck(m: StrandbeestMaster) -> Printed:
    long, wide = 2 * m.plate_half_length, 2 * m.plate_outer_y
    rim = m.fits.structural_wall
    inside_x = m.holder_width + 2 * m.fits.sliding
    inside_y = m.holder_length + 2 * m.fits.sliding
    frame = Location((0.0, 0.0, m.deck_level))
    with BuildPart() as made:
        Box(long, wide, m.deck_thickness, align=FLOOR_UP)
        with Locations(Pos(Z=m.deck_thickness)):
            Box(inside_x + 2 * rim, inside_y + 2 * rim, m.rim_height, align=FLOOR_UP)
            Box(inside_x, inside_y, m.rim_height, align=FLOOR_UP, mode=Mode.SUBTRACT)
        with Locations(frame.inverse() * m.switch_face):
            Box(m.holder_width, m.holder_height, m.switch_panel, align=FACE_DOWN)
            Box(
                m.switch_cutout,
                switch.CUTOUT_WIDTH,
                m.switch_panel,
                align=FACE_DOWN,
                mode=Mode.SUBTRACT,
            )
        with Locations(
            *(frame.inverse() * spot * Pos(Z=m.deck_thickness) for spot in m.deck_spots)
        ):
            Hole(m.pivot_bore / 2, m.deck_thickness)
        for module in m.modules:
            at = frame.inverse() * m.sail_at(module)
            with Locations(at):
                Cylinder(m.mast_diameter, m.mast_socket, align=FLOOR_UP)
            with Locations(at * Pos(Z=m.mast_socket)):
                Hole(m.fits.printed(m.mast_diameter) / 2, m.mast_socket + m.deck_thickness)
        break_edges(made, [Plane.XY], m.fits.min_wall)
    return printed(m, DECK, made, frame, "-z", exterior=True)


@part
def sail(m: StrandbeestMaster, module: Module) -> Printed:
    frame = m.sail_at(module) * Rot(X=90.0)
    with BuildPart() as made:
        with Locations(Pos(Z=-m.sail_thickness / 2)):
            extrude(Context().run(Polygon, *m.sail_outline, align=None), amount=m.sail_thickness)
        with Locations(Rot(X=-90.0)):
            Cylinder(m.mast_diameter / 2, m.sail_base, align=FLOOR_UP)
    return printed(m, SAIL, made, frame, "-z", material=m.sail_material)


@part
def motor_cap(m: StrandbeestMaster) -> Printed:
    frame = m.across(m.plate_outer_y)
    wall = m.fits.structural_wall
    depth = m.motor_behind_plate + wall
    width = m.motor_pocket_width + 2 * wall
    height = m.motor_pocket_height + 2 * wall
    with BuildPart() as made:
        Box(width, height, depth, align=FLOOR_UP)
        Box(2 * (m.cap_spot_x + m.pivot_radius), height, m.cap_flange, align=FLOOR_UP)
        Box(
            m.motor_pocket_width,
            m.motor_pocket_height,
            m.motor_behind_plate,
            align=FLOOR_UP,
            mode=Mode.SUBTRACT,
        )
        with Locations(Pos(Y=-height / 2, Z=depth - wall)):
            Box(width, 2 * wall, 2 * wall, mode=Mode.SUBTRACT)
        with Locations(*(Pos(X=x, Z=m.cap_flange) for x in (-m.cap_spot_x, m.cap_spot_x))):
            Hole(m.pivot_bore / 2, m.cap_flange)
        break_edges(made, [Plane.XY.offset(depth)], m.fits.min_wall)
    return printed(m, MOTOR_CAP, made, frame, "-z", "in the cavity", exterior=True)
