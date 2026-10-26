from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Cylinder,
    Location,
    Locations,
    Mode,
    Plane,
    PolarLocations,
    Pos,
    Rectangle,
    VectorLike,
    revolve,
)

from cad.library.features.cuts import extrude_to, roofed_bore
from cad.library.features.hardware import (
    LIPS,
    Fastening,
    Hole,
    fastened,
    held_by,
    insert_holes,
    insert_land,
    screw_holes,
)
from cad.library.features.planes import between, normal_to, radial_at
from cad.library.fits import Fits
from cad.library.mates import Connector, Kind, Mate, named
from cad.library.printing import PrintSettings
from cad.library.shapes import (
    FACES,
    Brep,
    FaceQuery,
    FacesOn,
    Part,
    Printed,
    RoundFaces,
    SeatQuery,
    built,
    register,
    register_each,
)
from cad.library.standard.bearings import (
    INNER_RACE,
    OUTER_RACE,
    BearingRings,
    BearingSize,
    Race,
    Role,
    bearing_rings,
    housing_seat_radius,
    inner_ring,
    shaft_seat_radius,
)
from cad.library.standard.fasteners import Metric, Stock, counterbore_radius, insert_size
from cad.library.turns import turn_to
from cad.library.why import Why

BEARING_SEATS = "bearing seats"
SHAFT_SEATS = "shaft seats"
RETAINER_INSERTS = "retainer inserts"


def bearing_proud_of(face: Plane, *, fits: Fits) -> Plane:
    return face.offset(fits.bearing_proud)


@dataclass(frozen=True)
class RetainerScrews:
    screw: Metric
    count: int
    across: float


def retainer_face_beyond(inside: Plane, *, screw: Metric, fits: Fits, stock: Stock) -> Plane:
    return inside.offset(fits.min_wall + insert_size(screw, fits=fits, stock=stock).length)


def shoulder_plane(bearing: BearingSize, face: Plane) -> Plane:
    return face.offset(-bearing.width)


def housing_seat(
    bearing: BearingSize, face: Plane, opening: Plane, *, fits: Fits
) -> list[FaceQuery]:
    shoulder = shoulder_plane(bearing, face)
    radius = housing_seat_radius(bearing, fits=fits)
    depth = between(shoulder, opening)
    with Locations(shoulder):
        Cylinder(
            radius,
            depth,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
        Cylinder(
            bearing.between_races,
            fits.structural_wall,
            align=(Align.CENTER, Align.CENTER, Align.MAX),
            mode=Mode.SUBTRACT,
        )
    past_the_bearing = depth > bearing.width
    return [
        RoundFaces(
            axis=Axis(shoulder.location),
            radius=radius,
            length=min(depth, bearing.width),
            split_at=face if past_the_bearing else None,
        ),
        FacesOn(plane=shoulder),
    ]


@dataclass(frozen=True)
class Retainer:
    bearing: BearingSize
    holds: Race
    face: Plane
    fits: Fits
    stock: Stock
    screws: RetainerScrews
    screws_toward: Axis = field(default_factory=Axis.Z.reverse)

    @property
    def race(self) -> Plane:
        return bearing_proud_of(self.face, fits=self.fits)

    @property
    def screw_circle(self) -> float:
        land = insert_land(self.screws.screw, fits=self.fits, stock=self.stock)
        match self.holds:
            case Race.OUTER:
                return housing_seat_radius(self.bearing, fits=self.fits) + land
            case Race.INNER:
                return shaft_seat_radius(self.bearing, fits=self.fits) - land

    @property
    def inside(self) -> float:
        match self.holds:
            case Race.OUTER:
                return self.bearing.outer_race_middle
            case Race.INNER:
                return 0.0

    @property
    def outside(self) -> float:
        match self.holds:
            case Race.OUTER:
                return self.screw_circle + counterbore_radius(self.screws.screw, fits=self.fits)
            case Race.INNER:
                return self.bearing.da_max / 2

    @property
    def top(self) -> Plane:
        return self.race.offset(self.fits.structural_wall)

    @property
    def insert_spots(self) -> list[Location]:
        across, count = self.screws.across, self.screws.count
        with Locations(self.face):
            return PolarLocations(
                self.screw_circle,
                count,
                start_angle=turn_to(self.face, self.screws_toward.direction)
                - across / 2
                + across / (2 * count),
                angular_range=across,
            ).locations


@dataclass(frozen=True)
class BearingSite:
    name: str
    face: Plane
    opening: Plane

    @property
    def seat(self) -> Location:
        return Location(-self.face)

    @property
    def connector(self) -> str:
        return f"{self.name} seat"

    @property
    def inner_ring(self) -> str:
        return inner_ring(self.name)


@dataclass(frozen=True)
class BearingAxis:
    name: str
    role: Role
    bearing: BearingSize
    near: Plane
    far: Plane
    fits: Fits
    stock: Stock
    retainer_screws: RetainerScrews
    near_opening: Plane | None = None

    @property
    def near_site(self) -> BearingSite:
        opening = self.near if self.near_opening is None else self.near_opening
        return BearingSite(name=f"{self.name} bearing", face=-self.near, opening=-opening)

    @property
    def far_site(self) -> BearingSite:
        match self.role:
            case Role.CROSSED:
                return BearingSite(
                    name=f"{self.name} bearing outer",
                    face=self.far.offset(-self.fits.structural_wall),
                    opening=self.far,
                )
            case Role.LOCATES | Role.FLOATS:
                return BearingSite(
                    name=f"{self.name} bearing",
                    face=bearing_proud_of(self.far, fits=self.fits),
                    opening=self.far,
                )

    @property
    def sites(self) -> tuple[BearingSite, ...]:
        match self.role:
            case Role.CROSSED:
                return (self.near_site, self.far_site)
            case Role.LOCATES | Role.FLOATS:
                return (self.far_site,)

    @property
    def shaft_shoulder(self) -> Plane:
        match self.role:
            case Role.CROSSED:
                return self.near
            case Role.LOCATES | Role.FLOATS:
                return shoulder_plane(self.bearing, self.far_site.face)

    @property
    def collar_end(self) -> Plane:
        return self.far_site.face.offset(self.fits.structural_wall)

    @property
    def bearing_covers(self) -> tuple[Retainer, ...]:
        match self.role:
            case Role.LOCATES:
                return (
                    Retainer(
                        bearing=self.bearing,
                        holds=Race.OUTER,
                        face=self.far,
                        fits=self.fits,
                        stock=self.stock,
                        screws=self.retainer_screws,
                    ),
                )
            case Role.CROSSED | Role.FLOATS:
                return ()

    @property
    def end_plates(self) -> tuple[Retainer, ...]:
        match self.role:
            case Role.LOCATES | Role.FLOATS:
                return (
                    Retainer(
                        bearing=self.bearing,
                        holds=Race.INNER,
                        face=self.far,
                        fits=self.fits,
                        stock=self.stock,
                        screws=self.retainer_screws,
                    ),
                )
            case Role.CROSSED:
                return ()


def seats_at_each_site(
    axis: BearingAxis, cut: Callable[[BearingSite], list[FaceQuery]]
) -> list[FaceQuery]:
    made: list[FaceQuery] = []
    for site in axis.sites:
        seat = cut(site)
        register(site.connector, site.seat, seat)
        made += seat
    return made


def bearing_seats(axis: BearingAxis, turning: Location) -> None:
    made = seats_at_each_site(
        axis, lambda site: housing_seat(axis.bearing, site.face, site.opening, fits=axis.fits)
    )
    register(BEARING_SEATS, turning, made)


def housing_seats(axis: BearingAxis) -> list[FaceQuery]:
    return [
        query
        for site in axis.sites
        for query in housing_seat(axis.bearing, site.face, site.opening, fits=axis.fits)
    ]


def seat_between_lips(axis: BearingAxis, site: BearingSite) -> list[FaceQuery]:
    shoulder = shoulder_plane(axis.bearing, site.face)
    match axis.role:
        case Role.FLOATS:
            near, far = shoulder.offset(-axis.fits.sliding), site.face.offset(axis.fits.sliding)
        case Role.LOCATES | Role.CROSSED:
            near, far = shoulder, site.face
    radius = housing_seat_radius(axis.bearing, fits=axis.fits)
    with BuildSketch(near) as seat:
        Circle(radius)
    extrude_to(near, far, mode=Mode.SUBTRACT, sketch=seat)
    return [
        RoundFaces(axis=Axis(near.location), radius=radius, length=between(near, far)),
        FacesOn(plane=near),
        FacesOn(plane=far),
    ]


def seats_between_lips(axis: BearingAxis) -> list[FaceQuery]:
    return seats_at_each_site(axis, lambda site: seat_between_lips(axis, site))


def lipped_seats(axis: BearingAxis, up: VectorLike, start: Plane, end: Plane) -> list[FaceQuery]:
    lip = axis.bearing.between_races
    roofed_bore(start, end, up, lip, lip, fits=axis.fits)
    return seats_between_lips(axis)


def shaft_seat(axis: BearingAxis, site: BearingSite) -> list[FaceQuery]:
    radius = shaft_seat_radius(axis.bearing, fits=axis.fits)
    width = axis.bearing.width
    ends = (site.face, Plane(site.seat).offset(width))
    return [
        RoundFaces(axis=Axis(site.seat), radius=radius, length=width, split_at=end) for end in ends
    ]


def shaft_seats(axis: BearingAxis, turning: Location) -> None:
    register_each(
        SHAFT_SEATS,
        turning,
        [SeatQuery(frame=site.seat, faces=shaft_seat(axis, site)) for site in axis.sites],
    )


def inner_ring_seats(axis: BearingAxis) -> None:
    for site in axis.sites:
        register(site.inner_ring, site.seat, shaft_seat(axis, site))


def shaft_shoulder(axis: BearingAxis, start: Plane) -> None:
    with BuildSketch(start) as shoulder:
        Circle(axis.bearing.da_max / 2)
    extrude_to(start, axis.shaft_shoulder, sketch=shoulder)


def collared_shaft(axis: BearingAxis, start: Plane) -> None:
    shaft_shoulder(axis, start)
    face = axis.far_site.face
    with BuildSketch(axis.shaft_shoulder) as shaft_seat:
        Circle(shaft_seat_radius(axis.bearing, fits=axis.fits))
    extrude_to(axis.shaft_shoulder, face, sketch=shaft_seat)
    with BuildSketch(face) as collar:
        Circle(axis.bearing.da_max / 2)
    extrude_to(face, axis.collar_end, sketch=collar)


def axis_rings(axis: BearingAxis, frame: Location) -> list[BearingRings]:
    return [
        bearing_rings(site.name, frame * site.seat, axis.bearing, axis.role, axis.name)
        for site in axis.sites
    ]


def axis_bearings(axis: BearingAxis, frame: Location) -> list[Part]:
    return [part for rings in axis_rings(axis, frame) for part in rings.parts]


def seated_bearings(axis: BearingAxis, frame: Location, holder: Part, race: str) -> Fastening:
    rings = axis_rings(axis, frame)
    return Fastening(
        parts=[part for each in rings for part in each.parts],
        mates=[
            mate
            for site, each in zip(axis.sites, rings, strict=True)
            for mate in held_by([each.on(race)], race, Connector(holder, site.connector))
        ],
    )


def retainer_seat(ring: Retainer) -> Hole:
    return insert_holes(
        ring.face,
        ring.insert_spots,
        ring.screws.screw,
        RETAINER_INSERTS,
        fits=ring.fits,
        stock=ring.stock,
    )


def retainer_room(ring: Retainer) -> None:
    with BuildSketch(ring.face) as room:
        Circle(ring.outside + ring.fits.sliding)
    extrude_to(ring.face, ring.top.offset(ring.fits.sliding), mode=Mode.SUBTRACT, sketch=room)


def retainer(ring: Retainer) -> Hole:
    with BuildSketch(radial_at(ring.race, 0.0)) as section, Locations(Pos(X=ring.inside)):
        Rectangle(
            ring.outside - ring.inside,
            between(ring.race, ring.top),
            align=(Align.MIN, Align.MIN),
        )
    revolve(section.sketch, axis=Axis(ring.race.location))
    return screw_holes(
        ring.race,
        ring.insert_spots,
        ring.screws.screw,
        between(ring.face, ring.top),
        LIPS,
        fits=ring.fits,
    )


def retainer_part(
    ring: Retainer,
    name: str,
    frame: Location,
    body: Brep,
    print_settings: PrintSettings,
    print_why: Why,
) -> Printed:
    return Printed(
        name=name,
        pose=frame,
        body=body,
        bed=tuple(-ring.race.z_dir),
        print_settings=print_settings,
        print_why=print_why,
    )


def screwed_retainer(
    ring: Retainer, printed: Printed, holes: Hole, housing: Connector, seat: Hole
) -> Fastening:
    screwed = fastened(holes, seat, held=Connector(printed, LIPS), holder=housing, stock=ring.stock)
    return Fastening(parts=[printed, *screwed.parts], mates=screwed.mates)


def retained(
    ring: Retainer,
    name: str,
    frame: Location,
    housing: Connector,
    seat: Hole,
    print_settings: PrintSettings,
    print_why: Why,
) -> Fastening:
    with BuildPart() as body:
        holes = retainer(ring)
    printed = retainer_part(ring, name, frame, built(body), print_settings, print_why)
    return screwed_retainer(ring, printed, holes, housing, seat)


def turning_in(
    bearing: BearingRings,
    housing: Connector,
    shaft: Connector,
    sense: Axis,
    servo: Part | None = None,
) -> list[Mate]:
    turning = Location(normal_to(sense.direction, through=bearing.outer.pose))
    return [
        *held_by([bearing.outer], OUTER_RACE, housing),
        *held_by([bearing.inner], INNER_RACE, shaft),
        Mate(
            f"{named(shaft.part)} in {named(housing.part)}",
            Kind.REVOLUTE,
            child=shaft,
            parent=housing,
            at=turning,
            servo=servo,
            fasteners=tuple(bearing.parts),
        ),
    ]


def turning_rings(sites: Sequence[BearingSite], frame: Location) -> list[Mate]:
    return [
        Mate(
            f"{site.inner_ring} in {site.name}",
            Kind.BALL,
            child=Connector(site.inner_ring, FACES),
            parent=Connector(site.name, FACES),
            at=frame * site.seat,
            closes=True,
        )
        for site in sites
    ]
