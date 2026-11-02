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
)
from cad.design.parts import part
from cad.library.features.hardware import insert_cut
from cad.library.shapes import OUTSIDE, Outside, Printed, built

from v8.features import bore, break_edges
from v8.master import CYLINDERS, JOURNALS, LEFT_BANK_DEG, RIGHT_BANK_DEG, V8Master

BLOCK = "block"
REAR_PLATE = "rear plate"
MOTOR_CAP = "motor cap"
FLOOR_UP = (Align.CENTER, Align.CENTER, Align.MIN)
HANGING = (Align.CENTER, Align.CENTER, Align.MAX)
ALONG_THE_CRANK = Rot(X=-90.0)


def printed(
    m: V8Master,
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
        material=m.block_material,
        print_settings=m.print_settings,
        connectors={OUTSIDE: Outside(body)},
    )


@part
def block(m: V8Master) -> Printed:
    middle = (m.front + m.rear) / 2
    cavity_middle = (m.wall_inside + m.rear) / 2
    cavity = m.rear - m.wall_inside
    with BuildPart() as made:
        for bank in (LEFT_BANK_DEG, RIGHT_BANK_DEG):
            with Locations(m.axle * Pos(Y=middle) * Rot(Y=bank)):
                Box(m.bank_width, m.length, m.deck, align=FLOOR_UP)
        with Locations(Pos(Y=middle)):
            Box(2 * m.case_half, m.length, m.axle_height, align=FLOOR_UP)
        ends = (m.front + m.cam_pad / 2, m.rear - m.cam_pad / 2)
        for bank in (LEFT_BANK_DEG, RIGHT_BANK_DEG):
            for y in ends:
                with Locations(m.bank(bank, y) * Pos(X=m.pad_x, Z=m.rail_low)):
                    Box(m.pad_width, m.cam_pad, m.pad_height, align=HANGING)
        with Locations(m.axle * Pos(Y=cavity_middle) * ALONG_THE_CRANK):
            Cylinder(m.swing_radius, cavity, mode=Mode.SUBTRACT)
        with Locations(Pos(Y=cavity_middle)):
            Box(2 * m.swing_radius, cavity, m.axle_height, align=FLOOR_UP, mode=Mode.SUBTRACT)
        for cylinder in CYLINDERS:
            with Locations(m.bank_axis(cylinder)):
                Cylinder(
                    m.bore / 2,
                    m.deck,
                    align=FLOOR_UP,
                    mode=Mode.SUBTRACT,
                )
        with Locations(m.axle * Pos(Y=m.wall_inside - m.wall / 2) * ALONG_THE_CRANK):
            Cylinder(
                m.crank_pin_diameter / 2 + m.fits.structural_wall + m.fits.printed_hole / 2,
                m.wall,
                mode=Mode.SUBTRACT,
            )
        for journal in JOURNALS:
            with Locations(Pos(Y=m.journal_y(journal))):
                Box(
                    2 * m.case_half,
                    m.pin_length + 2 * m.fits.sliding,
                    m.axle_height + m.big_end_radius,
                    align=FLOOR_UP,
                    mode=Mode.SUBTRACT,
                )
        for cylinder in CYLINDERS:
            with Locations(m.wrist_pin_at(cylinder)):
                Cylinder(
                    m.wrist_pin_diameter / 2 + m.fits.membrane,
                    m.wrist_access,
                    align=FLOOR_UP,
                    mode=Mode.SUBTRACT,
                )
        bore(m.cam_axis * ALONG_THE_CRANK, m.cam_bore)
        for spot in m.plate_spots:
            insert_cut(spot, m.screw, fits=m.fits, stock=m.stock)
        for bank in (LEFT_BANK_DEG, RIGHT_BANK_DEG):
            for spot in (*m.head_spots(bank), *m.rail_spots(bank), *m.keeper_spots(bank)):
                insert_cut(spot, m.screw, fits=m.fits, stock=m.stock)
        break_edges(made, [Plane(Pos(Y=m.front) * ALONG_THE_CRANK)], m.fits.min_wall / 2)
    return printed(m, BLOCK, made, Location(), "-z", "under the overhangs", exterior=True)


@part
def rear_plate(m: V8Master) -> Printed:
    frame = Location((0.0, m.rear, 0.0))
    t = m.plate_thickness
    with BuildPart() as made:
        with Locations(Pos(Y=t / 2, Z=m.plate_top / 2)):
            Box(2 * m.case_half, t, m.plate_top)
        with Locations(Pos(Y=t / 2, Z=m.axle_height)):
            Box(m.motor_pocket_width, t, m.motor_pocket_height, mode=Mode.SUBTRACT)
        with Locations(*(frame.inverse() * m.plate_screw_at(spot) for spot in m.plate_spots)):
            Hole(m.pivot_bore / 2, t)
        for spot in m.cap_spots:
            insert_cut(frame.inverse() * spot, m.screw, fits=m.fits, stock=m.stock)
        for spot in m.tray_spots:
            insert_cut(frame.inverse() * spot, m.screw, fits=m.fits, stock=m.stock)
        break_edges(made, [Plane.XY], m.fits.min_wall)
    return printed(m, REAR_PLATE, made, frame, "-y", exterior=True)


@part
def motor_cap(m: V8Master) -> Printed:
    frame = m.across(m.plate_outer_y)
    wall = m.fits.structural_wall
    depth = m.motor_behind_plate + wall
    width = m.motor_pocket_width + 2 * wall
    height = m.motor_pocket_height + 2 * wall
    with BuildPart() as made:
        Box(width, height, depth, align=FLOOR_UP)
        Box(2 * (m.cap_spot_x + m.pivot_bore), height, m.cap_flange, align=FLOOR_UP)
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
