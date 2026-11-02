from collections.abc import Sequence
from contextvars import Context

from build123d import Hole, Location, Locations, Mode, Polygon, Pos, Sketch, extrude

MATERIAL = "PETG white"
THROUGH = 400.0


def cut_outline(outline: Sketch, at: Location, depth: float) -> None:
    extrude(at * outline, amount=depth, mode=Mode.SUBTRACT)


def bore(at: Location, diameter: float) -> None:
    with Locations(at * Pos(Z=THROUGH / 2)):
        Hole(diameter / 2, THROUGH)


def outline(points: Sequence[tuple[float, float]]) -> Sketch:
    return Context().run(Polygon, *points, align=None)
