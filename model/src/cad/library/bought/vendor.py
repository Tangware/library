import gzip
import hashlib
import io
import os
import tempfile
import zipfile
from collections import Counter
from collections.abc import Callable, Iterator
from dataclasses import dataclass, replace
from http.client import BAD_GATEWAY, GATEWAY_TIMEOUT, OK, SERVICE_UNAVAILABLE, HTTPSConnection
from pathlib import Path
from urllib.parse import urlsplit

from build123d import (
    Axis,
    BoundBox,
    CenterOf,
    Compound,
    Face,
    Keep,
    Location,
    Plane,
    Pos,
    ShapeList,
    Solid,
    Vertex,
    split,
)

from cad.library.bought.catalogue import Bores, Catalogue, Download, Piece, PlugFace, Rgb, ServoKind
from cad.library.bought.query import (
    LENGTH_TOLERANCE,
    aligned,
    axis_of,
    bores,
    cylinders,
    exactly,
    on_axis,
    planes,
)
from cad.library.bought.step import Look, Named, coloured_step
from cad.library.derived import derived
from cad.library.shapes import (
    OUTSIDE,
    Block,
    Brep,
    Outside,
    Part,
    Seat,
    Shaped,
    common,
    radius_of,
    seat_of,
)

DOWNLOADS = Path.cwd() / "build" / "downloads"
DOWNLOAD_TIMEOUT_SECONDS = 600
USER_AGENT = "tangware"
DOWNLOAD_ATTEMPTS = 3
GATEWAY_ERRORS = {BAD_GATEWAY, SERVICE_UNAVAILABLE, GATEWAY_TIMEOUT}


def maker_step(source: Download, body: bytes) -> bytes:
    step = body if source.member is None else zipfile.ZipFile(io.BytesIO(body)).read(source.member)
    found = hashlib.sha256(step).hexdigest()
    if found != source.sha256:
        raise ValueError(f"{source.url} gave a STEP with sha256 {found}, not {source.sha256}")
    return step


def _fetched(address: str) -> bytes:
    url = urlsplit(address)
    for _ in range(DOWNLOAD_ATTEMPTS):
        connection = HTTPSConnection(url.netloc, timeout=DOWNLOAD_TIMEOUT_SECONDS)
        connection.request("GET", url.path, headers={"User-Agent": USER_AGENT})
        response = connection.getresponse()
        body = response.read()
        connection.close()
        if response.status == OK:
            return body
        if response.status not in GATEWAY_ERRORS:
            break
    raise ValueError(f"{address} answered {response.status} {response.reason}")


def downloaded(source: Download) -> Path:
    path = DOWNLOADS / f"{source.sha256}.step"
    if path.exists():
        return path
    step = maker_step(source, _fetched(source.url))
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(f".{os.getpid()}.part")
    partial.write_bytes(step)
    partial.replace(path)
    return path


@derived
def placed_solids(
    shape: Path | Download | Callable[[], Brep],
    correct: Callable[[list[Solid]], list[Solid]] | None,
) -> tuple[Named, ...]:
    if isinstance(shape, Download):
        found = coloured_step(downloaded(shape))
    elif isinstance(shape, Path):
        with tempfile.NamedTemporaryFile(suffix=".step") as step:
            step.write(gzip.decompress(shape.read_bytes()))
            step.flush()
            found = coloured_step(Path(step.name))
    else:
        found = [
            (solid, (_model_colour(leaf),) * len(solid.faces()), leaf.label)
            for leaf in _leaves(shape())
            for solid in leaf.solids()
        ]
    if correct is None:
        return tuple(found)
    corrected = correct([solid for solid, _, _ in found])
    return tuple(
        (new, look if new is old else evenly(new, look), name)
        for (old, look, name), new in zip(found, corrected, strict=True)
    )


def evenly(solid: Solid, look: Look) -> Look:
    ((colour, _),) = Counter(look).most_common(1)
    return (colour,) * len(solid.faces())


def _leaves(shape: Brep) -> Iterator[Brep]:
    if shape.children:
        for child in shape.children:
            yield from _leaves(child)
    else:
        yield shape


def _model_colour(shape: Brep) -> Rgb | None:
    return None if shape.color is None else tuple(shape.color)[:3]


def on_the_bores(solids: list[Solid], wanted: Bores) -> Plane:
    found = exactly(
        ShapeList(
            bores(Compound(solids).faces(), 2 * wanted.narrowest_radius, 2 * wanted.widest_radius)
        ),
        wanted.count,
        "bores",
    )
    axes = [axis_of(f) for f in found]
    upward = [axis if axis.direction.Z > 0 else -axis for axis in axes]
    if not all(aligned(one.direction, other.direction, True) for one in upward for other in upward):
        raise ValueError("the bores are not parallel")
    middle = Compound([Vertex(axis.position) for axis in axes]).center(CenterOf.BOUNDING_BOX)
    pointing_up = Compound([Vertex(axis.direction) for axis in upward]).center(
        CenterOf.BOUNDING_BOX
    )
    return Plane(origin=middle, x_dir=Axis.X.direction, z_dir=pointing_up)


def on_the_plug_face(solids: list[Solid], face: PlugFace) -> Plane:
    into = face.into_the_socket.direction
    nose = max(vertex.center().dot(into) for solid in solids for vertex in solid.vertices())
    fronts = exactly(
        [f for f in planes(solids, into) if abs(f.center().dot(into) - nose) <= LENGTH_TOLERANCE],
        face.fronts,
        "plug front faces",
    )
    middle = Compound(fronts).center(CenterOf.BOUNDING_BOX)
    return Plane(origin=middle, x_dir=face.across.direction, z_dir=-into).offset(face.inserted)


def moulded_end(solids: list[Solid], toward: Axis, length: float) -> list[Solid]:
    (cable,) = exactly(solids, 1, "moulded cables")
    facing = Plane(origin=toward.position, z_dir=toward.direction)
    reach = (facing.location.inverse() * cable).bounding_box().max.Z
    (head,) = exactly(
        split(cable, bisect_by=facing.offset(reach - length), keep=Keep.TOP).solids(),
        1,
        "moulded heads",
    )
    return [head]


def _one_solid_each(pieces: list[tuple[Brep, Look]]) -> list[tuple[Solid, Look]]:
    kept = []
    for piece, look in pieces:
        if piece.solids():
            (solid,) = exactly(piece.solids(), 1, "solids left of a cut vendor solid")
            kept.append((solid, evenly(solid, look)))
    return kept


@derived
def vendor_solids(item: Catalogue) -> tuple[tuple[Solid, Look], ...]:
    raw = placed_solids(item.shape, item.cleanup.correct)
    chosen = raw if item.cleanup.piece is None else _of_the_piece(raw, item.cleanup.piece)
    solids = [solid for solid, _, _ in raw]
    match item.frame:
        case Bores():
            frame = on_the_bores(solids, item.frame)
        case PlugFace():
            frame = on_the_plug_face([solid for solid, _, _ in chosen], item.frame)
        case _:
            frame = item.frame
    local = [frame.location.inverse() * solid for solid, _, _ in chosen]
    if item.cleanup.centred:
        footprint = Compound(local).bounding_box()
        to_the_middle = Pos(-footprint.center().X, -footprint.center().Y, -footprint.min.Z)
        local = [to_the_middle * solid for solid in local]
    looks = [
        tuple(item.cleanup.paint or colour or item.cleanup.colour for colour in look)
        for _, look, _ in chosen
    ]
    kept = list(zip(local, looks, strict=True))
    if item.cleanup.keep_above is not None:
        above = Plane.XY.offset(item.cleanup.keep_above)
        kept = _one_solid_each(
            [(split(solid, bisect_by=above, keep=Keep.TOP), look) for solid, look in kept]
        )
    if item.cleanup.trim_radius is not None:
        reach = Compound([solid for solid, _ in kept]).bounding_box()
        within = Solid.make_cylinder(
            item.cleanup.trim_radius, reach.size.Z, plane=Plane.XY.offset(reach.min.Z)
        )
        kept = _one_solid_each([(common(solid, within), look) for solid, look in kept])
    if item.cleanup.only == "all":
        return tuple(kept)
    whole = replace(item, cleanup=replace(item.cleanup, only="all"))
    horn = _horn(whole, in_front=True)
    if item.cleanup.only == "bare case":
        left_off = {horn, _horn(whole, in_front=False)}
        return tuple(found for i, found in enumerate(kept) if i not in left_off)
    return tuple(
        (solid, look)
        for i, (solid, look) in enumerate(kept)
        if (i == horn) == (item.cleanup.only == "horn")
    )


def _of_the_piece(raw: tuple[Named, ...], piece: Piece) -> tuple[Named, ...]:
    return exactly(
        tuple((solid, look, name) for solid, look, name in raw if piece.component in name),
        piece.solids,
        piece.name,
    )


def named_solids(item: Catalogue) -> list[tuple[Solid, str]]:
    filtered = (item.cleanup.keep_above, item.cleanup.trim_radius)
    if (
        any(value is not None for value in filtered)
        or item.cleanup.piece is not None
        or item.cleanup.only != "all"
    ):
        raise ValueError(
            f"{item.file} keeps only some of its solids, so their names do not line up"
        )
    return [
        (solid, name)
        for (solid, _), (_, _, name) in zip(
            vendor_solids(item), placed_solids(item.shape, item.cleanup.correct), strict=True
        )
    ]


def solids_of(item: Catalogue) -> list[Solid]:
    return [solid for solid, _ in vendor_solids(item)]


@derived
def _horn(item: Catalogue, in_front: bool) -> int:
    if not isinstance(item.kind, ServoKind):
        raise ValueError(f"{item.file} has no horn")
    radius = item.kind.horn_radius

    def turns(solid: Solid) -> bool:
        return any(
            abs(radius_of(f) - radius) <= LENGTH_TOLERANCE
            and on_axis(f)
            and (f.bounding_box().max.Z > LENGTH_TOLERANCE) is in_front
            for f in cylinders([solid], Axis.Z.direction)
        )

    solids = solids_of(item)
    (index,) = exactly([i for i, solid in enumerate(solids) if turns(solid)], 1, "servo horns")
    return index


def vendor_shape(item: Catalogue) -> Brep:
    return Compound(solids_of(item))


@derived
def vendor_reach(item: Catalogue, toward: Axis) -> float:
    facing = Plane(origin=toward.position, z_dir=toward.direction)
    along_an_axis = sorted(abs(value) for value in toward.direction) == [0.0, 0.0, 1.0]
    shape = vendor_box(item) if along_an_axis else vendor_shape(item)
    return (facing.location.inverse() * shape).bounding_box().max.Z


def vendor_extent(item: Catalogue) -> BoundBox:
    return vendor_box(item).bounding_box()


@derived
def vendor_box(item: Catalogue) -> Solid:
    found = vendor_shape(item).bounding_box()
    size = found.size
    return Solid.make_box(size.X, size.Y, size.Z, plane=Plane(origin=found.min))


def vendor_block(item: Catalogue, at: Location) -> Block:
    found = vendor_extent(item)
    middle = found.center()
    return Block(
        at=at * Pos(middle.X, middle.Y, found.min.Z),
        width=found.size.X,
        depth=found.size.Y,
        height=found.size.Z,
    )


def piece(item: Catalogue, name: str) -> Catalogue:
    (chosen,) = exactly([found for found in item.pieces if found.name == name], 1, name)
    return replace(item, cleanup=replace(item.cleanup, piece=chosen), pieces=(), grams=chosen.grams)


@dataclass(kw_only=True)
class Bought(Part):
    item: Catalogue
    material: str = "bought"

    @property
    def grams(self) -> float:
        return self.item.grams

    @property
    def catalogue(self) -> Catalogue:
        return self.item

    def shape(self) -> Brep:
        return vendor_shape(self.item)

    def published(self) -> dict[str, Seat]:
        points = {point.name: seat_of([], point.at) for point in self.item.connection_points}
        return {OUTSIDE: Outside(self.unposed()), **points, **self.connectors}

    def coloured_solids(self) -> list[tuple[Brep, Rgb | None]]:
        return [
            (self.pose * shape, colour)
            for solid, look in vendor_solids(self.item)
            for shape, colour in painted(solid, look)
        ]


def whole(name: str, pose: Location, item: Catalogue) -> Bought:
    return Bought(name=name, pose=pose, item=item)


@dataclass(kw_only=True)
class Cut(Shaped):
    item: Catalogue
    material: str = "bought"

    @property
    def label(self) -> str:
        return self.name

    @property
    def catalogue(self) -> Catalogue:
        return self.item


def painted(solid: Solid, look: Look) -> list[tuple[Brep, Rgb | None]]:
    by_colour: dict[Rgb | None, list[Face]] = {}
    for face, colour in zip(solid.faces(), look, strict=True):
        by_colour.setdefault(colour, []).append(face)
    if len(by_colour) == 1:
        (colour,) = by_colour
        return [(solid, colour)]
    return [(Compound(faces), colour) for colour, faces in by_colour.items()]
