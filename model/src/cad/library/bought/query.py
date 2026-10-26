from collections.abc import Iterable, Sequence, Sized
from dataclasses import dataclass

from build123d import Axis, Face, GeomType, Solid, VectorLike, Vertex
from OCP.BRep import BRep_Tool
from OCP.gp import gp_Lin

from cad.library.shapes import radius_of

ANGLE_TOLERANCE_DEG = 0.1
LENGTH_TOLERANCE = 0.01
LEVEL_DIGITS = 2


def exactly[S: Sized](found: S, count: int, what: str) -> S:
    if len(found) != count:
        raise ValueError(f"expected {count} {what}, found {len(found)}")
    return found


def aligned(direction: VectorLike, axis: VectorLike, signed: bool) -> bool:
    found = Axis((0, 0, 0), direction)
    wanted = Axis((0, 0, 0), axis)
    if signed:
        return found.angle_between(wanted) <= ANGLE_TOLERANCE_DEG
    return found.is_parallel(wanted, ANGLE_TOLERANCE_DEG)


def planes(shapes: Sequence[Solid], normal: VectorLike) -> list[Face]:
    return [
        f
        for shape in shapes
        for f in shape.faces()
        if f.geom_type == GeomType.PLANE and aligned(f.normal_at(), normal, signed=True)
    ]


def axis_of(face: Face) -> Axis:
    found = face.axis_of_rotation
    if found is None:
        raise ValueError(f"a {face.geom_type.name} face has no axis")
    return found


def cylinders(shapes: Sequence[Solid], axis: VectorLike) -> list[Face]:
    return [
        f
        for shape in shapes
        for f in shape.faces()
        if f.geom_type == GeomType.CYLINDER and aligned(axis_of(f).direction, axis, signed=False)
    ]


def bores(faces: Iterable[Face], narrowest: float, widest: float) -> list[Face]:
    return [
        f
        for f in faces
        if f.geom_type == GeomType.CYLINDER
        and narrowest - LENGTH_TOLERANCE <= 2 * radius_of(f) <= widest + LENGTH_TOLERANCE
    ]


@dataclass(frozen=True)
class Hole:
    axis: Axis
    faces: list[Face]

    @property
    def radius(self) -> float:
        return one_radius(self.faces)


def by_axis(faces: Sequence[Face]) -> list[Hole]:
    holes: list[Hole] = []
    for face in faces:
        matching = [hole for hole in holes if coaxial(hole.axis, face)]
        if matching:
            (hole,) = exactly(matching, 1, "holes on one axis")
            hole.faces.append(face)
        else:
            holes.append(Hole(axis=axis_of(face), faces=[face]))
    return holes


def one_radius(faces: Sequence[Face]) -> float:
    radii = [radius_of(f) for f in faces]
    exactly({round(radius, LEVEL_DIGITS) for radius in radii}, 1, "radii")
    return min(radii)


def coaxial(axis: Axis, face: Face) -> bool:
    return aligned(axis_of(face).direction, axis.direction, signed=False) and on_axis(face, axis)


def off_axis(point: VectorLike, axis: Axis) -> float:
    return gp_Lin(axis.wrapped).Distance(BRep_Tool.Pnt_s(Vertex(point).wrapped))


def on_axis(face: Face, axis: Axis = Axis.Z) -> bool:
    return off_axis(axis_of(face).position, axis) <= LENGTH_TOLERANCE
