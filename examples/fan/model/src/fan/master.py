from dataclasses import dataclass
from functools import cache, cached_property

from build123d import Axis, BoundBox, Compound, Location, Plane, PolarLocations, Pos
from cad.design.master import Envelope, KeepOut, Master, Pose, given
from cad.library.bought.boards import BoardMount, board_mount
from cad.library.bought.catalogue import BoardKind, Catalogue, Download, Piece
from cad.library.bought.query import Hole, axis_of, bores, by_axis, cylinders, exactly
from cad.library.bought.vendor import named_solids, piece, solids_of, vendor_extent
from cad.library.features.hardware import insert_land
from cad.library.features.planes import between, halfway
from cad.library.fits import FITS_UNITS, Fits, STAINLESS_A2_70
from cad.library.mates import JointRange
from cad.library.printing import PRINT_SETTINGS_UNITS, PrintSettings
from cad.library.shapes import Block, radius_of
from cad.library.standard.fasteners import STOCK_UNITS, Metric, Stock, head_height, insert_size
from cad.library.turns import ALONG_X, HALF_TURN
from cad.standards import RatedTorque

from fan import models

VENDOR = models.VENDOR
FAN = Catalogue(
    file="fan_delta_afb0805l",
    grams=models.FAN_GRAMS,
    download=Download(
        url="https://www.delta-fan.com/Download/3D/AFB0805L.stp",
        sha256="6c829981cdc091ad6cc9db8da7feb26393c74b0863c95967dd5db0d7db9b5804",
    ),
)
STEPPER = Catalogue(
    file="stepper_28byj48",
    grams=models.STEPPER_GRAMS,
    model=models.stepper,
    pieces=(
        Piece(
            name=models.STATOR,
            grams=models.STEPPER_GRAMS - models.ROTOR_GRAMS,
            component=models.STATOR,
            solids=models.STATOR_SOLIDS,
        ),
        Piece(name=models.ROTOR, grams=models.ROTOR_GRAMS, component=models.ROTOR),
    ),
    torque=RatedTorque(
        nm=models.STEPPER_HOLDING_NM,
        source="Adafruit product 858 page, opened 24 Oct 2026: holding torque 150 g-cm (15 N-mm)",
    ),
)
STATOR = piece(STEPPER, models.STATOR)
ROTOR = piece(STEPPER, models.ROTOR)
XIAO = Catalogue(
    file="seeed_xiao_rp2040",
    grams=models.XIAO_GRAMS,
    download=Download(
        url="https://files.seeedstudio.com/wiki/XIAO-RP2040/res/seeed-studio-xiao-rp2040-3d-model.zip",
        sha256="e4e8be7d793a141ecb5a0c4efb710af97a47fc62cde28882b470a610396b48b9",
        member="Seeed Studio XIAO RP2040 v26.step",
    ),
)
TAPE = Catalogue(file="vhb_pad", grams=models.TAPE_GRAMS, model=models.vhb_pad)
BUTTON = Catalogue(file="button_adafruit_1445", grams=models.BUTTON_GRAMS, folder=VENDOR)
DRIVER = Catalogue(
    file="drv8833", grams=models.DRIVER_GRAMS, model=models.drv8833, kind=BoardKind()
)
BUMPER = Catalogue(file="bumper", grams=models.BUMPER_GRAMS, model=models.bumper)
DRIVER_HOLES = 2
FAN_HOLES = 4
FAN_HOLE = (4.2, 4.8)  # Delta AFB0805L specification: Ø4.5 ± 0.3
XIAO_PADS = 14
XIAO_PAD = (1.9, 2.1)  # the XIAO STEP's Ø2 edge pads
STEPPER_TABS = 2
STEPPER_TAB_HOLE = (3.4, 3.6)  # the Adafruit 858 STEP's tab bores
SHAFT_RADIUS = models.SHAFT_DIAMETER / 2
BUTTON_FLANGE_HEIGHT = 13.0  # Adafruit 1445 STEP: the flange's underside sits 13 mm up its body
FEET = 4
FEET_START = 45.0  # the feet sit between the floor screws, which lie on the X axis
OVERMOLD_SOURCE = "estimate: a common USB-C plug overmold; the USB-IF drawing was not opened"


@cache
def xiao_port() -> BoundBox:
    found = [solid for solid, name in named_solids(XIAO) if models.XIAO_PORT_PART in name]
    return Compound(exactly(found, models.XIAO_PORT_SOLIDS, "XIAO USB-C solids")).bounding_box()


@cache
def xiao_five_volt_pad() -> Pos:
    found = by_axis(bores(cylinders(solids_of(XIAO), Axis.Z.direction), *XIAO_PAD))
    inner = models.XIAO_WIDTH / 2 - models.XIAO_EDGE_PADS
    edge = [hole.axis.position for hole in found if abs(hole.axis.position.X) > inner]
    pads = exactly(edge, XIAO_PADS, "XIAO edge pads")
    right = [pad for pad in pads if pad.X > 0]
    (port_end,) = [pad for pad in right if max(each.Y for each in right) == pad.Y]
    return Pos(X=port_end.X, Y=port_end.Y)  # Seeed's XIAO RP2040 pinout: 5V, then GND


@cache
def fan_holes() -> list[Hole]:
    found = by_axis(bores(cylinders(solids_of(FAN), Axis.Y.direction), *FAN_HOLE))
    return exactly(found, FAN_HOLES, "fan mounting holes")


@dataclass(frozen=True)
class FanMaster(Master):
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
        source="estimate: the library's example fits, not calibrated on a printer",
    )
    stock: Stock = given(
        Stock(
            inserts={Metric.M3: "M3-0.5-5.7", Metric.M2_5: "M2.5-0.45-4"},
            insert_maker="CNCKitchen",
            screw_lengths={},
            fastener_grade=STAINLESS_A2_70,
        ),
        STOCK_UNITS,
        why="CNC Kitchen heat-set inserts: M3 for the printed joints, M2.5 for the boards",
        source="bd_warehouse HeatSetNut CNCKitchen data; CNC Kitchen store listings",
    )
    screw: Metric = given(
        Metric.M3,
        "-",
        why="One screw type joins the printed parts, the fan and the stepper (M8)",
        source="the 28BYJ-48's tab holes and the fan's Ø4.5 holes both pass M3; ISO 4762",
    )
    board_screw: Metric = given(
        Metric.M2_5,
        "-",
        why="The driver's mounting holes are made for M2.5",
        source="Adafruit DRV8833 Eagle board (Ø2.5 holes)",
    )
    sweep: float = given(
        45.0, "deg", why="R2: 90° in total, either side of straight ahead", source="prd.md R2"
    )
    neck_show: float = given(
        10.0,
        "mm",
        why="The neck reads as a short gap between head and puck, not a column",
        source="design input (design/language.md, neck)",
    )
    grille_slot: float = given(
        6.0,
        "mm",
        why="R7: each grille slot is half the test finger's width",
        source="IEC 61032 test probe B is a Ø12 mm finger; half of it is a design input",
    )
    lead_bore: float = given(
        4.0,
        "mm",
        why="The fan's four leads pass down the neck into the puck, plug cut off",
        source="estimate: four 28 AWG leads (Same Sky datasheet) with room to thread them",
    )
    plug_width: float = given(
        12.4, "mm", why="The widest USB-C plug overmold the port must take", source=OVERMOLD_SOURCE
    )
    plug_height: float = given(
        6.5, "mm", why="The tallest USB-C plug overmold the port must take", source=OVERMOLD_SOURCE
    )
    plug_reach: float = given(
        20.0, "mm", why="Room behind the puck for a USB-C plug body", source="design input"
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
        source="estimate: a common 0.4 mm nozzle profile",
    )

    @property
    def poses(self) -> tuple[Pose, ...]:
        return (
            Pose(name="rest", joints={}),
            Pose(name="swept left", joints={models.SWEEP: self.sweep}),
            Pose(name="swept right", joints={models.SWEEP: -self.sweep}),
        )

    @property
    def sweep_range(self) -> JointRange:
        return JointRange(low=-self.sweep, high=self.sweep)

    @property
    def wall(self) -> float:
        return self.fits.structural_wall

    @property
    def insert_depth(self) -> float:
        return insert_size(self.screw, fits=self.fits, stock=self.stock).length + self.fits.min_wall

    @cached_property
    def fan_side(self) -> float:
        return vendor_extent(FAN).size.X

    @cached_property
    def fan_origin(self) -> Location:
        found = vendor_extent(FAN)
        return Pos(X=found.center().X, Y=found.max.Y, Z=found.center().Z)

    @cached_property
    def fan_depth(self) -> float:
        back = self.fan_origin.position.Y
        return max(back - face.bounding_box().min.Y for hole in fan_holes() for face in hole.faces)

    @property
    def lead_reach(self) -> float:
        return models.FAN_LEAD_WIRE

    @property
    def head_width(self) -> float:
        return self.fan_side + 2 * (self.fits.sliding + self.wall)

    @property
    def head_depth(self) -> float:
        return self.insert_depth + self.fan_depth + self.wall

    @property
    def head_back(self) -> float:
        return self.head_depth / 2

    @property
    def fan_back(self) -> float:
        return self.head_back - self.wall

    @property
    def fan_front(self) -> float:
        return self.fan_back - self.fan_depth

    @property
    def head_front(self) -> float:
        return -self.head_depth / 2

    @property
    def puck_radius(self) -> float:
        return self.head_width / 2

    @property
    def inside_radius(self) -> float:
        return self.puck_radius - self.wall

    @property
    def screw_sunk(self) -> float:
        return head_height(self.screw) + self.fits.sliding

    @property
    def floor_thickness(self) -> float:
        return self.screw_sunk + self.wall

    @property
    def floor_bottom(self) -> Plane:
        return Plane.XY.offset(models.BUMPER_HEIGHT)

    @property
    def floor_top(self) -> Plane:
        return self.floor_bottom.offset(self.floor_thickness)

    @cached_property
    def driver_mount(self) -> BoardMount:
        return board_mount(DRIVER, self.board_screw, DRIVER_HOLES)

    @property
    def standoff(self) -> float:
        inserted = insert_size(self.board_screw, fits=self.fits, stock=self.stock).length
        return inserted + self.fits.min_wall

    @cached_property
    def stepper_depth(self) -> float:
        return -vendor_extent(STEPPER).min.Z

    @cached_property
    def shaft(self) -> Axis:
        found = [
            face
            for face in cylinders(solids_of(STEPPER), Axis.Z.direction)
            if abs(radius_of(face) - SHAFT_RADIUS) < 0.01
        ]
        (face,) = exactly(found, 1, "stepper shaft faces")
        return axis_of(face)

    @cached_property
    def stepper_tab_spots(self) -> list[Location]:
        found = by_axis(bores(cylinders(solids_of(STEPPER), Axis.Z.direction), *STEPPER_TAB_HOLE))
        holes = exactly(found, STEPPER_TABS, "stepper tab holes")
        return [Pos(X=hole.axis.position.X, Y=hole.axis.position.Y) for hole in holes]

    @property
    def xiao_top(self) -> Plane:
        return self.floor_top.offset(models.TAPE_THICKNESS + models.XIAO_TOP)

    @property
    def tabs(self) -> Plane:
        return self.xiao_top.offset(self.stepper_depth + self.fits.sliding)

    @property
    def top(self) -> Plane:
        return self.tabs.offset(self.insert_depth)

    @property
    def top_under(self) -> Plane:
        return self.top.offset(-self.wall)

    @property
    def stepper_at(self) -> Location:
        shaft = self.shaft.position
        return Location(self.tabs) * HALF_TURN * Pos(X=-shaft.X, Y=-shaft.Y)

    @property
    def shaft_top(self) -> Plane:
        return self.tabs.offset(vendor_extent(STEPPER).max.Z)

    @property
    def head_bottom(self) -> Plane:
        return self.top.offset(self.neck_show)

    @property
    def fan_middle(self) -> Location:
        up = self.wall + self.fits.sliding + self.fan_side / 2
        return Location(self.head_bottom) * Pos(Y=(self.fan_back + self.fan_front) / 2, Z=up)

    @property
    def head_top(self) -> Plane:
        return Plane(self.fan_middle).offset(self.fan_side / 2 + self.fits.sliding + self.wall)

    @property
    def head_height(self) -> float:
        return between(self.head_bottom, self.head_top)

    @property
    def fan_at(self) -> Location:
        up = self.wall + self.fits.sliding + self.fan_side / 2
        return (
            Location(self.head_bottom)
            * Pos(Y=self.fan_back, Z=up)
            * ALONG_X
            * self.fan_origin.inverse()
        )

    @property
    def fan_screws(self) -> list[Pos]:
        placed = [self.fan_at * Pos(hole.axis.position) for hole in fan_holes()]
        across = [Pos(X=at.position.X, Z=at.position.Z) for at in placed]
        middle = self.fan_middle.position
        return [at for at in across if (at.position.X > middle.X) == (at.position.Z > middle.Z)]

    def facing_back(self, at: Location, depth: float) -> Location:
        return Location(
            Plane(origin=(at.position.X, depth, at.position.Z), x_dir=(1, 0, 0), z_dir=(0, 1, 0))
        )

    @property
    def lead_way(self) -> Location:
        return Pos(Y=self.fan_front - self.lead_reach / 2)

    @property
    def neck_radius(self) -> float:
        return -self.lead_way.position.Y + self.lead_bore / 2 + self.fits.min_wall

    @property
    def neck_opening(self) -> float:
        return -self.lead_way.position.Y + self.lead_bore / 2

    @property
    def neck_bottom(self) -> Plane:
        return self.top.offset(self.fits.sliding)

    @property
    def xiao_at(self) -> Location:
        port = xiao_port()
        mouth = (self.inside_radius**2 - port.max.X**2) ** 0.5
        return Location(self.floor_top) * Pos(Y=mouth - port.max.Y, Z=models.TAPE_THICKNESS)

    @property
    def tape_at(self) -> Location:
        return Location(self.floor_top) * Pos(Y=self.xiao_at.position.Y)

    @property
    def driver_at(self) -> Location:
        wall = self.inside_radius - self.fits.sliding
        long, short = models.DRIVER_LENGTH / 2, models.DRIVER_WIDTH / 2
        corner_on_wall = ((2 * wall**2 - (long - short) ** 2) ** 0.5 - (long + short)) / 2
        lift = self.standoff - self.driver_mount.board_bottom
        return Location(self.floor_top) * Pos(X=-corner_on_wall, Y=-corner_on_wall, Z=lift)

    @property
    def harness_level(self) -> Plane:
        return halfway(self.floor_top, self.tabs)

    @property
    def harness_lane(self) -> Location:
        return Location(self.harness_level) * Pos(X=self.inside_radius / 2)

    @property
    def stepper_lane(self) -> Location:
        return Location(self.harness_level) * Pos(X=-self.inside_radius / 2)

    @property
    def under_neck(self) -> Location:
        return Location(self.harness_level) * self.lead_way

    @property
    def button_at(self) -> Location:
        between = (self.neck_opening + self.inside_radius) / 2
        return Location(self.top) * Pos(Y=-between, Z=-BUTTON_FLANGE_HEIGHT)

    @property
    def screw_land(self) -> float:
        return insert_land(self.screw, fits=self.fits, stock=self.stock)

    @property
    def floor_spots(self) -> list[Location]:
        reach = self.inside_radius - self.screw_land
        return [Location(self.floor_top) * Pos(X=x) for x in (reach, -reach)]

    @property
    def feet_at(self) -> list[Location]:
        reach = self.puck_radius - models.BUMPER_DIAMETER
        corners = PolarLocations(reach, FEET, start_angle=FEET_START).locations
        return [Location(Plane.XY) * corner for corner in corners]

    @property
    def usb_keepout(self) -> KeepOut:
        port = xiao_port()
        mouth = Pos((self.xiao_at * Pos(Y=port.max.Y, Z=port.center().Z)).position)
        depth = self.puck_radius + self.plug_reach - mouth.position.Y
        at = mouth * Pos(Y=depth / 2, Z=-self.plug_height / 2)
        return KeepOut(
            block=Block(at=at, width=self.plug_width, depth=depth, height=self.plug_height),
            why="A USB-C plug reaches the XIAO's port through the puck's back wall",
        )

    @property
    def envelope(self) -> Envelope:
        return Envelope(
            block=Block(
                at=Location(),
                width=self.head_width,
                depth=self.head_width,
                height=self.head_top.origin.Z,
            ),
            why="The fan at rest: the head over a puck no wider than it (S4)",
        )


MASTER = FanMaster()
