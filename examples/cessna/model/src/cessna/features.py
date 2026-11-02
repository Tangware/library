from collections.abc import Sequence
from contextvars import Context

from build123d import (
    BuildPart,
    Hole,
    Location,
    Locations,
    Mode,
    Plane,
    Polygon,
    Pos,
    Sketch,
    chamfer,
    extrude,
)
from cad.library.shapes import built, edges_on

THROUGH = 400.0


def cut_outline(outline: Sketch, at: Location, depth: float) -> None:
    extrude(at * outline, amount=depth, mode=Mode.SUBTRACT)


def bore(at: Location, diameter: float) -> None:
    with Locations(at * Pos(Z=THROUGH / 2)):
        Hole(diameter / 2, THROUGH)


def outline(points: Sequence[tuple[float, float]]) -> Sketch:
    return Context().run(Polygon, *points, align=None)


def break_edges(made: BuildPart, faces: Sequence[Plane], size: float) -> None:
    chamfer([edge for face in faces for edge in edges_on(built(made), face)], size)
