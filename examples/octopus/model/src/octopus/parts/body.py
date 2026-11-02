from build123d import (
    Align,
    Box,
    BuildPart,
    Cone,
    Cylinder,
    Hole,
    Location,
    Locations,
    Mode,
    Pos,
    Rot,
    Sphere,
)
from cad.design.parts import part
from cad.library.features.hardware import insert_cut
from cad.library.shapes import OUTSIDE, Outside, Printed, built

from octopus.features import MATERIAL, bore, web_at
from octopus.master import ARMS, OctopusMaster

BODY = "body"
MANTLE = "mantle"
MOTOR_CAP = "motor cap"
UP_FROM = (Align.CENTER, Align.CENTER, Align.MIN)
HANGING = (Align.CENTER, Align.CENTER, Align.MAX)
EYES = (-1.0, 1.0)


def printed(
    m: OctopusMaster,
    name: str,
    made: BuildPart,
    pose: Location,
    bed: str,
    supports: str = "",
    exterior: bool = False,
) -> Printed:
    body_part = built(made)
    return Printed(
        name=name,
        pose=pose,
        body=body_part,
        bed=bed,
        supports=supports,
        exterior=exterior,
        material=MATERIAL,
        print_settings=m.print_settings,
        connectors={OUTSIDE: Outside(body_part)},
    )


@part
def body(m: OctopusMaster) -> Printed:
    deck_top = m.body_height + m.saddle_floor
    with BuildPart() as made:
        Cylinder(m.foot_radius, m.foot_thickness, align=UP_FROM)
        Cylinder(m.stem_radius, m.seat_height, align=UP_FROM)
        with Locations(Pos(Z=deck_top)):
            Cylinder(m.deck_radius, m.deck_thickness, align=HANGING)
        with Locations(Pos(Z=deck_top - m.deck_thickness)):
            Cone(m.stem_radius, m.beak_radius, m.beak_length, align=HANGING)
        with Locations(m.mantle_seat):
            Cylinder(m.shelf_radius, m.shelf_thickness, align=HANGING)
        for arm in ARMS:
            height = m.saddle_bed_depth(arm)
            with Locations(m.saddle_at(arm)):
                Box(m.saddle_width, m.saddle_length, height, align=HANGING)
        for arm in ARMS:
            with Locations(m.saddle_at(arm)):
                Box(
                    m.motor_height + 2 * m.fits.sliding,
                    m.saddle_length,
                    m.motor_width + 2 * m.fits.sliding,
                    align=HANGING,
                    mode=Mode.SUBTRACT,
                )
        for arm in ARMS:
            with Locations(m.saddle_window(arm)):
                Box(
                    m.window_width,
                    m.window_length,
                    m.saddle_window_depth(arm),
                    align=UP_FROM,
                    mode=Mode.SUBTRACT,
                )
        for arm in ARMS:
            frame = m.spot(arm, 0.0, m.segment_y(0), 0.0)
            root = Pos(X=m.root_x)
            anchor = Pos(X=m.root_x, Y=-m.offset)
            foot_at = Pos(X=m.deck_radius - m.fits.structural_wall, Y=m.lug_foot)
            web_at(frame, [(root, m.eye), (anchor, m.eye), (foot_at, m.eye)], m.thin)
            with Locations(frame * root * Pos(Z=m.thin / 2)):
                Cylinder(m.pin_diameter / 2, m.layer, align=UP_FROM)
            bore(frame * anchor, m.stub_hole)
        for arm in ARMS:
            for spot in m.saddle_spots(arm):
                insert_cut(spot, m.screw, fits=m.fits, stock=m.stock)
        for spot in m.mantle_spots:
            insert_cut(spot, m.screw, fits=m.fits, stock=m.stock)
        for arm in ARMS:
            with Locations(m.lead_hole(arm)):
                Hole(m.pivot_bore, m.shelf_thickness)
    return printed(m, BODY, made, Location(), "-z", "under the overhangs", exterior=True)


@part
def motor_cap(m: OctopusMaster, arm: int) -> Printed:
    frame = m.saddle_at(arm)
    with BuildPart() as made:
        Box(m.saddle_width, m.saddle_length, m.cap_thickness, align=UP_FROM)
        with Locations(
            *(frame.inverse() * each * Pos(Z=m.cap_thickness) for each in m.saddle_spots(arm))
        ):
            Hole(m.pivot_bore / 2, m.cap_thickness)
    return printed(m, MOTOR_CAP, made, frame, "-z", exterior=True)


@part
def mantle(m: OctopusMaster) -> Printed:
    frame = m.mantle_seat
    r = m.mantle_radius
    with BuildPart() as made:
        Sphere(r)
        for side in EYES:
            with Locations(Rot(Z=side * m.eye_tilt_deg) * Pos(X=r) * Rot(Y=90.0)):
                Cylinder(m.eye_radius, 2 * m.eye_depth)
        with Locations(Rot(Z=180.0) * Pos(X=r, Z=m.siphon_radius) * Rot(Y=90.0)):
            Cylinder(m.siphon_radius, m.siphon_length)
        Sphere(r - m.mantle_wall, mode=Mode.SUBTRACT)
        with Locations(Pos()):
            Box(4 * r, 4 * r, 2 * r, align=HANGING, mode=Mode.SUBTRACT)
        Cylinder(m.flange_radius, m.flange, align=UP_FROM)
        Cylinder(r - m.mantle_wall, m.flange, align=UP_FROM, mode=Mode.SUBTRACT)
        with Locations(*(frame.inverse() * spot * Pos(Z=m.flange) for spot in m.mantle_spots)):
            Hole(m.pivot_bore / 2, m.flange)
    return printed(m, MANTLE, made, frame, "+z", "inside the dome", exterior=True)
