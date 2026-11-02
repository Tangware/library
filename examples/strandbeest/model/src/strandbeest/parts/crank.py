from contextvars import Context

from build123d import (
    Align,
    BuildPart,
    Circle,
    Cylinder,
    Hole,
    Locations,
    Pos,
    Rectangle,
)
from cad.design.parts import part
from cad.library.features.hardware import insert_cut
from cad.library.shapes import OUTSIDE, Outside, Printed, built

from strandbeest.features import cut_outline, web
from strandbeest.master import (
    MOTOR_SHAFT,
    MOTOR_SHAFT_DIAMETER,
    MOTOR_SHAFT_FLAT,
    CrankPiece,
    StrandbeestMaster,
)

UP_FROM = (Align.CENTER, Align.CENTER, Align.MIN)
DOWN_FROM = (Align.CENTER, Align.CENTER, Align.MAX)


@part
def crank(m: StrandbeestMaster, piece: CrankPiece) -> Printed:
    arm = m.crank_arm
    axle = Pos()
    core = m.pin_boss_radius
    hub = core + m.fits.structural_wall
    with BuildPart() as made:
        with Locations(Pos(Z=-arm)):
            Cylinder(core, m.crank_web, align=UP_FROM)
        if piece.low is not None:
            pin = m.pin_spot(piece.low)
            web([(axle, hub), (pin, core)], arm, -arm / 2)
            with Locations(pin):
                Hole(m.pivot_bore / 2, arm)
        if piece.high is not None:
            pin = m.pin_spot(piece.high)
            tip = pin * Pos(Z=arm + m.two_layers)
            web([(axle, hub), (pin, core)], arm, arm / 2)
            with Locations(pin * Pos(Z=arm)):
                Cylinder(m.crank_pin_diameter / 2, m.two_layers, align=UP_FROM)
            with Locations(tip):
                Hole(m.pivot_bore / 2, m.pin_screw_length - arm + m.fits.sliding)
            insert_cut(tip, m.screw, fits=m.fits, stock=m.stock)
        if piece.low is None:
            with Locations(Pos(Z=-arm)):
                Cylinder(
                    m.crank_pin_diameter / 2,
                    m.plate_thickness + m.fits.sliding,
                    align=DOWN_FROM,
                )
        if piece.high is None:
            radius = m.fits.printed(MOTOR_SHAFT_DIAMETER) / 2
            flat = Pos(Y=MOTOR_SHAFT_FLAT - MOTOR_SHAFT_DIAMETER)
            d_shape = Context().run(Circle, radius) - flat * Context().run(
                Rectangle, MOTOR_SHAFT_DIAMETER, MOTOR_SHAFT_DIAMETER
            )
            cut_outline(d_shape, Pos(Z=arm - MOTOR_SHAFT), MOTOR_SHAFT)
    body = built(made)
    return Printed(
        name=piece.name,
        pose=m.crank_frame(piece),
        body=body,
        bed="-z",
        supports="under the arms",
        material=m.leg_material,
        print_settings=m.print_settings,
        connectors={OUTSIDE: Outside(body)},
    )
