import io
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal, cast

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Compound,
    Cylinder,
    Edge,
    Face,
    FilletPolyline,
    GeomType,
    Location,
    Mode,
    Plane,
    Pos,
    Rectangle,
    RigidJoint,
    ShapeList,
    Solid,
    Sphere,
    VectorLike,
    Vertex,
    Wire,
    extrude,
    insert,
    sweep,
)
from build123d.topology import Shape
from OCP.BinTools import BinTools, BinTools_FormatVersion
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.BRepFeat import BRepFeat_SplitShape
from OCP.TopoDS import TopoDS_Shape

from cad.library.bought.catalogue import Catalogue
from cad.library.fits import FILAMENTS, METALS, Filament, Fits, Metal
from cad.library.points import points
from cad.library.printing import PrintSettings
from cad.library.provenance import Provenance
from cad.library.why import Why
from cad.standards import Rated

type Brep = Solid | Compound
type Point = tuple[float, ...]
OUTSIDE = "outside"
ENDS = "ends"
BORE = "bore"
TEETH = "teeth"
FACES = "faces"
FACE_TOLERANCE = 0.01
MESH_ANGLE_RAD = 0.25


@dataclass(frozen=True)
class Block:
    at: Location
    width: float
    depth: float
    height: float

    @property
    def corners(self) -> list[Location]:
        near = self.at * Pos(X=self.width / 2, Y=self.depth / 2)
        ends = [near, near * Pos(Z=self.height)]
        across = [*ends, *(end.mirror(Plane(self.at * Plane.YZ.location)) for end in ends)]
        return [*across, *(end.mirror(Plane(self.at * Plane.XZ.location)) for end in across)]

    @property
    def solid(self) -> Solid:
        corner = Plane(self.at * Pos(X=-self.width / 2, Y=-self.depth / 2))
        return Solid.make_box(self.width, self.depth, self.height, plane=corner)


def brep(shape: TopoDS_Shape) -> bytes:
    stream = io.BytesIO()
    current = BinTools_FormatVersion.BinTools_FormatVersion_CURRENT
    BinTools.Write_s(shape, stream, False, False, current)
    return stream.getvalue()


def common(a: Brep, b: Brep) -> Brep:
    with BuildPart(mode=Mode.PRIVATE) as overlap:
        insert(a, clean=False)
        insert(b, clean=False, mode=Mode.INTERSECT)
    return built(overlap)


def union(a: Brep, b: Brep) -> Brep:
    total = a + b
    if isinstance(total, Wire):
        raise TypeError("solids fused into a wire")
    return total


def built(builder: BuildPart) -> Brep:
    if builder.part is None:
        raise ValueError("the builder made no solid")
    return builder.part


@dataclass(frozen=True)
class Seat:
    frame: Location
    faces: list[Face]
    instances: tuple[Seat, ...] = ()


def seat_of(faces: Sequence[Face], frame: Location) -> Seat:
    return Seat(frame=frame, faces=list(faces))


def faces_of(instances: Sequence[Seat]) -> list[Face]:
    return [face for instance in instances for face in instance.faces]


@dataclass(frozen=True, kw_only=True)
class FacesOn:
    plane: Plane
    pierced_by: tuple[Axis, ...] = ()

    @property
    def at(self) -> Location:
        return Location(self.plane)

    def found(self, shape: Brep) -> list[Face]:
        return pierced(shape, faces_on(shape, self.plane), self.pierced_by)


def pierced(shape: Brep, faces: Sequence[Face], by: Sequence[Axis]) -> list[Face]:
    if not by:
        return list(faces)
    holes = [face for face in shape.faces() if any(turns_about(face, axis) for axis in by)]
    return [face for face in faces if meeting([face], holes)]


def radius_of(face: Face) -> float:
    surface = BRepAdaptor_Surface(face.wrapped)
    match face.geom_type:
        case GeomType.CYLINDER:
            return surface.Cylinder().Radius()
        case GeomType.SPHERE:
            return surface.Sphere().Radius()
    raise ValueError(f"a {face.geom_type.name} face has no radius")


def turns_about(face: Face, axis: Axis) -> bool:
    turning = face.axis_of_rotation
    return turning is not None and any(
        turning.is_coaxial(each, linear_tolerance=FACE_TOLERANCE) for each in (axis, -axis)
    )


@dataclass(frozen=True, kw_only=True)
class RoundFaces:
    axis: Axis
    radius: float
    length: float | None = None
    kind: GeomType = GeomType.CYLINDER
    pierced_by: tuple[Axis, ...] = ()
    split_at: Plane | None = None

    @property
    def at(self) -> Location:
        return self.axis.location

    def found(self, shape: Brep) -> list[Face]:
        rounds = shape.faces().filter_by(self.kind).filter_by(self.on_the_axis)
        if self.length is not None:
            ends = (0.0, self.length)
            rounds = rounds.filter_by_position(
                self.axis, min(ends) - FACE_TOLERANCE, max(ends) + FACE_TOLERANCE
            )
        return pierced(shape, rounds, self.pierced_by)

    def on_the_axis(self, face: Face) -> bool:
        return turns_about(face, self.axis) and abs(radius_of(face) - self.radius) <= FACE_TOLERANCE


@dataclass(frozen=True, kw_only=True)
class SurfaceFaces:
    kind: GeomType

    @property
    def at(self) -> Location:
        return Location()

    def found(self, shape: Brep) -> list[Face]:
        return list(shape.faces().filter_by(self.kind))


type FaceQuery = FacesOn | RoundFaces | SurfaceFaces


@dataclass(frozen=True, kw_only=True)
class SeatQuery:
    frame: Location
    faces: Sequence[FaceQuery]


def unique[T](items: Sequence[T]) -> list[T]:
    found: list[T] = []
    for item in items:
        if item not in found:
            found.append(item)
    return found


def queried(shape: Brep, queries: Sequence[FaceQuery], where: str) -> list[Face]:
    found: list[Face] = []
    for query in queries:
        faces = query.found(shape)
        if not faces:
            raise ValueError(f"{where} finds no face for {query}")
        found += faces
    return unique(found)


class SeatJoint(RigidJoint):
    def __init__(
        self,
        name: str,
        frame: Location,
        faces: list[FaceQuery],
        instances: list[SeatQuery],
    ) -> None:
        if name in registered():
            raise ValueError(f"the {name} connector is registered twice")
        super().__init__(name, joint_location=frame)
        self.frame = frame
        self.faces = faces
        self.instances = instances

    def seat(self, shape: Brep, part: str) -> Seat:
        where = f"the {self.label} connector on {part}"
        instances = tuple(
            Seat(frame=each.frame, faces=queried(shape, each.faces, where))
            for each in self.instances
        )
        own = queried(shape, self.faces, where)
        return Seat(
            frame=self.frame, faces=unique([*own, *faces_of(instances)]), instances=instances
        )


def registered() -> dict[str, SeatJoint]:
    builder = BuildPart._get_context()
    if builder is None:
        raise ValueError("a connector is registered while its part is built")
    return cast(dict[str, SeatJoint], builder.joints)


def register(name: str, at: Location | Plane, faces: Sequence[FaceQuery]) -> None:
    SeatJoint(name, Location(at), list(faces), [])


def register_each(
    name: str,
    at: Location | Plane,
    instances: Sequence[SeatQuery],
    faces: Sequence[FaceQuery] = (),
) -> None:
    SeatJoint(name, Location(at), list(faces), list(instances))


def connectors_of(shape: Brep) -> dict[str, SeatJoint]:
    return cast(dict[str, SeatJoint], shape.joints)


def split_lines(shape: Brep) -> Brep:
    lines = unique(
        [
            (RoundFaces(axis=query.axis, radius=query.radius, kind=query.kind), query.split_at)
            for joint in connectors_of(shape).values()
            for query in [*joint.faces, *(q for each in joint.instances for q in each.faces)]
            if isinstance(query, RoundFaces) and query.split_at is not None
        ]
    )
    if not lines:
        return shape
    splitter = BRepFeat_SplitShape(shape.wrapped)
    for rounds, plane in lines:
        for face in rounds.found(shape):
            section = BRepAlgoAPI_Section(face.wrapped, plane.wrapped, False)
            section.ComputePCurveOn1(True)
            section.Build()
            for edge in Shape.cast(section.Shape()).edges():
                splitter.Add(edge.wrapped, face.wrapped)
    splitter.Build()
    split = cast(Brep, Shape.cast(splitter.Shape()))
    split.joints = shape.joints
    return split


def instances_in(builder: BuildPart, name: str) -> list[SeatQuery]:
    return cast(SeatJoint, builder.joints[name]).instances


def register_more(
    name: str, faces: Sequence[FaceQuery] = (), instances: Sequence[SeatQuery] = ()
) -> None:
    joint = registered()[name]
    joint.faces += faces
    joint.instances += instances


def clamp_face(connector: str) -> str:
    return f"{connector} clamp face"


def horn_name(servo: str) -> str:
    return f"{servo} horn"


def on_the_horn_face(face: Plane, horn_face: Plane) -> Location:
    return Location(face) * Location(horn_face).inverse()


def faces_on(shape: Brep, plane: Plane) -> list[Face]:
    normal = Axis(plane.location)
    on = shape.faces().filter_by(plane).filter_by_position(normal, -FACE_TOLERANCE, FACE_TOLERANCE)
    return list(on)


def standing_on(shape: Brep, plane: Plane) -> list[Face]:
    normal = Axis(plane.location)

    def above(face: Face) -> bool:
        corners = face.vertices()
        return len(corners.filter_by_position(normal, -FACE_TOLERANCE, float("inf"))) == len(
            corners
        ) and bool(face.edges().filter_by_position(normal, FACE_TOLERANCE, float("inf")))

    return [face for face in shape.faces() if above(face)]


def edges_on(shape: Brep, plane: Plane) -> list[Edge]:
    normal = Axis(plane.location)

    def lying(edge: Edge) -> bool:
        pieces: ShapeList[Edge | Vertex] = ShapeList([edge, *edge.vertices()])
        on = pieces.filter_by_position(normal, -FACE_TOLERANCE, FACE_TOLERANCE)
        return len(on) == len(pieces)

    return [edge for edge in shape.edges() if lying(edge)]


def flat_faces(shape: Brep, level: float) -> list[Face]:
    return faces_on(shape, Plane.XY.offset(level))


def round_faces(shape: Brep, radius: float, kind: GeomType = GeomType.CYLINDER) -> list[Face]:
    rounds = shape.faces().filter_by(kind)
    return [face for face in rounds if abs(radius_of(face) - radius) <= FACE_TOLERANCE]


def meeting(first: Sequence[Face], second: Sequence[Face]) -> list[Edge]:
    edges = [edge for face in first for edge in face.edges()]
    return [edge for edge in edges if any(edge in face.edges() for face in second)]


def round_faces_below(shape: Brep, level: float) -> list[Face]:
    cylinders = shape.faces().filter_by(GeomType.CYLINDER)
    return list(cylinders.filter_by_position(Axis.Z, -float("inf"), level))


@dataclass(kw_only=True)
class Part:
    name: str
    group: str = ""
    pose: Location
    material: str = "PETG white"
    exterior: bool = False
    bed: Bed | None = None
    print_settings: PrintSettings | None = None
    ships_with: str = ""
    connectors: dict[str, Seat] = field(default_factory=dict, compare=False)
    _unposed: Brep | None = field(default=None, init=False, repr=False, compare=False)
    _solid: Brep | None = field(default=None, init=False, repr=False, compare=False)
    _published: dict[str, Seat] | None = field(default=None, init=False, repr=False, compare=False)

    def __getstate__(self) -> dict[str, object]:
        return {**vars(self), "_unposed": None, "_solid": None, "_published": None}

    def solid(self) -> Brep:
        if self._solid is None:
            self._solid = self.build()
        return self._solid

    def build(self) -> Brep:
        return self.pose * self.unposed()

    def unposed(self) -> Brep:
        if self._unposed is None:
            self._unposed = self.shape()
        return self._unposed

    def published(self) -> dict[str, Seat]:
        return self.connectors

    def connector(self, name: str) -> Seat:
        if self._published is None:
            self._published = self.published()
        found = self._published
        if name not in found:
            raise ValueError(f"{self.name} publishes no {name} connector")
        return found[name]

    def shape(self) -> Brep:
        raise NotImplementedError

    @property
    def label(self) -> str:
        raise NotImplementedError

    @property
    def filament(self) -> Filament | None:
        plastic, _, _ = self.material.partition(" ")
        return FILAMENTS.get(plastic)

    @property
    def printed(self) -> bool:
        return self.filament is not None

    @property
    def metal(self) -> Metal | None:
        return None if self.printed else METALS.get(self.material)

    @property
    def grams(self) -> float | None:
        return None

    @property
    def catalogue(self) -> Catalogue | None:
        return None

    def rating(self, fits: Fits) -> Rated | None:
        return None if self.catalogue is None else self.catalogue.rating

    @property
    def mesh_angle(self) -> float:
        return MESH_ANGLE_RAD


@dataclass(kw_only=True)
class Shaped(Part):
    body: Brep
    provenance: Provenance | None = None
    source: str = ""

    def __post_init__(self) -> None:
        self.body = split_lines(self.body)
        joints = connectors_of(self.body)
        if twice := [name for name in self.connectors if name in joints]:
            raise ValueError(f"{self.name} registers and lists {', '.join(twice)}")
        seats = {name: joint.seat(self.body, self.name) for name, joint in joints.items()}
        self.connectors = {**seats, **self.connectors}

    def shape(self) -> Brep:
        return self.body


type Bed = Literal["+x", "-x", "+y", "-y", "+z", "-z"] | Point

ONTO_THE_BED: dict[str, Axis] = {
    "+x": Axis.X,
    "-x": -Axis.X,
    "+y": Axis.Y,
    "-y": -Axis.Y,
    "+z": Axis.Z,
    "-z": -Axis.Z,
}


def prints_up(bed: Bed) -> Axis:
    onto_the_bed = ONTO_THE_BED[bed] if isinstance(bed, str) else Axis((0, 0, 0), bed)
    return -onto_the_bed


@dataclass(kw_only=True)
class Printed(Shaped):
    bed: Bed
    supports: str = ""
    print_why: Why | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if len(pieces := self.body.solids()) > 1:
            listed = ", ".join(f"{piece.volume:.0f} mm³" for piece in pieces)
            raise ValueError(f"{self.name} is {len(pieces)} disconnected pieces: {listed}")


@dataclass(kw_only=True)
class Tube(Part):
    outside_radius: float
    inside_radius: float = 0.0
    bottom: float
    top: float

    def shape(self) -> Brep:
        with BuildPart() as tube:
            with BuildSketch(Plane.XY.offset(self.bottom)):
                Circle(self.outside_radius)
                if self.inside_radius > 0:
                    Circle(self.inside_radius, mode=Mode.SUBTRACT)
            extrude(amount=self.top - self.bottom)
        return built(tube)


@dataclass(kw_only=True)
class Rod(Part):
    length: float
    radius: float
    wall: float = 0.0

    @classmethod
    def between(
        cls,
        *,
        name: str,
        start: VectorLike,
        end: VectorLike,
        radius: float,
        wall: float = 0.0,
    ) -> Rod:
        centreline = Edge.make_line(start, end)
        return cls(
            name=name,
            pose=Location(Plane(Axis(start, end_point=end))),
            length=centreline.length,
            radius=radius,
            wall=wall,
        )

    def shape(self) -> Brep:
        body = self._capsule(self.radius)
        if self.wall > 0:
            body = body - self._capsule(self.radius - self.wall)
        return body

    def _capsule(self, radius: float) -> Brep:
        body = Cylinder(radius, self.length, align=(Align.CENTER, Align.CENTER, Align.MIN))
        return union(union(body, Sphere(radius)), Pos(Z=self.length) * Sphere(radius))


@dataclass(frozen=True)
class FlatSection:
    width: float
    thickness: float
    bend: float


def flat_run(path: tuple[Location, ...], across: VectorLike, section: FlatSection) -> Solid:
    route = FilletPolyline(*points(path), radius=section.bend)
    start = Plane(axis=Axis(route.location_at(0)), x_dir=across)
    profile = Rectangle(section.width, section.thickness)
    return sweep(profile.moved(start.location), path=route).solid()


@dataclass(kw_only=True)
class FlatCable(Part):
    path: tuple[Location, ...]
    width_along_x_of: Location
    section: FlatSection
    item: Catalogue
    material: str = "cable"

    @property
    def label(self) -> str:
        return self.name

    @property
    def catalogue(self) -> Catalogue:
        return self.item

    @property
    def length(self) -> float:
        return FilletPolyline(*points(self.path), radius=self.section.bend).length

    def published(self) -> dict[str, Seat]:
        return {OUTSIDE: seat_of(self.unposed().faces(), Location())}

    def shape(self) -> Brep:
        return flat_run(self.path, Plane(self.width_along_x_of).x_dir, self.section)
