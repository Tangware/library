from collections.abc import Sequence
from contextvars import Context

from build123d import (
    Circle,
    Edge,
    Hole,
    Location,
    Locations,
    Mode,
    Plane,
    Pos,
    Rectangle,
    Sketch,
    extrude,
    make_hull,
)

MATERIAL = "PETG white"
THROUGH = 400.0


def web(spots: Sequence[tuple[Location, float]], thickness: float, middle: float = 0.0) -> None:
    edges = [Edge.make_circle(radius, Plane(at)) for at, radius in spots]
    outline = Context().run(make_hull, edges)
    extrude(Pos(Z=middle - thickness / 2) * outline, amount=thickness)


def web_at(frame: Location, spots: Sequence[tuple[Location, float]], thickness: float) -> None:
    edges = [Edge.make_circle(radius, Plane(at)) for at, radius in spots]
    outline = Context().run(make_hull, edges)
    extrude(frame * Pos(Z=-thickness / 2) * outline, amount=thickness)


def cut_outline(outline: Sketch, at: Location, depth: float) -> None:
    extrude(at * outline, amount=depth, mode=Mode.SUBTRACT)


def bore(at: Location, diameter: float) -> None:
    with Locations(at * Pos(Z=THROUGH / 2)):
        Hole(diameter / 2, THROUGH)


def d_bore(radius: float, flat: float) -> Sketch:
    block = Pos(Y=flat - 2 * radius) * Context().run(Rectangle, 2 * radius, 2 * radius)
    return Context().run(Circle, radius) - block
