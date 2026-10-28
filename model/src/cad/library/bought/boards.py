from dataclasses import dataclass, replace
from functools import cache

from build123d import (
    Axis,
    BoundBox,
    Compound,
    Face,
    GeomType,
    Location,
    Locations,
    Plane,
    Pos,
    Solid,
    Vertex,
)

from cad.library.bought.catalogue import Catalogue
from cad.library.bought.connectors import board_ports
from cad.library.bought.query import (
    LENGTH_TOLERANCE,
    Hole,
    axis_of,
    bores,
    by_axis,
    cylinders,
    exactly,
    off_axis,
)
from cad.library.bought.vendor import solids_of, vendor_box
from cad.library.derived import derived
from cad.library.shapes import Seat, clamp_face, flat_faces, seat_of
from cad.library.standard.fasteners import Metric, passing_range
from cad.library.turns import UPSIDE_DOWN

MOUNTING_HOLES = "mounting holes"


def mounting_hole_seats(holes: MountingHoles) -> dict[str, Seat]:
    return {
        MOUNTING_HOLES: seat_of(holes.bores, Location()),
        clamp_face(MOUNTING_HOLES): seat_of([*holes.faces, *holes.bores], Location()),
    }


def board_connectors(item: Catalogue, holes: MountingHoles) -> dict[str, Seat]:
    return {**mounting_hole_seats(holes), **board_ports(item)}


@dataclass(frozen=True)
class MountingHoles:
    spots: list[Location]
    board_bottom: float
    board_top: float
    edges: list[Location]
    bores: list[Face]
    faces: list[Face]


@derived
def mounting_holes(item: Catalogue, narrowest: float, widest: float, count: int) -> MountingHoles:
    return holes_in(solids_of(item), narrowest, widest, count)


def holes_in(solids: list[Solid], narrowest: float, widest: float, count: int) -> MountingHoles:
    holes = by_axis(bores(cylinders(solids, Axis.Z.direction), narrowest, widest))
    middle = Axis(Compound(solids).bounding_box().center(), Axis.Z.direction)

    def centre(hole: Hole) -> Axis:
        return Axis(hole.axis.position, Axis.Z.direction)

    def reach(hole: Hole) -> float:
        return off_axis(centre(hole).position, middle)

    def farther_out(hole: Hole) -> int:
        return sum(reach(other) > reach(hole) + LENGTH_TOLERANCE for other in holes)

    outermost = exactly(
        [hole for hole in holes if farther_out(hole) < count],
        count,
        f"outermost Ø{narrowest:g}-{widest:g} holes",
    )
    chamfers = [f for s in solids for f in s.faces() if f.geom_type == GeomType.CONE]
    hole_faces = [
        face
        for hole in outermost
        for face in [
            *hole.faces,
            *(
                c
                for c in chamfers
                if off_axis(axis_of(c).position, centre(hole)) <= LENGTH_TOLERANCE
            ),
        ]
    ]
    board = Compound(hole_faces).bounding_box()
    points = sorted((centre(hole).position for hole in outermost), key=lambda p: (p.X, p.Y))
    circuit = Compound([s for s in solids if any(f in s.faces() for f in hole_faces)])
    pcb = circuit.bounding_box()
    pcb_middle = Pos(pcb.center())
    corner = Pos(X=pcb.max.X, Y=pcb.max.Y)
    pair = [corner, corner.mirror(Plane(pcb_middle * Plane.XZ.location))]
    across = Plane(pcb_middle * Plane.YZ.location)
    return MountingHoles(
        spots=[Pos(X=point.X, Y=point.Y) for point in points],
        board_bottom=board.min.Z,
        board_top=board.max.Z,
        edges=[*pair, *(end.mirror(across) for end in pair)],
        bores=hole_faces,
        faces=[*flat_faces(circuit, board.min.Z), *flat_faces(circuit, board.max.Z)],
    )


@dataclass(frozen=True)
class CornerHoles:
    left: Plane
    right: Plane
    front: Plane
    back: Plane


@dataclass(frozen=True)
class BoardMount:
    item: Catalogue
    spots: list[Location]
    screw: Metric
    board_bottom: float
    board_top: float
    parts_below: float
    parts_above: float
    middle: Location
    length: float
    width: float
    edges: list[Location]

    @property
    def holes(self) -> MountingHoles:
        return board_holes_of(self.item, self.screw, len(self.spots))

    @property
    def corner_holes(self) -> CornerHoles:
        pattern = Compound([Vertex(spot.position) for spot in self.spots]).bounding_box()

        low, high = Pos(pattern.min), Pos(pattern.max)

        def through(side: Plane, corner: Location) -> Plane:
            return Plane(origin=corner.position, x_dir=side.x_dir, z_dir=side.z_dir)

        return CornerHoles(
            left=through(-Plane.YZ, low),
            right=through(Plane.YZ, high),
            front=through(Plane.XZ, low),
            back=through(-Plane.XZ, high),
        )

    @property
    def board_thickness(self) -> float:
        return self.board_top - self.board_bottom

    @property
    def face_down(self) -> BoardMount:
        return replace(
            self,
            spots=[UPSIDE_DOWN * spot * UPSIDE_DOWN for spot in self.spots],
            board_bottom=-self.board_top,
            board_top=-self.board_bottom,
            parts_below=self.parts_above,
            parts_above=self.parts_below,
            middle=UPSIDE_DOWN * self.middle * UPSIDE_DOWN,
            edges=[UPSIDE_DOWN * edge * UPSIDE_DOWN for edge in self.edges],
        )

    @property
    def outline(self) -> BoundBox:
        return Compound([Vertex(edge.position) for edge in self.edges]).bounding_box()

    def standing(self, on: Location, height: float) -> Location:
        return on * Pos(Z=height - self.board_bottom)

    def underside(self, board: Location) -> list[Location]:
        with Locations(board * Pos(Z=self.board_bottom)), Locations(*self.spots):
            return Locations(UPSIDE_DOWN).locations

    def topside(self, board: Location) -> list[Location]:
        with Locations(board * Pos(Z=self.board_top)):
            return Locations(*self.spots).locations


@cache
def board_mount(item: Catalogue, screw: Metric, holes: int) -> BoardMount:
    return mount_on(item, screw, board_holes_of(item, screw, holes))


def board_holes_of(item: Catalogue, screw: Metric, holes: int) -> MountingHoles:
    return mounting_holes(item, *passing_range(screw), holes)


def mount_on(item: Catalogue, screw: Metric, found: MountingHoles) -> BoardMount:
    box = vendor_box(item).bounding_box()
    return BoardMount(
        item=item,
        spots=found.spots,
        screw=screw,
        board_bottom=found.board_bottom,
        board_top=found.board_top,
        parts_below=found.board_bottom - box.min.Z,
        parts_above=box.max.Z - found.board_top,
        middle=Pos(X=box.center().X, Y=box.center().Y),
        length=box.size.X,
        width=box.size.Y,
        edges=found.edges,
    )
