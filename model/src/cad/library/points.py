from collections.abc import Sequence

from build123d import Edge, Location, VectorLike, Wire

type Point = tuple[float, ...]


def points(path: Sequence[Location]) -> list[VectorLike]:
    return [at.position for at in path]


def point(at: Location) -> Point:
    return tuple(at.position)


def bent(path: Sequence[Location], arcs: Sequence[tuple[Point, Point, Point] | None]) -> Wire:
    edges = []
    at = path[0]
    for turn, arc in zip(path[1:-1], arcs, strict=True):
        start, middle, end = (turn, turn, turn) if arc is None else map(Location, arc)
        if at.position != start.position:
            edges.append(Edge.make_line(at.position, start.position))
        if arc is not None:
            edges.append(Edge.make_three_point_arc(start.position, middle.position, end.position))
        at = end
    if at.position != path[-1].position:
        edges.append(Edge.make_line(at.position, path[-1].position))
    return Wire(edges)
