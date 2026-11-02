from contextvars import Context

from build123d import Align, BuildPart, Circle, Cylinder, Hole, Locations, Pos, Rectangle
from cad.design.parts import part
from cad.library.features.hardware import insert_cut
from cad.library.shapes import OUTSIDE, Outside, Printed, built

from v8.features import cut_outline, web
from v8.master import (
    MOTOR_SHAFT,
    MOTOR_SHAFT_DIAMETER,
    MOTOR_SHAFT_FLAT,
    CrankPiece,
    V8Master,
)

UP_FROM = (Align.CENTER, Align.CENTER, Align.MIN)
DOWN_FROM = (Align.CENTER, Align.CENTER, Align.MAX)


@part
def crank(m: V8Master, piece: CrankPiece) -> Printed:
    arm = m.arm
    axle = Pos()
    core = m.crank_pin_diameter / 2 + m.fits.structural_wall
    hub = core + m.fits.membrane
    with BuildPart() as made:
        with Locations(Pos(Z=-arm)):
            Cylinder(core, m.web, align=UP_FROM)
        if piece.low is not None:
            pin = m.pin_spot(piece, piece.low)
            web([(axle, hub), (pin, core)], arm, -arm / 2)
            with Locations(pin * Pos(Z=-arm)):
                Cylinder(m.crank_pin_diameter / 2, m.pin_length, align=DOWN_FROM)
            with Locations(pin):
                Hole(m.pivot_bore / 2, arm + m.pin_length)
        if piece.high is not None:
            pin = m.pin_spot(piece, piece.high)
            face = pin * Pos(Z=arm)
            web([(axle, hub), (pin, core)], arm, arm / 2)
            with Locations(face):
                Hole(m.pivot_bore / 2, m.pin_screw_length - arm - m.pin_length + m.fits.sliding)
            insert_cut(face, m.screw, fits=m.fits, stock=m.stock)
        if piece.low is None:
            with Locations(Pos(Z=-arm)):
                Cylinder(core, m.wall + 2 * m.fits.sliding, align=DOWN_FROM)
            for spot in m.nose_spots:
                insert_cut(
                    m.crank_frame(piece).inverse() * spot, m.screw, fits=m.fits, stock=m.stock
                )
            web([(axle, hub), (m.counter_spot(piece, piece.high), core)], arm, arm / 2)
        if piece.high is None:
            with Locations(Pos(Z=arm)):
                Cylinder(m.swing_radius - m.fits.sliding, m.flywheel, align=UP_FROM)
            with Locations(m.pin_spot(piece, piece.low) * Pos(Z=arm + m.flywheel)):
                Hole(m.head_access, arm + m.flywheel)
            radius = m.fits.printed(MOTOR_SHAFT_DIAMETER) / 2
            flat = Pos(Y=MOTOR_SHAFT_FLAT - MOTOR_SHAFT_DIAMETER)
            d_shape = Context().run(Circle, radius) - flat * Context().run(
                Rectangle, MOTOR_SHAFT_DIAMETER, MOTOR_SHAFT_DIAMETER
            )
            cut_outline(d_shape, Pos(Z=arm + m.flywheel - MOTOR_SHAFT), MOTOR_SHAFT)
    body = built(made)
    return Printed(
        name=piece.name,
        pose=m.crank_frame(piece),
        body=body,
        bed="-z",
        supports="under the webs",
        material=m.moving_material,
        print_settings=m.print_settings,
        connectors={OUTSIDE: Outside(body)},
    )
