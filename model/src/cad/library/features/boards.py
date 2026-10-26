from dataclasses import dataclass

from build123d import (
    Axis,
    BuildLine,
    BuildSketch,
    Circle,
    Location,
    Locations,
    Mode,
    Plane,
    Polyline,
    Pos,
    Rectangle,
    Until,
    add,
    extrude,
    make_face,
)

from cad.library.bought.boards import MOUNTING_HOLES, BoardMount, board_mount
from cad.library.bought.catalogue import USB_C, Catalogue
from cad.library.bought.query import exactly
from cad.library.features.cuts import extrude_to
from cad.library.features.hardware import (
    Anchor,
    Fastening,
    Hole,
    Screws,
    clamp_length,
    fastened,
    insert_holes,
    insert_land,
    insert_seats,
    nut_seat,
    screw_seats,
    screwed,
)
from cad.library.features.planes import box_reach, outline
from cad.library.fits import Fits
from cad.library.mates import Connector
from cad.library.shapes import FacesOn, Part, SeatQuery
from cad.library.standard.fasteners import (
    Metric,
    Stock,
    clearance_hole,
    nut_across_flats,
    nut_height,
)
from cad.library.standard.profiles import HexSize
from cad.library.turns import UPSIDE_DOWN

BOARD_ROLE = "board"


def port_to_the_back(item: Catalogue, name: str) -> Location:
    (port,) = exactly([p for p in item.board.ports if p.name == name], 1, f"{item.file} {name}")
    return Location(Plane(Axis.Z, port.mating.direction)).inverse()


def usb_c_to_the_back(item: Catalogue) -> Location:
    return port_to_the_back(item, USB_C)


@dataclass(frozen=True)
class Board:
    name: str
    item: Catalogue
    screw: Metric
    holes: int
    turn: Location
    standoff: float

    @property
    def mount(self) -> BoardMount:
        return board_mount(self.item, self.screw, holes=self.holes)

    def mounted(self, on: Location) -> Mounted:
        return Mounted(name=self.name, board=self.mount, on=on * self.turn, height=self.standoff)

    def reach(self, on: Location, toward: Plane) -> Plane:
        return box_reach(self.item, self.mounted(on).at, toward)


@dataclass(frozen=True)
class Mounted:
    name: str
    board: BoardMount
    on: Location
    height: float

    @property
    def at(self) -> Location:
        return self.board.standing(on=self.on, height=self.height)


@dataclass(frozen=True)
class BoardScrews:
    screws: Screws
    nuts: list[Location]


def nut_post_radius(screw: Metric, *, fits: Fits) -> float:
    return (
        HexSize(across_flats=nut_across_flats(screw) + fits.sliding).corner_radius + fits.min_wall
    )


def screwed_down(board: BoardMount, at: Location, *, stock: Stock) -> BoardScrews:
    length = clamp_length(board.screw, Anchor.NUT, board.board_thickness, stock=stock)
    return BoardScrews(
        screws=Screws(seats=board.topside(at), size=board.screw, length=length),
        nuts=board.underside(at),
    )


def board_holes(board: BoardMount, at: Location) -> Hole:
    return Hole(face=Plane(at), seats=board.topside(at), screw=board.screw, anchor=Anchor.CLEARANCE)


def board_screws(
    board: Part,
    mount: BoardMount,
    at: Location,
    into: Hole,
    holder: Connector,
    closes: bool = False,
    *,
    stock: Stock,
) -> Fastening:
    held = Connector(board, MOUNTING_HOLES)
    return screwed(
        board_holes(mount, at), into, held, holder, BOARD_ROLE, closes=closes, stock=stock
    )


def on_the_posts(board: BoardMount, at: Location) -> Location:
    return at * Pos(Z=board.board_bottom)


def post_tops(board: BoardMount, at: Location) -> list[Location]:
    with Locations(on_the_posts(board, at)):
        return Locations(*board.spots).locations


def board_inserts(board: BoardMount, at: Location, *, fits: Fits, stock: Stock) -> Hole:
    tops = Plane(on_the_posts(board, at))
    return insert_seats(tops, post_tops(board, at), board.screw, fits=fits, stock=stock)


def board_nuts_seats(board: BoardMount, at: Location) -> Hole:
    seats = board.underside(at)
    return Hole(face=Plane(at), seats=seats, screw=board.screw, anchor=Anchor.NUT)


def hook(
    under_the_board: Location, thickness: float, *, fits: Fits, hook_width: float, hook_lip: float
) -> None:
    lip = thickness + fits.sliding
    with BuildSketch(Plane(under_the_board * Plane.XZ.location)) as profile:
        with BuildLine():
            Polyline(
                (fits.sliding, 0),
                (fits.sliding + fits.min_wall, 0),
                (fits.sliding + fits.min_wall, lip + hook_lip),
                (fits.sliding, lip + hook_lip),
                (-fits.snap, lip),
                (fits.sliding, lip),
                close=True,
            )
        make_face()
    extrude(profile.sketch, amount=hook_width / 2, both=True)
    with (
        BuildSketch(under_the_board * UPSIDE_DOWN) as root,
        Locations(Pos(X=fits.sliding + fits.min_wall / 2)),
    ):
        Rectangle(fits.min_wall, hook_width)
    extrude(root.sketch, until=Until.NEXT)


def relief(under_the_board: Location, depth: float, *, fits: Fits, hook_width: float) -> None:
    room = fits.sliding + fits.min_wall + fits.snap
    with BuildSketch(under_the_board) as gap, Locations(Pos(X=room / 2)):
        Rectangle(room, hook_width + 2 * fits.sliding)
    extrude(gap.sketch, amount=-depth, mode=Mode.SUBTRACT)


def nut_posts(
    board: BoardMount, at: Location, on: Plane, name: str, *, fits: Fits, stock: Stock
) -> Hole:
    mount = screwed_down(board, at, stock=stock)
    with BuildSketch(*mount.nuts) as posts:
        Circle(nut_post_radius(board.screw, fits=fits))
    extrude_to(at * Pos(Z=board.board_bottom) * UPSIDE_DOWN, on, sketch=posts)
    with Locations(*mount.screws.seats):
        clearance_hole(board.screw, mount.screws.length + fits.sliding, fits=fits)
    hole = board_nuts_seats(board, at)
    screw_seats(
        name,
        [nut_post(nut, board.screw, fits=fits) for nut in hole.seats],
        hole,
        bears_on=[FacesOn(plane=Plane(on_the_posts(board, at)))],
    )
    return hole


def insert_posts(
    board: BoardMount, at: Location, on: Plane, name: str, *, fits: Fits, stock: Stock
) -> Hole:
    with BuildSketch(*board.underside(at)) as posts:
        Circle(insert_land(board.screw, fits=fits, stock=stock))
    extrude_to(on_the_posts(board, at) * UPSIDE_DOWN, on, sketch=posts)
    tops = Plane(on_the_posts(board, at))
    return insert_holes(tops, post_tops(board, at), board.screw, name, fits=fits, stock=stock)


def nut_post(nut: Location, screw: Metric, *, fits: Fits) -> SeatQuery:
    pocket = nut_seat(nut, screw, nut_height(screw) + fits.sliding, fits=fits)
    return SeatQuery(
        frame=nut, faces=[FacesOn(plane=Plane(nut), pierced_by=(Axis(nut),)), *pocket.faces]
    )


def under_the_board(mounted: Mounted, *, fits: Fits, stock: Stock) -> None:
    board = mounted.board
    corners = board.corner_holes
    left, right, front, back = corners.left, corners.right, corners.front, corners.back
    sides = [(left, front), (right, front), (right, back), (left, back)]
    with BuildSketch(mode=Mode.PRIVATE) as between_the_posts:
        add(outline(Plane.XY, sides))
        with Locations(*board.spots):
            Circle(insert_land(board.screw, fits=fits, stock=stock), mode=Mode.SUBTRACT)
    extrude(
        mounted.at * Pos(Z=board.board_bottom) * between_the_posts.sketch,
        amount=board.item.board.parts_under_the_board,
        dir=-Plane(mounted.at).z_dir,
        mode=Mode.SUBTRACT,
    )


def standoff_mount(
    board: BoardMount, on: Location, height: float, name: str, *, fits: Fits, stock: Stock
) -> Hole:
    at = board.standing(on=on, height=height)
    return insert_posts(board, at, Plane(on), name, fits=fits, stock=stock)


def under_the_hole(hole: Mounted) -> Location:
    (under,) = hole.board.underside(hole.at)
    return under


def board_held(
    mount: BoardMount, posts: Hole, board: Part, holder: Connector, *, stock: Stock
) -> Fastening:
    held = Connector(board, MOUNTING_HOLES)
    return fastened(board_holes(mount, Location()), posts, held, holder, BOARD_ROLE, stock=stock)
