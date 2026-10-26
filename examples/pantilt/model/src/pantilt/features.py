from build123d import (
    Align,
    BuildSketch,
    Circle,
    Cylinder,
    Location,
    Locations,
    Mode,
    Plane,
    Pos,
    Rectangle,
)
from cad.library.features.cuts import extrude_to
from cad.library.features.hardware import insert_holes
from cad.library.standard.fasteners import clearance_hole, head_diameter

from pantilt.master import ProductMaster
from pantilt.models import stepper

ABOVE = (Align.CENTER, Align.CENTER, Align.MIN)


def d_bore(m: ProductMaster, flange: Location, start: float, depth: float) -> None:
    radius = m.fits.printed(stepper.SHAFT_DIAMETER) / 2
    flat = stepper.SHAFT_DIAMETER / 2 - stepper.FLAT_DEPTH + m.fits.printed_hole / 2
    with BuildSketch(Plane(flange * Pos(Z=start))) as bore:
        Circle(radius)
        with Locations(Pos(X=flat)):
            Rectangle(radius, 2 * radius, align=(Align.MIN, Align.CENTER), mode=Mode.SUBTRACT)
    extrude_to(
        Plane(flange * Pos(Z=start)),
        Plane(flange * Pos(Z=start + depth)),
        sketch=bore,
        mode=Mode.SUBTRACT,
    )


def shaft_clamp(m: ProductMaster, spot: Location, out_to: float, name: str) -> None:
    insert_holes(Plane(spot), [spot], m.screw, name, fits=m.fits, stock=m.stock)
    with Locations(spot):
        clearance_hole(m.screw, m.clamp_screw_length, fits=m.fits)
    with Locations(spot):
        Cylinder(
            m.fits.printed(head_diameter(m.screw)) / 2, out_to, align=ABOVE, mode=Mode.SUBTRACT
        )
