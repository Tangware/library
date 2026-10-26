from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from build123d import Axis, Location, Plane, Pos

from cad.design.master import Envelope, KeepOut, Master, given
from cad.library.bought.boards import BoardMount, board_mount
from cad.library.bought.catalogue import BoardKind, Catalogue, Port
from cad.library.bought.connectors import port_seats
from cad.library.features.hardware import insert_land
from cad.library.fits import FITS_UNITS, STAINLESS_A2_70, Fits
from cad.library.printing import PRINT_SETTINGS_UNITS, PrintSettings
from cad.library.shapes import Block
from cad.library.standard.fasteners import STOCK_UNITS, Metric, Stock, insert_size
from cad.library.standard.magnets import DISC_UNITS, DiscSize

VENDOR = Path(__file__).parents[2] / "vendor"
PICO_2_GRAMS_ESTIMATED = 3.0
PICO_2_USB = Port(
    name="USB", instance="edac_690-005-298-486:edac_690-005-298-486", mating=Axis.Y, across=Axis.X
)
PICO_2 = Catalogue(
    file="rpi_pico2",
    grams=PICO_2_GRAMS_ESTIMATED,
    folder=VENDOR,
    kind=BoardKind(ports=(PICO_2_USB,)),
)
PICO_2_HOLES = 4
N45_6X3 = DiscSize(
    kind="N45 disc magnet",
    short_name="magnet",
    diameter=6.0,
    thickness=3.0,
    pull_n=4.54,  # K&J Magnetics: to an identical magnet at 0.7 mm
)
OVERMOLD_SOURCE = (
    "Micro-USB plug overmold envelope as quoted by ora.it.com; the USB-IF drawing was not opened"
)


@dataclass(frozen=True)
class BoxMaster(Master):
    fits: Fits = given(
        Fits(
            sliding=0.2,
            bearing_seat=0.05,
            bearing_proud=0.1,
            snap=0.6,
            membrane=0.5,
            min_wall=1.0,
            structural_wall=2.0,
            overhang_deg=45.0,
            printed_hole=0.25,
            press=0.25,
            clearance_fit="Normal",
            plastic_pilot=0.8,
            plastic_thread=2.0,
            insert_pull_out_n={3.0: 1167.0},
            spring_force_share=0.6,
        ),
        FITS_UNITS,
        why="Print allowances for an FDM PETG printer",
        source="estimate: the library's test fits, not calibrated on a printer",
    )
    stock: Stock = given(
        Stock(
            inserts={Metric.M3: "M3-0.5-5.7", Metric.M2: "M2-0.4-3"},
            insert_maker="CNCKitchen",
            screw_lengths={},
            fastener_grade=STAINLESS_A2_70,
        ),
        STOCK_UNITS,
        why="CNC Kitchen heat-set inserts for the lid screws and the board screws",
        source="bd_warehouse HeatSetNut data, CNC Kitchen store listings",
    )
    lid_screw: Metric = given(
        Metric.M3,
        "-",
        why="One screw type closes the box; M3 is the smallest common insert size with a 2.5 mm key",
        source="ISO 4762",
    )
    board_screw: Metric = given(
        Metric.M2,
        "-",
        why="The Pico 2's 2.1 mm mounting holes are made for M2",
        source="Raspberry Pi Pico 2 datasheet, section 3",
    )
    magnet: DiscSize = given(
        N45_6X3,
        DISC_UNITS,
        why="Holds the box to a steel surface",
        source="K&J Magnetics pull force for a 6 x 3 mm N45 disc",
    )
    board_gap: float = given(
        2.0,
        "mm",
        why="Room to lift the board out by its edges",
        source="design input",
    )
    plug_width: float = given(
        10.6, "mm", why="The widest micro-USB plug body the port must take", source=OVERMOLD_SOURCE
    )
    plug_height: float = given(
        8.5, "mm", why="The tallest micro-USB plug body the port must take", source=OVERMOLD_SOURCE
    )
    plug_reach: float = given(
        20.0,
        "mm",
        why="Room outside the box for a micro-USB cable's plug body",
        source="design input",
    )
    cable_run: float = given(
        40.0,
        "mm",
        why="How far in front of the box the USB cable reaches the desk",
        source="design input",
    )

    print_settings: PrintSettings = given(
        PrintSettings(
            preset="structural",
            walls=4,
            top_layers=5,
            bottom_layers=5,
            infill=0.15,
            extrusion_width=0.45,
            layer_height=0.2,
        ),
        PRINT_SETTINGS_UNITS,
        why="Every printed part takes the structural preset",
        source="estimate: the library's test structural preset",
    )

    @cached_property
    def mount(self) -> BoardMount:
        return board_mount(PICO_2, self.board_screw, PICO_2_HOLES)

    @property
    def wall(self) -> float:
        return self.fits.structural_wall

    @property
    def floor(self) -> Plane:
        return Plane.XY.offset(self.wall)

    @property
    def standoff(self) -> float:
        return (
            insert_size(self.board_screw, fits=self.fits, stock=self.stock).length
            + self.fits.min_wall
        )

    @property
    def board_at(self) -> Location:
        return Location(self.floor) * Pos(Z=self.standoff - self.mount.board_bottom)

    @property
    def lid_land(self) -> float:
        return insert_land(self.lid_screw, fits=self.fits, stock=self.stock)

    @property
    def inside_half_width(self) -> float:
        return self.mount.length / 2 + self.board_gap + 2 * self.lid_land

    @property
    def inside_back(self) -> float:
        return min(edge.position.Y for edge in self.mount.edges) - self.board_gap

    @property
    def inside_front(self) -> float:
        return self.mount.middle.position.Y + self.mount.width / 2

    @property
    def usb_keepout(self) -> KeepOut:
        connector_middle = self.mount.board_top + self.mount.parts_above / 2
        bottom = connector_middle - self.plug_height / 2
        depth = self.wall + self.plug_reach
        at = self.board_at * Pos(Y=self.inside_front + depth / 2, Z=bottom)
        return KeepOut(
            block=Block(
                at=at,
                width=self.plug_width,
                depth=depth,
                height=self.plug_height,
            ),
            why="A micro-USB plug reaches the board's port through the front wall",
        )

    @property
    def usb_port(self) -> Location:
        return self.board_at * port_seats(PICO_2, PICO_2_USB)[PICO_2_USB.name].frame

    @property
    def cable_exit(self) -> Location:
        return self.usb_port * Pos(Z=self.wall + self.plug_reach)

    @property
    def cable_on_desk(self) -> Location:
        exit = self.cable_exit
        return Location(Plane.XY) * Pos(X=exit.position.X, Y=exit.position.Y + self.cable_run)

    @property
    def rim(self) -> Plane:
        keepout = self.usb_keepout.block
        top = keepout.at * Pos(Z=keepout.height + self.wall)
        return Plane(origin=(0, 0, top.position.Z))

    @property
    def outside(self) -> Block:
        middle_y = (self.inside_back + self.inside_front) / 2
        return Block(
            at=Location((0, middle_y, 0)),
            width=2 * (self.inside_half_width + self.wall),
            depth=self.inside_front - self.inside_back + 2 * self.wall,
            height=self.rim.origin.Z,
        )

    @property
    def inside(self) -> Block:
        outside = self.outside
        return Block(
            at=outside.at * Pos(Z=self.wall),
            width=outside.width - 2 * self.wall,
            depth=outside.depth - 2 * self.wall,
            height=outside.height - self.wall,
        )

    @property
    def lid_spots(self) -> list[Location]:
        x = self.inside_half_width - self.lid_land
        ys = (self.inside_back + self.lid_land, self.inside_front - self.lid_land)
        top = self.rim.origin.Z
        return [Location((sx * x, y, top)) for y in ys for sx in (-1, 1)]

    @property
    def magnet_seats(self) -> list[Location]:
        return [
            Location(Plane.XY) * Pos(X=spot.position.X, Y=spot.position.Y)
            for spot in self.lid_spots
        ]

    @property
    def envelope(self) -> Envelope:
        outside = self.outside
        whole = Block(
            at=outside.at,
            width=outside.width,
            depth=outside.depth,
            height=outside.height + self.wall,
        )
        return Envelope(block=whole, why="The closed box with its lid")


MASTER = BoxMaster()
