from build123d import Align, Box, BuildPart, Cylinder, Location, Locations, Mode, Plane, Pos, Rot
from cad.design.parts import part
from cad.library.shapes import OUTSIDE, Outside, Printed, built

from v8.features import bore, break_edges, web
from v8.master import V8Master

ROD = "rod"
PISTON = "piston"
ABOVE = (Align.CENTER, Align.CENTER, Align.MIN)
RING_PITCH = 2.0
RING_WIDTH = 0.6


@part
def rod(m: V8Master, at: Location) -> Printed:
    small, big = Location(), Location((m.rod, 0.0, 0.0))
    with BuildPart() as made:
        web([(small, m.small_end_radius), (big, m.small_end_radius)], m.rod_thickness)
        web([(big, m.big_end_radius)], m.rod_thickness)
        bore(small, m.fits.printed(m.wrist_pin_diameter))
        bore(big, m.pin_bore)
        faces = [Plane.XY.offset(m.rod_thickness / 2), Plane.XY.offset(-m.rod_thickness / 2)]
        break_edges(made, faces, m.fits.min_wall / 2)
    body = built(made)
    return Printed(
        name=ROD,
        pose=at,
        body=body,
        bed="-z",
        material=m.moving_material,
        print_settings=m.print_settings,
        connectors={OUTSIDE: Outside(body)},
    )


@part
def piston(m: V8Master, at: Location, number: int) -> Printed:
    radius = m.bore / 2 - m.fits.sliding
    height = m.compression_height + m.skirt
    slot_height = m.skirt + m.small_end_radius + m.fits.structural_wall
    with BuildPart() as made:
        with Locations(Pos(Z=-m.skirt)):
            Cylinder(radius, height, align=ABOVE)
        with Locations(Pos(Z=-m.skirt)):
            Box(
                2 * radius,
                m.rod_pitch,
                slot_height,
                align=ABOVE,
                mode=Mode.SUBTRACT,
            )
        for n in (1, 2, 3):
            z = m.compression_height - n * RING_PITCH
            with Locations(Pos(Z=z)):
                Cylinder(radius, RING_WIDTH, mode=Mode.SUBTRACT)
                Cylinder(radius - RING_WIDTH, RING_WIDTH)
        bore(Rot(X=90.0), m.fits.pressed(m.wrist_pin_diameter))
        break_edges(made, [Plane.XY.offset(m.compression_height)], m.fits.min_wall / 2)
    body = built(made)
    return Printed(
        name=f"{PISTON} {number}",
        pose=at,
        body=body,
        bed="+z",
        material=m.moving_material,
        print_settings=m.print_settings,
        connectors={OUTSIDE: Outside(body)},
    )
