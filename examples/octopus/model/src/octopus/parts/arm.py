from contextvars import Context

from build123d import Align, BuildPart, Circle, Cylinder, Location, Locations, Pos, Rectangle, Rot
from cad.design.parts import part
from cad.library.shapes import OUTSIDE, Outside, Printed, built

from octopus.features import MATERIAL, bore, cut_outline, web
from octopus.master import (
    MOTOR_SHAFT,
    MOTOR_SHAFT_DIAMETER,
    MOTOR_SHAFT_FLAT,
    OctopusMaster,
)

CRANK = "crank"
UP_FROM = (Align.CENTER, Align.CENTER, Align.MIN)
DOWN_FROM = (Align.CENTER, Align.CENTER, Align.MAX)
UP = 1.0
DOWN = -1.0
EVEN = (2, 4)


def segment_name(arm: int, k: int) -> str:
    return f"arm {arm + 1} segment {k}"


def rod_name(arm: int, k: int) -> str:
    return f"arm {arm + 1} rod {k}"


def drive_rod_name(arm: int) -> str:
    return f"arm {arm + 1} drive rod"


def crank_name(arm: int) -> str:
    return f"arm {arm + 1} crank"


def printed(m: OctopusMaster, name: str, made: BuildPart, pose: Location) -> Printed:
    body_part = built(made)
    return Printed(
        name=name,
        pose=pose,
        body=body_part,
        bed="-z",
        material=MATERIAL,
        print_settings=m.print_settings,
        connectors={OUTSIDE: Outside(body_part)},
    )


def stub(m: OctopusMaster, at: Location, sign: float, length: float | None = None) -> None:
    reach = m.layer if length is None else length
    with Locations(at * Pos(Z=sign * m.thin / 2)):
        Cylinder(m.pin_diameter / 2, reach, align=UP_FROM if sign > 0 else DOWN_FROM)


@part
def segment(m: OctopusMaster, arm: int, k: int) -> Printed:
    frame = m.segment_frame(arm, k)
    length = m.lengths[k - 1]
    tip = Pos(X=length)
    root_up = Pos(Y=m.low_offset)
    tip_up = Pos(X=length, Y=-m.offset)
    lever = Pos(X=m.lever_out(arm), Y=-m.lever_up(arm))
    spots = [
        (Location(), m.drum_at(k)),
        (tip, m.drum_at(k + 1)),
    ]
    if k < 4:
        spots.append((tip_up, m.eye))
    if k > 1:
        spots.append((root_up, m.eye))
    if k == 1:
        spots.append((lever, m.eye))
    even = k in EVEN
    with BuildPart() as made:
        web(spots, m.thin)
        with Locations(Pos(X=length / 2, Y=m.drum_at(k + 1) - m.sucker_radius) * Rot(X=-90.0)):
            Cylinder(m.sucker_radius, 2 * m.sucker_radius, align=UP_FROM)
        for at in (Location(), tip):
            if at is tip and k == 4:
                continue
            if even:
                stub(m, at, UP)
            else:
                bore(at, m.stub_hole)
        for at in [*([tip_up] if k < 4 else []), *([root_up] if k > 1 else [])]:
            bore(at, m.stub_hole)
        if k == 1:
            bore(lever, m.stub_hole)
    return printed(m, segment_name(arm, k), made, frame)


@part
def rod(m: OctopusMaster, arm: int, k: int) -> Printed:
    frame = m.rod_frame(arm, k)
    end = Pos(X=m.rod_length(k))
    sign = DOWN if k in EVEN else UP
    with BuildPart() as made:
        web([(Location(), m.eye), (end, m.eye)], m.thin)
        stub(m, Location(), sign)
        stub(m, end, sign)
    return printed(m, rod_name(arm, k), made, frame)


@part
def drive_rod(m: OctopusMaster, arm: int) -> Printed:
    frame = m.drive_rod_frame(arm)
    end = Pos(X=m.drive_rod_length(arm))
    with BuildPart() as made:
        web([(Location(), m.eye), (end, m.eye)], m.thin)
        stub(m, end, DOWN, 2 * m.layer)
        bore(Location(), m.stub_hole)
    return printed(m, drive_rod_name(arm), made, frame)


@part
def crank(m: OctopusMaster, arm: int) -> Printed:
    frame = m.motor_axis(arm)
    pin = Rot(Z=m.crank_lean_deg) * Pos(Y=-m.crank_throw)
    with BuildPart() as made:
        web([(Location(), m.eye + m.fits.structural_wall), (pin, m.eye)], m.thin)
        stub(m, pin, UP)
        radius = m.fits.printed(MOTOR_SHAFT_DIAMETER) / 2
        flat = Pos(Y=MOTOR_SHAFT_FLAT - MOTOR_SHAFT_DIAMETER)
        d_shape = Context().run(Circle, radius) - flat * Context().run(
            Rectangle, MOTOR_SHAFT_DIAMETER, MOTOR_SHAFT_DIAMETER
        )
        cut_outline(d_shape, Pos(Z=m.thin / 2 - MOTOR_SHAFT) * Rot(Z=90.0), MOTOR_SHAFT)
    return printed(m, crank_name(arm), made, frame)
