from collections.abc import Sequence

from build123d import (
    Axis,
    Compound,
    Edge,
    Face,
    Location,
    Plane,
    Pos,
    Rotation,
    Shell,
    VectorLike,
    Wire,
)

from cad.library.bought.catalogue import Catalogue
from cad.library.bought.vendor import vendor_block
from cad.library.shapes import Block


def _located(at: Location) -> Location:
    if not isinstance(at, Location):
        raise TypeError(
            f"a {type(at).__name__} is not a Location; a shape's position is its origin"
        )
    return at


def between(start: Plane, end: Plane) -> float:
    return float(start.to_local_coords(end.origin).Z)


def first_of(start: Plane, planes: Sequence[Plane]) -> Plane:
    return min(planes, key=lambda plane: between(start, plane))


def last_of(start: Plane, planes: Sequence[Plane]) -> Plane:
    return max(planes, key=lambda plane: between(start, plane))


def halfway(start: Plane, end: Plane) -> Plane:
    return start.offset(between(start, end) / 2)


def parallel(plane: Plane, through: Location) -> Plane:
    return Plane(origin=_located(through).position, x_dir=plane.x_dir, z_dir=plane.z_dir)


def farthest(toward: Plane, points: Sequence[Location]) -> Plane:
    return last_of(toward, [parallel(toward, through=point) for point in points])


def normal_to(direction: VectorLike, through: Location, x_dir: VectorLike | None = None) -> Plane:
    return Plane(origin=_located(through).position, x_dir=x_dir, z_dir=direction)


def axis_along(direction: VectorLike, through: Location) -> Axis:
    return Axis(_located(through).position, direction)


def line_between(start: Location, end: Location) -> Edge:
    return Edge.make_line(_located(start).position, _located(end).position)


def arc_through(start: Location, middle: Location, end: Location) -> Edge:
    return Edge.make_three_point_arc(
        _located(start).position, _located(middle).position, _located(end).position
    )


def line_through(start: Location, end: Location) -> Axis:
    return Axis(_located(start).position, end_point=_located(end).position)


def polygon(corners: Sequence[Location]) -> Face:
    return Face(Wire.make_polygon([_located(corner).position for corner in corners], close=True))


def plane_through(first: Location, second: Location, third: Location) -> Plane:
    return Plane([_located(point).position for point in (first, second, third)])


def foot_on(level: Plane, of: Location) -> Location:
    return Location(level.shift_origin(Axis(_located(of).position, level.z_dir)))


def station(along: Plane, through: Location) -> Plane:
    return parallel(along, through=through).shift_origin(Axis(along.origin, along.z_dir))


def crossing(on: Plane | Axis, line: Axis) -> Location:
    point = on & line
    if point is None or isinstance(point, Axis | Plane):
        raise ValueError("the line does not cross it at one point")
    return Pos(point)


def crossings(shape: Edge | Compound, by: Edge | Shell | Plane | Axis) -> list[Location]:
    found = shape & by
    if found is None or not found.vertices():
        raise ValueError("nothing meets the shape")
    return [Pos(point.center()) for point in found.vertices()]


def chord_end(frame: Location, radius: float, beside: float) -> Location:
    round_about = Edge.make_circle(radius, Plane(frame))
    chord = parallel(Plane(frame * Plane.XZ.location), through=frame * Pos(Y=beside))
    end = farthest(Plane(frame * Plane.YZ.location), crossings(round_about, chord))
    return Location(parallel(Plane(frame), through=Location(end)))


def tangent_points(point: Location, circle: Edge) -> list[Location]:
    flat = Location(Plane(origin=circle.arc_center, z_dir=circle.normal()))
    seen = flat.inverse() * _located(point)
    lines = Edge.make_constrained_lines(flat.inverse() * circle, seen.position)
    return [flat * Pos(line @ 0) for line in lines]


def outline_on(surface: Face, on: Plane) -> Edge:
    found = surface & on
    if not isinstance(found, Edge):
        raise ValueError("the plane does not cut the surface in one curve")
    return found


def common_tangents(on: Plane, first: Edge, second: Edge) -> list[Axis]:
    flat = Location(on)
    lines = Edge.make_constrained_lines(flat.inverse() * first, flat.inverse() * second)
    return [Axis(flat * line) for line in lines]


def tangent(corner: Location, swing: Edge, along: Plane) -> Axis:
    touching = farthest(along, tangent_points(corner, swing))
    return line_through(corner, Location(touching))


def either_side(middle: Plane, half_width: float) -> tuple[Plane, Plane]:
    return middle.offset(half_width), (-middle).offset(half_width)


def reach(blocks: Sequence[Block], toward: Plane) -> Plane:
    return farthest(toward, [corner for block in blocks for corner in block.corners])


def flush_to(nearest: Plane, against: Plane) -> Location:
    return Pos(against.z_dir * between(-against, nearest))


def flush(blocks: Sequence[Block], against: Plane) -> Location:
    return flush_to(reach(blocks, toward=-against), against)


def through_the_middle(blocks: Sequence[Block], along: Plane) -> Axis:
    middles = [
        halfway(reach(blocks, toward=-side), reach(blocks, toward=side))
        for side in (
            normal_to(along.x_dir, through=along.location),
            normal_to(along.y_dir, through=along.location),
        )
    ]
    return axis_along(along.z_dir, through=corner(along, *middles))


def box_reach(item: Catalogue, at: Location, toward: Plane) -> Plane:
    return reach([vendor_block(item, at)], toward)


def box_flush(item: Catalogue, at: Location, against: Plane) -> Location:
    return flush([vendor_block(item, at)], against)


def corner(on: Plane, first: Plane, second: Plane) -> Location:
    line = first & second
    if not isinstance(line, Axis):
        raise ValueError("the planes do not meet in a line")
    return crossing(on, line)


def outline(on: Plane, sides: list[tuple[Plane, Plane]]) -> Face:
    return polygon([corner(on, *side) for side in sides])


def radial_at(level: Plane, angle: float) -> Plane:
    return Plane(Location(level) * Rotation(0, 0, angle) * Plane.XZ.location)


def turned_about(spot: Location, axis: Axis, turn: float) -> Location:
    pivot = axis.location
    return pivot * Rotation(0, 0, turn) * pivot.inverse() * spot
