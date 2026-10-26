from collections.abc import Sequence
from dataclasses import dataclass, replace
from enum import Enum

from build123d import (
    Align,
    Axis,
    BuildSketch,
    Circle,
    Cylinder,
    Face,
    Location,
    Locations,
    Mode,
    Plane,
    Pos,
    Rectangle,
    Sketch,
    Until,
    extrude,
)

from cad.library.features.cuts import nut_pocket
from cad.library.features.planes import (
    between,
    corner,
    either_side,
    first_of,
    foot_on,
    last_of,
    normal_to,
    outline,
    parallel,
    station,
)
from cad.library.fits import Fits
from cad.library.mates import (
    TURNING,
    Connector,
    Kind,
    Mate,
    Reference,
    copy_keys,
    joined,
    named,
)
from cad.library.shapes import (
    OUTSIDE,
    FacesOn,
    Part,
    RoundFaces,
    SeatQuery,
    clamp_face,
    register,
    register_each,
    register_more,
)
from cad.library.standard.fasteners import (
    BEARING_FACE,
    SOCKET_HEAD,
    UNDER_HEAD,
    Ends,
    Metric,
    Nut,
    Pin,
    Screw,
    Stock,
    ThreadedInsert,
    clearance_hole,
    counterbore_radius,
    counterbored_hole,
    insert_hole,
    insert_size,
    nut_across_flats,
    nut_height,
    past_the_nut,
    screw_length,
)
from cad.library.standard.magnets import Disc, DiscSize

LIPS = "lips"
INSERTS = "inserts"


def mount_lug(*, fits: Fits) -> float:
    return fits.structural_wall


@dataclass(frozen=True)
class Screws:
    seats: list[Location]
    size: Metric
    length: float
    ships_with: str = ""


def seated(spots: Sequence[Location], depth: float) -> list[Location]:
    return [spot * Pos(Z=depth) for spot in spots]


def several(count: int, name: str) -> str:
    return name if count == 1 else f"{count} \N{MULTIPLICATION SIGN} {name}"


def hardware_name(owner: str, count: int, kind: str) -> str:
    return f"{owner} {several(count, kind)}"


def with_role(role: str, kind: str) -> str:
    return " ".join(word for word in (role, kind) if word)


def screws_at(
    owner: str, frame: Location, screws: Screws, role: str = "", *, stock: Stock
) -> list[Part]:
    name = hardware_name(owner, len(screws.seats), with_role(role, f"{screws.size.size} screw"))
    return [
        Screw(
            name=name,
            pose=frame * seat,
            size=screws.size,
            length=screws.length,
            grade=stock.fastener_grade,
            ships_with=screws.ships_with,
        )
        for seat in screws.seats
    ]


def disc_name(owner: str, disc: DiscSize) -> str:
    return hardware_name(owner, 1, f"Ø{disc.diameter:g} {disc.short_name}")


def disc_names(owner: str, count: int, disc: DiscSize) -> list[str]:
    return copy_keys(disc_name(owner, disc), count)


def discs_at(
    owner: str, frame: Location, seats: Sequence[Location | Plane], disc: DiscSize
) -> list[Part]:
    return [
        Disc(name=disc_name(owner, disc), pose=frame * Location(seat), size=disc) for seat in seats
    ]


def insert_land(screw: Metric, *, fits: Fits, stock: Stock) -> float:
    return insert_size(screw, fits=fits, stock=stock).outside / 2 + fits.min_wall


def deepest_seat(insert_face: Plane, screw: Metric, *, fits: Fits, stock: Stock) -> Plane:
    return insert_face.offset(
        max(stock.screw_lengths[screw, SOCKET_HEAD])
        - insert_size(screw, fits=fits, stock=stock).length
    )


def clearance_holes(
    spots: Sequence[Location], screw: Metric, depth: float, *, fits: Fits
) -> list[Location]:
    seats = seated(spots, depth)
    with Locations(*seats):
        clearance_hole(screw, depth, fits=fits)
    return seats


def mount_lugs(
    face: Plane,
    spots: list[Location],
    land: float,
    screw: Metric,
    *,
    fits: Fits,
) -> Hole:
    with BuildSketch(*spots) as lugs:
        Rectangle(2 * land, 2 * land)
    extrude(lugs.sketch, amount=mount_lug(fits=fits))
    return screw_holes(face, spots, screw, mount_lug(fits=fits), LIPS, fits=fits)


@dataclass(frozen=True)
class LevelScrews:
    wall: Plane
    level: Plane
    spots: list[Location]
    lug: float
    screw: Metric


def square_through(wall: Plane, point: Location, level: Plane) -> Plane:
    out = Plane(Axis(level.location), wall.z_dir).x_dir
    return normal_to(out, through=point, x_dir=wall.x_dir)


def land_edges(wall: Plane, point: Location, level: Plane, land: float) -> list[Plane]:
    square = square_through(wall, point, level)
    across = normal_to(wall.x_dir, through=point)
    return [
        station(square, through=corner(wall, side, across))
        for side in either_side(parallel(level, through=point), land)
    ]


def inner_land_edge(wall: Plane, point: Location, level: Plane, land: float) -> Plane:
    return first_of(square_through(wall, point, level), land_edges(wall, point, level, land))


def level_screws(
    wall: Plane,
    points: Sequence[Location],
    level: Plane,
    screw: Metric,
    *,
    fits: Fits,
    stock: Stock,
) -> LevelScrews:
    land = insert_land(screw, fits=fits, stock=stock)
    square = square_through(wall, wall.location, level)
    edges = land_edges(wall, wall.location, level, land)
    return LevelScrews(
        wall=wall,
        level=level,
        spots=[Location(inner_land_edge(wall, point, level, land)) for point in points],
        lug=between(first_of(square, edges), last_of(square, edges).offset(mount_lug(fits=fits))),
        screw=screw,
    )


def lug_profile(screws: LevelScrews, spot: Location, inner: Plane, low: Plane, high: Plane) -> Face:
    seat = Plane(spot).offset(screws.lug)
    across = normal_to(screws.wall.x_dir, through=spot)
    return outline(across, [(inner, low), (inner, high), (seat, high), (seat, low)])


def wedge_profile(screws: LevelScrews, spot: Location, *, fits: Fits, stock: Stock) -> Face:
    high, low = either_side(
        parallel(screws.level, through=spot), insert_land(screws.screw, fits=fits, stock=stock)
    )
    return lug_profile(screws, spot, screws.wall, low, high)


def wedge_lugs(screws: LevelScrews, adding: bool = False, *, fits: Fits, stock: Stock) -> Hole:
    profiles = [wedge_profile(screws, spot, fits=fits, stock=stock) for spot in screws.spots]
    extrude(Sketch(profiles), amount=insert_land(screws.screw, fits=fits, stock=stock), both=True)
    return screw_holes(
        screws.wall,
        screws.spots,
        screws.screw,
        screws.lug,
        LIPS,
        adding,
        fits=fits,
    )


def level_inserts(
    face: Plane,
    levels: Sequence[LevelScrews],
    name: str,
    *,
    fits: Fits,
    stock: Stock,
) -> Hole:
    made = [
        cut
        for level in levels
        for cut in insert_cuts(level.spots, level.screw, fits=fits, stock=stock)
    ]
    hole = merged(
        face,
        [
            insert_seats(level.wall, level.spots, level.screw, fits=fits, stock=stock)
            for level in levels
        ],
    )
    screw_seats(name, made, hole, bears_on=[FacesOn(plane=level.wall) for level in levels])
    return hole


def head_room(screws: Hole, *, fits: Fits) -> None:
    with BuildSketch(*screws.seats) as heads:
        Circle(counterbore_radius(screws.screw, fits=fits))
    extrude(heads.sketch, until=Until.LAST, mode=Mode.SUBTRACT)


def side_lugs(
    screws: LevelScrews,
    top: Plane,
    lid: Plane,
    adding: bool = False,
    *,
    fits: Fits,
    stock: Stock,
) -> Hole:
    inside = screws.wall.offset(-mount_lug(fits=fits))
    profiles = [lug_profile(screws, spot, inside, top, lid) for spot in screws.spots]
    extrude(Sketch(profiles), amount=insert_land(screws.screw, fits=fits, stock=stock), both=True)
    return wedge_lugs(screws, adding, fits=fits, stock=stock)


def floor_bosses(
    spots: Sequence[Location],
    floor: Plane,
    top: Plane,
    screw: Metric,
    grow: float,
    mode: Mode,
    *,
    fits: Fits,
) -> None:
    feet = [foot_on(floor, of=spot) for spot in spots]
    radius = counterbore_radius(screw, fits=fits) + fits.min_wall + grow
    with Locations(*feet):
        Cylinder(
            radius,
            between(floor, top) + grow,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=mode,
        )


class Anchor(Enum):
    NUT = "nut"
    INSERT = "insert"
    TAPPED = "tapped"
    CLEARANCE = "clearance"


@dataclass(frozen=True)
class Hole:
    face: Plane
    seats: list[Location]
    screw: Metric
    anchor: Anchor


def land(hole: Hole, *, fits: Fits, stock: Stock) -> float:
    match hole.anchor:
        case Anchor.NUT:
            return nut_across_flats(hole.screw) / 2 + fits.min_wall
        case Anchor.INSERT:
            return insert_land(hole.screw, fits=fits, stock=stock)
        case Anchor.CLEARANCE | Anchor.TAPPED:
            raise ValueError(f"a {hole.anchor.value} hole has no land")


def lip(seat: Location) -> SeatQuery:
    return SeatQuery(frame=seat, faces=[FacesOn(plane=Plane(seat), pierced_by=(Axis(seat),))])


def lips(seats: Sequence[Location]) -> list[SeatQuery]:
    return [lip(seat) for seat in seats]


def screw_seats(
    name: str,
    made: list[SeatQuery],
    hole: Hole,
    adding: bool = False,
    bears_on: Sequence[FacesOn | RoundFaces] = (),
) -> None:
    on = list(bears_on) if bears_on else [FacesOn(plane=hole.face)]
    screws = tuple(Axis(seat) for seat in hole.seats)
    pressed = [replace(query, pierced_by=screws) for query in on]
    clamp = [*pressed, *(query for each in made for query in each.faces)]
    if adding:
        register_more(name, instances=made)
        register_more(clamp_face(name), clamp)
    else:
        register_each(name, hole.face, made)
        register(clamp_face(name), hole.face, clamp)


def screw_holes(
    face: Plane,
    spots: list[Location],
    screw: Metric,
    depth: float,
    name: str,
    adding: bool = False,
    *,
    bears_on: Sequence[FacesOn | RoundFaces] = (),
    fits: Fits,
) -> Hole:
    hole = Hole(
        face=face,
        seats=clearance_holes(spots, screw, depth, fits=fits),
        screw=screw,
        anchor=Anchor.CLEARANCE,
    )
    screw_seats(name, lips(hole.seats), hole, adding, bears_on)
    return hole


def counterbored_screws(
    face: Plane,
    spots: Sequence[Location],
    screw: Metric,
    sunk: float,
    depth: float,
    *,
    fits: Fits,
) -> Hole:
    with Locations(*seated(spots, depth)):
        counterbored_hole(screw, sunk, depth, fits=fits)
    hole = Hole(face=face, seats=seated(spots, depth - sunk), screw=screw, anchor=Anchor.CLEARANCE)
    screw_seats(LIPS, lips(hole.seats), hole)
    return hole


def insert_seat(spot: Location, screw: Metric, *, fits: Fits, stock: Stock) -> Location:
    return spot * Pos(Z=-insert_size(screw, fits=fits, stock=stock).length)


def insert_seats(
    face: Plane, spots: Sequence[Location], screw: Metric, *, fits: Fits, stock: Stock
) -> Hole:
    seats = [insert_seat(spot, screw, fits=fits, stock=stock) for spot in spots]
    return Hole(face=face, seats=seats, screw=screw, anchor=Anchor.INSERT)


def insert_bore(spot: Location, screw: Metric, *, fits: Fits, stock: Stock) -> RoundFaces:
    radius = insert_size(screw, fits=fits, stock=stock).hole / 2
    return RoundFaces(axis=Axis(spot), radius=radius)


def insert_cut(spot: Location, screw: Metric, *, fits: Fits, stock: Stock) -> SeatQuery:
    with Locations(spot):
        insert_hole(screw, fits=fits, stock=stock)
    return SeatQuery(
        frame=insert_seat(spot, screw, fits=fits, stock=stock),
        faces=[insert_bore(spot, screw, fits=fits, stock=stock)],
    )


def insert_cuts(
    spots: Sequence[Location], screw: Metric, *, fits: Fits, stock: Stock
) -> list[SeatQuery]:
    return [insert_cut(spot, screw, fits=fits, stock=stock) for spot in spots]


def insert_holes(
    face: Plane,
    spots: Sequence[Location],
    screw: Metric,
    name: str,
    bears_on: Sequence[FacesOn | RoundFaces] = (),
    *,
    fits: Fits,
    stock: Stock,
) -> Hole:
    made = insert_cuts(spots, screw, fits=fits, stock=stock)
    hole = insert_seats(face, spots, screw, fits=fits, stock=stock)
    screw_seats(name, made, hole, bears_on=bears_on)
    return hole


def nut_pockets(
    face: Plane,
    spots: list[Location],
    screw: Metric,
    depth: float,
    name: str,
    *,
    fits: Fits,
) -> Hole:
    hole = Hole(face=face, seats=spots, screw=screw, anchor=Anchor.NUT)
    screw_seats(
        name,
        [nut_seat(spot, screw, depth, fits=fits) for spot in spots],
        hole,
    )
    return hole


def nut_seat(spot: Location, screw: Metric, depth: float, *, fits: Fits) -> SeatQuery:
    nut_pocket(screw, [spot], depth, fits=fits)
    return SeatQuery(
        frame=spot, faces=[FacesOn(plane=Plane(spot).offset(depth), pierced_by=(Axis(spot),))]
    )


@dataclass(frozen=True)
class Fastening:
    parts: list[Part]
    mates: list[Mate]


def held_by(parts: Sequence[Reference], on: str, holder: Connector) -> list[Mate]:
    return [
        Mate(
            f"{named(part)} in {named(holder.part)}",
            Kind.RIGID,
            child=Connector(part, on),
            parent=holder if holder.placing is not None else replace(holder, placing=part),
        )
        for part in parts
    ]


def closing_on(parts: Sequence[Reference], on: str, holder: Connector) -> list[Mate]:
    return [replace(mate, closes=True) for mate in held_by(parts, on, holder)]


def clamped_between(
    parts: Sequence[Reference], on: str, holder: Connector, closing: Connector
) -> list[Mate]:
    return [*held_by(parts, on, holder), *closing_on(parts, on, closing)]


def discs_in(held: Part, seats: Sequence[Location | Plane], disc: DiscSize, seat: str) -> Fastening:
    discs = discs_at(held.name, held.pose, seats, disc)
    return Fastening(parts=discs, mates=held_by(discs, OUTSIDE, Connector(held, seat)))


def subassembly(name: str, made: Fastening) -> Fastening:
    for part in made.parts:
        part.group = f"{name}/{part.group}".removesuffix("/")
    return made


def mounted_on(child: Connector, holder: Connector, fasteners: Sequence[Reference] = ()) -> Mate:
    return Mate(
        f"{named(child.part)} on {named(holder.part)}",
        Kind.RIGID,
        child=child,
        parent=holder,
        fasteners=tuple(fasteners),
    )


def together(each: Sequence[Fastening], parts: Sequence[Part] = ()) -> Fastening:
    return Fastening(
        parts=[*parts, *(part for one in each for part in one.parts)],
        mates=[mate for one in each for mate in one.mates],
    )


def clamp_length(screw: Metric, anchor: Anchor, reach: float, *, stock: Stock) -> float:
    match anchor:
        case Anchor.INSERT | Anchor.TAPPED:
            return screw_length(screw, reach, Ends.WITHIN, stock=stock)
        case Anchor.NUT:
            return screw_length(
                screw, reach + nut_height(screw) + past_the_nut(screw), Ends.PAST, stock=stock
            )
        case Anchor.CLEARANCE:
            raise ValueError(f"a {screw.size} screw is fastened into a nut, an insert or a thread")


def merged(face: Plane, holes: Sequence[Hole]) -> Hole:
    (screw,) = {hole.screw for hole in holes}
    (anchor,) = {hole.anchor for hole in holes}
    return Hole(
        face=face,
        seats=[seat for hole in holes for seat in hole.seats],
        screw=screw,
        anchor=anchor,
    )


def anchor_name(into: Hole, held: str, holder: str, role: str = "") -> str:
    if into.anchor in (Anchor.CLEARANCE, Anchor.TAPPED):
        raise ValueError(f"{held}: only a nut or an insert is a part of its own")
    kind = hardware_name(holder, 1, with_role(role, f"{into.screw.size} {into.anchor.value}"))
    return f"{kind} for {held}"


def anchors_of(
    into: Hole, frame: Location, held: str, holder: str, role: str = "", *, stock: Stock
) -> list[Part]:
    name = anchor_name(into, held, holder, role)
    match into.anchor:
        case Anchor.NUT:
            return [
                Nut(name=name, pose=frame * seat, size=into.screw, grade=stock.fastener_grade)
                for seat in into.seats
            ]
        case _:
            return [
                ThreadedInsert(
                    name=name,
                    pose=frame * seat,
                    designation=stock.inserts[into.screw],
                    maker=stock.insert_maker,
                )
                for seat in into.seats
            ]


def anchor_seat(into: Hole) -> str:
    return BEARING_FACE if into.anchor is Anchor.NUT else OUTSIDE


def seats_frame(holder: Connector, held: Part) -> Location:
    return held.pose if isinstance(holder.part, str) else holder.part.pose


def anchors_for(held: str) -> str:
    return f"{held} anchors"


def anchored(into: Hole, holder: Part, held: str, role: str = "", *, stock: Stock) -> Fastening:
    anchors = anchors_of(into, holder.pose, held, holder.name, role, stock=stock)
    on = Connector(holder, anchors_for(held))
    return Fastening(parts=anchors, mates=held_by(anchors, anchor_seat(into), on))


def clamp_screws(
    through: Hole,
    into: Hole,
    through_frame: Location,
    into_frame: Location,
    owner: str,
    role: str = "",
    *,
    stock: Stock,
) -> list[Part]:
    lengths = [
        clamp_length(
            through.screw,
            into.anchor,
            abs(between(Plane(into_frame * end), Plane(through_frame * head))),
            stock=stock,
        )
        for head, end in zip(through.seats, into.seats, strict=True)
    ]
    return [
        screw
        for length in sorted(set(lengths))
        for screw in screws_at(
            owner,
            through_frame,
            Screws(
                seats=[h for h, n in zip(through.seats, lengths, strict=True) if n == length],
                size=through.screw,
                length=length,
            ),
            role,
            stock=stock,
        )
    ]


def screwed(
    through: Hole,
    into: Hole,
    held: Connector,
    holder: Connector,
    role: str = "",
    closes: bool = False,
    *,
    stock: Stock,
) -> Fastening:
    part = joined(held.part)
    into_frame = seats_frame(holder, part)
    screws = clamp_screws(through, into, part.pose, into_frame, part.name, role, stock=stock)
    anchors = (
        []
        if into.anchor is Anchor.TAPPED
        else copy_keys(anchor_name(into, part.name, named(holder.part), role), len(into.seats))
    )
    clamp = Mate(
        f"{part.name} on {named(holder.part)}",
        Kind.RIGID,
        child=Connector(part, clamp_face(held.name)),
        parent=Connector(holder.part, clamp_face(holder.name)),
        closes=closes,
        fasteners=(*screws, *anchors),
    )
    return Fastening(parts=screws, mates=[clamp, *held_by(screws, UNDER_HEAD, held)])


def screwed_on(
    through: Hole,
    into: Hole,
    mount: Connector,
    fitted: Connector,
    role: str = "",
    *,
    stock: Stock,
) -> Fastening:
    made = screwed(through, into, mount, fitted, role, stock=stock)
    clamp, *screws_held = made.mates
    (first, *_) = made.parts
    on = replace(
        clamp,
        name=f"{named(fitted.part)} on {named(mount.part)}",
        child=clamp.parent,
        parent=clamp.child,
        approach=Axis(first.pose),
    )
    return Fastening(parts=made.parts, mates=[on, *screws_held])


def fastened(
    through: Hole,
    into: Hole,
    held: Connector,
    holder: Connector,
    role: str = "",
    *,
    stock: Stock,
) -> Fastening:
    return together(
        [
            screwed(through, into, held, holder, role, stock=stock),
            set_in(into, held, holder, role, stock=stock),
        ]
    )


def set_in(
    into: Hole, held: Connector, holder: Connector, role: str = "", *, stock: Stock
) -> Fastening:
    frame = seats_frame(holder, joined(held.part))
    anchors = anchors_of(into, frame, joined(held.part).name, named(holder.part), role, stock=stock)
    return Fastening(parts=anchors, mates=held_by(anchors, anchor_seat(into), holder))


def pinned(
    pin: Pin,
    into: Connector,
    through: Connector,
    kind: Kind,
    closes: bool = False,
    held_in: Connector | None = None,
) -> list[Mate]:
    return [
        *held_by([pin], OUTSIDE, into if held_in is None else held_in),
        Mate(
            f"{named(through.part)} on {pin.name}",
            kind,
            child=through,
            parent=into,
            at=pin.pose if kind in TURNING else None,
            closes=closes,
            fasteners=(pin,),
        ),
    ]
