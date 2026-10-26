from collections.abc import Sequence

from build123d import (
    Align,
    Axis,
    BuildLine,
    BuildPart,
    BuildSketch,
    Circle,
    Cylinder,
    Face,
    GeomType,
    Keep,
    Location,
    Locations,
    Mode,
    Part,
    Plane,
    Polyline,
    Pos,
    Rectangle,
    RegularPolygon,
    Rotation,
    Solid,
    VectorLike,
    extrude,
    insert,
    make_face,
    revolve,
    split,
)

from cad.library.features.planes import axis_along, between, foot_on, halfway, normal_to, radial_at
from cad.library.fits import Fits
from cad.library.shapes import Brep, FacesOn, SeatQuery, built
from cad.library.standard.fasteners import Metric, nut_across_flats
from cad.library.standard.magnets import DiscSize
from cad.library.turns import UPSIDE_DOWN


def extrude_to(
    start: Plane | Location,
    end: Plane,
    *,
    sketch: BuildSketch,
    mode: Mode = Mode.ADD,
    taper: float = 0.0,
) -> Part:
    on = Plane(Location(start))
    return extrude(sketch.sketch, amount=between(on, end), mode=mode, taper=taper)


def round_side(radius: float, start: Plane, end: Plane) -> list[Face]:
    with BuildPart(mode=Mode.PRIVATE) as span:
        with BuildSketch(start) as profile:
            Circle(radius)
        extrude_to(start, end, sketch=profile)
    return list(built(span).faces().filter_by(GeomType.CYLINDER))


def within(stock: Brep, *outside: Plane) -> Brep:
    with BuildPart(mode=Mode.PRIVATE) as body:
        insert(stock)
        for plane in outside:
            split(bisect_by=plane, keep=Keep.BOTTOM)
    return built(body)


def open_slot(on: Plane, radius: float, run: float, to: Plane) -> Brep:
    with BuildPart(mode=Mode.PRIVATE) as slot:
        with BuildSketch(on) as profile:
            Circle(radius)
            Rectangle(2 * radius, run, align=(Align.CENTER, Align.MIN))
        extrude_to(on, to, sketch=profile)
    return built(slot)


def block_between(
    near: Plane, far: Plane, *, on: Plane, width: float, up_to: Plane, mode: Mode = Mode.ADD
) -> None:
    with BuildSketch(foot_on(on, of=Location(halfway(near, far)))) as block:
        Rectangle(between(near, far), width)
    extrude_to(on, up_to, sketch=block, mode=mode)


def sector(
    about: Axis, *, start: float, span: float, inner: float, outer: float, low: Plane, high: Plane
) -> Solid:
    with BuildPart(mode=Mode.PRIVATE) as body:
        with BuildSketch(radial_at(low, start)), Locations(Pos(X=inner)):
            Rectangle(outer - inner, between(low, high), align=(Align.MIN, Align.MIN))
        revolve(axis=about, revolution_arc=span)
    (solid,) = built(body).solids()
    return solid


def sector_ends(
    level: Plane, start: float, span: float, radius: float, solid: bool
) -> list[SeatQuery]:
    ends = ((start, not solid), (start + span, solid))
    return [
        SeatQuery(
            frame=Location(radial_at(level, angle))
            * Pos(X=radius)
            * (UPSIDE_DOWN if flip else Location()),
            faces=[FacesOn(plane=radial_at(level, angle))],
        )
        for angle, flip in ends
    ]


def turned(on: Plane, start: Plane, steps: Sequence[tuple[float, Plane]], mode: Mode) -> None:
    along = normal_to(on.x_dir, through=on.location)
    station = between(along, start)
    corners = [(station, 0.0)]
    for radius, far in steps:
        corners += [(station, radius), (station := between(along, far), radius)]
    with BuildSketch(on) as profile:
        with BuildLine():
            Polyline(*corners, (station, 0.0), close=True)
        make_face()
    revolve(profile.sketch, axis=axis_along(on.x_dir, through=on.location), mode=mode)


def disc_seat(disc: DiscSize, seats: Sequence[Location | Plane], *, fits: Fits) -> None:
    with Locations(*[Location(seat) for seat in seats]):
        Cylinder(
            fits.pressed(disc.diameter) / 2,
            disc.thickness,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )


def nut_pocket(screw: Metric, seats: list[Location], depth: float, *, fits: Fits) -> None:
    with BuildSketch(*seats) as pockets:
        RegularPolygon((nut_across_flats(screw) + fits.sliding) / 2, 6, major_radius=False)
    extrude(pockets.sketch, amount=depth, mode=Mode.SUBTRACT)


def nut_slot(
    screw: Metric, nuts: Sequence[Location], reach: float, depth: float, *, fits: Fits
) -> None:
    nut_pocket(screw, list(nuts), depth, fits=fits)
    with BuildSketch(*nuts) as slots, Locations(Pos(X=reach / 2)):
        Rectangle(reach, nut_across_flats(screw) + 2 * fits.sliding)
    extrude(slots.sketch, amount=depth, mode=Mode.SUBTRACT)


def roofed(plane: Plane, up: VectorLike) -> Plane:
    return Plane(Axis(plane.location), up)


def teardrop(radius: float, *, fits: Fits) -> None:
    Circle(radius)
    with Locations(Rotation(0, 0, -fits.overhang_deg)):
        Rectangle(radius, radius, align=(Align.MIN, Align.MIN))


def roofed_both_ways(radius: float, ceiling: float, *, fits: Fits) -> None:
    teardrop(radius, fits=fits)
    with Locations(Rotation(0, 0, 180)):
        teardrop(radius, fits=fits)
    Rectangle(2 * ceiling, 2 * radius, mode=Mode.INTERSECT)


def roofed_bore(
    near: Plane, far: Plane, up: VectorLike, radius: float, ceiling: float, *, fits: Fits
) -> None:
    with BuildSketch(roofed(near, up)) as bore:
        roofed_both_ways(radius, ceiling, fits=fits)
    extrude_to(roofed(near, up), far, mode=Mode.SUBTRACT, sketch=bore)
