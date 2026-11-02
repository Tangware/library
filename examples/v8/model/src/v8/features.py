from collections.abc import Sequence
from contextvars import Context

from build123d import (
    BuildPart,
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
    chamfer,
    extrude,
    make_hull,
)
from cad.library.shapes import built, edges_on

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


def d_shape(radius: float, flat: float) -> Sketch:
    void = Pos(Y=flat - radius - radius) * Context().run(Rectangle, 2 * radius, 2 * radius)
    return Context().run(Circle, radius) - void


def break_edges(made: BuildPart, faces: Sequence[Plane], size: float) -> None:
    chamfer([edge for face in faces for edge in edges_on(built(made), face)], size)
