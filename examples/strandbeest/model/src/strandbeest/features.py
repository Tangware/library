from collections.abc import Sequence
from contextvars import Context

from build123d import (
    Edge,
    Hole,
    Location,
    Locations,
    Mode,
    Plane,
    Pos,
    Sketch,
    extrude,
    make_hull,
)

MATERIAL = "PETG white"
THROUGH = 200.0


def web(spots: Sequence[tuple[Location, float]], thickness: float, middle: float = 0.0) -> None:
    edges = [Edge.make_circle(radius, Plane(at)) for at, radius in spots]
    outline = Context().run(make_hull, edges)
    extrude(Pos(Z=middle - thickness / 2) * outline, amount=thickness)


def cut_outline(outline: Sketch, at: Location, depth: float) -> None:
    extrude(at * outline, amount=depth, mode=Mode.SUBTRACT)


def bore(at: Location, diameter: float) -> None:
    with Locations(at * Pos(Z=THROUGH / 2)):
        Hole(diameter / 2, THROUGH)
