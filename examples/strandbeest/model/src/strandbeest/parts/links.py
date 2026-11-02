from contextvars import Context

from build123d import (
    BuildPart,
    Location,
    Plane,
    Pos,
    RegularPolygon,
)
from cad.design.parts import part
from cad.library.shapes import OUTSIDE, Outside, Printed, built

from strandbeest.features import bore, break_edges, cut_outline, web
from strandbeest.master import StrandbeestMaster

UPPER_LINK = "upper link"
LOWER_LINK = "lower link"
ROCKER = "rocker"
COUPLER = "coupler"
TRIANGLE = "triangle"
FOOT = "foot"
SIX_SIDED = 6


def faces_broken(m: StrandbeestMaster, body: BuildPart, thickness: float) -> None:
    faces = [Plane.XY.offset(thickness / 2), Plane.XY.offset(-thickness / 2)]
    break_edges(body, faces, m.fits.min_wall / 2)


def link(
    m: StrandbeestMaster, name: str, body: BuildPart, at: Location, supports: str = ""
) -> Printed:
    made = built(body)
    return Printed(
        name=name,
        pose=at,
        body=made,
        bed="-z",
        supports=supports,
        material=m.leg_material,
        print_settings=m.print_settings,
        connectors={OUTSIDE: Outside(made)},
    )


def crank_link(m: StrandbeestMaster, name: str, length: float, at: Location) -> Printed:
    pin, far = Location(), Location((length, 0.0, 0.0))
    with BuildPart() as made:
        web([(pin, m.pivot_radius), (far, m.pivot_radius)], m.link_thickness)
        web([(pin, m.pin_boss_radius)], m.link_thickness)
        bore(pin, m.pin_bore)
        bore(far, m.pivot_bore)
        faces_broken(m, made, m.link_thickness)
    return link(m, name, made, at)


@part
def upper_link(m: StrandbeestMaster, at: Location) -> Printed:
    return crank_link(m, UPPER_LINK, m.j * m.scale, at)


@part
def lower_link(m: StrandbeestMaster, at: Location) -> Printed:
    return crank_link(m, LOWER_LINK, m.k * m.scale, at)


@part
def rocker(m: StrandbeestMaster, at: Location) -> Printed:
    pivot, far = Location(), Location((m.c * m.scale, 0.0, 0.0))
    with BuildPart() as made:
        web([(pivot, m.tube_boss_radius), (far, m.pivot_radius)], m.link_thickness)
        bore(pivot, m.tube_bore)
        bore(far, m.pivot_bore)
        faces_broken(m, made, m.link_thickness)
    return link(m, ROCKER, made, at)


@part
def coupler(m: StrandbeestMaster, at: Location) -> Printed:
    start, far = Location(), Location((m.f * m.scale, 0.0, 0.0))
    with BuildPart() as made:
        web([(start, m.pivot_radius), (far, m.pivot_radius)], m.link_thickness)
        bore(start, m.pivot_bore)
        bore(far, m.pivot_bore)
        faces_broken(m, made, m.link_thickness)
    return link(m, COUPLER, made, at)


@part
def triangle(m: StrandbeestMaster, at: Location) -> Printed:
    pivot = Location()
    upper = Location((m.b * m.scale, 0.0, 0.0))
    outer = m.triangle_outer
    corners = [
        (pivot, m.tube_boss_radius),
        (upper, m.pivot_radius),
        (outer, m.pivot_radius),
    ]
    with BuildPart() as made:
        web(corners, m.link_thickness)
        bore(pivot, m.tube_bore)
        bore(upper, m.pivot_bore)
        bore(outer, m.pivot_bore)
        faces_broken(m, made, m.link_thickness)
    return link(m, TRIANGLE, made, at)


def nut_pocket(m: StrandbeestMaster, spot: Location) -> None:
    hexagon = Context().run(RegularPolygon, m.nut_flats / 2, SIX_SIDED, major_radius=False)
    cut_outline(hexagon, spot * Pos(Z=m.foot_thickness / 2 - m.nut_height), m.nut_height)


@part
def foot(m: StrandbeestMaster, at: Location) -> Printed:
    lower = Location()
    knee = Location((m.g * m.scale, 0.0, 0.0))
    tip = m.foot_tip
    corners = [(lower, m.foot_boss), (knee, m.foot_boss), (tip, m.pivot_radius)]
    with BuildPart() as made:
        web(corners, m.foot_thickness)
        bore(lower, m.pivot_bore)
        bore(knee, m.pivot_bore)
        nut_pocket(m, lower)
        nut_pocket(m, knee)
        faces_broken(m, made, m.foot_thickness)
    return link(m, FOOT, made, at, "under the overhangs")
