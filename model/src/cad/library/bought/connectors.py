from build123d import (
    Axis,
    CenterOf,
    Compound,
    GridLocations,
    Location,
    Locations,
    Plane,
    Pos,
)

from cad.library.bought.catalogue import Catalogue, Pins, PlugFace, Port
from cad.library.bought.query import (
    LENGTH_TOLERANCE,
    LEVEL_DIGITS,
    Hole,
    bores,
    by_axis,
    cylinders,
    exactly,
    planes,
)
from cad.library.bought.vendor import named_solids, solids_of, vendor_reach, vendor_shape
from cad.library.cache import cached
from cad.library.shapes import Seat, faces_on, seat_of

HEADER_PITCH = 2.54
PLUG_FACE = "plug face"
CABLE_EXIT = "cable exit"


def facing(mating: Axis, across: Axis) -> Plane:
    return Plane(origin=(0, 0, 0), x_dir=across.direction, z_dir=mating.direction)


def of_the_instance(name: str, instance: str) -> bool:
    return instance in name.split("/")


@cached
def port_seats(item: Catalogue, port: Port) -> dict[str, Seat]:
    frame = facing(port.mating, port.across)
    found = [solid for solid, name in named_solids(item) if of_the_instance(name, port.instance)]
    if not found:
        raise ValueError(f"{item.file} has no {port.instance}")
    facing_out = planes(found, port.mating.direction)
    if not facing_out:
        raise ValueError(f"{port.instance} of {item.file} has no face facing out")
    out = port.mating.direction
    reach = max(face.center().dot(out) for face in facing_out)
    front = Compound(
        [
            frame.location.inverse() * face
            for face in facing_out
            if abs(face.center().dot(out) - reach) <= LENGTH_TOLERANCE
        ]
    ).bounding_box()
    faces = [face for solid in found for face in solid.faces()]
    levels = port.levels or (port.name,)
    with Locations(frame.location * Pos(X=front.center().X, Y=front.center().Y, Z=front.max.Z)):
        mouths = GridLocations(0, front.size.Y / len(levels), 1, len(levels)).locations
    names = [f"{port.name}, {level}" for level in port.levels] or [port.name]
    return {name: seat_of(faces, mouth) for name, mouth in zip(names, mouths, strict=True)}


@cached
def pin_seats(item: Catalogue, pins: Pins) -> dict[str, Seat]:
    count = len(pins.lines[0])
    across = Plane(origin=(0, 0, 0), x_dir=pins.along.direction, z_dir=(0, 0, 1)).y_dir
    holes = by_axis(
        bores(cylinders(solids_of(item), Axis.Z.direction), 2 * pins.radius, 2 * pins.radius)
    )
    lines: dict[float, list[Hole]] = {}
    for hole in holes:
        lines.setdefault(round(hole.axis.position.dot(across), LEVEL_DIGITS), []).append(hole)
    full = exactly(
        [
            sorted(line, key=lambda hole: hole.axis.position.dot(pins.along.direction))
            for _, line in sorted(lines.items())
            if len(line) == count
        ],
        len(pins.lines),
        f"lines of {count} Ø{2 * pins.radius:g} pins",
    )
    seats = {}
    for names, line in zip(pins.lines, full, strict=True):
        for name, hole in zip(names, line, strict=True):
            centre = hole.axis.position
            top = Compound(hole.faces).bounding_box().max.Z
            seats[name] = seat_of(hole.faces, Pos(X=centre.X, Y=centre.Y, Z=top))
    return seats


def board_ports(item: Catalogue) -> dict[str, Seat]:
    board = item.board
    return {
        name: seat
        for found in [
            *(port_seats(item, port) for port in board.ports),
            *(pin_seats(item, pins) for pins in board.pins),
        ]
        for name, seat in found.items()
    }


@cached
def cable_exit(item: Catalogue) -> Location:
    match item.frame:
        case PlugFace(leaving=Axis() as leaving):
            return sideways(item, leaving)
        case _:
            return Pos(Z=vendor_reach(item, Axis.Z))


def sideways(item: Catalogue, leaving: Axis) -> Location:
    end = Plane(origin=leaving.position, z_dir=leaving.direction).offset(
        vendor_reach(item, leaving)
    )
    middle = Compound(faces_on(vendor_shape(item), end)).center(CenterOf.BOUNDING_BOX)
    return Location(Plane(origin=middle, x_dir=Axis.Z.direction, z_dir=leaving.direction))


@cached
def plug_seats(item: Catalogue, leaving: Location) -> dict[str, Seat]:
    shape = vendor_shape(item)
    nose = Plane.XY.offset(-vendor_reach(item, -Axis.Z))
    return {
        PLUG_FACE: seat_of(faces_on(shape, nose), Location()),
        CABLE_EXIT: seat_of(faces_on(shape, Plane(leaving)), leaving),
    }
