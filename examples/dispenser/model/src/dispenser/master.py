from dataclasses import dataclass
from functools import cache, cached_property

from build123d import Axis, Location, Plane, PolarLocations, Pos, Rot
from cad.design.master import Envelope, KeepOut, Master, Pose, given
from cad.library.bought.boards import BoardMount, board_mount
from cad.library.bought.catalogue import BoardKind, Catalogue, Download, Piece, Port
from cad.library.bought.query import axis_of, bores, by_axis, cylinders, exactly
from cad.library.bought.vendor import piece, solids_of, vendor_extent
from cad.library.features.hardware import insert_land
from cad.library.fits import FITS_UNITS, Fits, STAINLESS_A2_70
from cad.library.printing import PRINT_SETTINGS_UNITS, PrintSettings
from cad.library.shapes import Block, radius_of
from cad.library.standard.fasteners import STOCK_UNITS, Metric, Stock, head_height, insert_size
from cad.library.turns import END_FOR_END, HALF_TURN, UPSIDE_DOWN
from cad.standards import RatedTorque

from dispenser import models

VENDOR = models.VENDOR
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
        nm=models.STEPPER_PULL_IN_NM,
        source="28BYJ-48 datasheet, MikroElektronika: pull-in torque 300 gf·cm at 100 pps",
    ),
)
STATOR = piece(STEPPER, models.STATOR)
ROTOR = piece(STEPPER, models.ROTOR)
PICO_USB = Port(
    name="USB", instance="edac_690-005-298-486:edac_690-005-298-486", mating=Axis.Y, across=Axis.X
)
PICO = Catalogue(
    file="rpi_pico2", grams=models.PICO_GRAMS, folder=VENDOR, kind=BoardKind(ports=(PICO_USB,))
)
PICO_HOLES = 4
DRIVER = Catalogue(
    file="drv8833", grams=models.DRIVER_GRAMS, model=models.drv8833, kind=BoardKind()
)
DRIVER_HOLES = 2
REED = Catalogue(file="reed_59140", grams=models.REED_GRAMS, model=models.reed_sensor)
REED_HOLES = 2
REED_HOLE = (3.1, 3.3)  # the model's Ø3.2 holes, from the Littelfuse 59140 datasheet's slots
ACTUATOR = Catalogue(file="actuator_57140", grams=models.ACTUATOR_GRAMS, model=models.actuator)
BUZZER = Catalogue(
    file="buzzer_soberton_wst_1205s",
    grams=models.BUZZER_GRAMS,
    download=Download(
        url="https://www.soberton.com/wp-content/uploads/2016/10/WST-1205S-1.step",
        sha256="c15700bc656a0e06a2bf2d244ce55cbdf63a65246c2ebe0a2dc985acdb4664f5",
    ),
)
LED = Catalogue(
    file="led_wp7113",
    grams=models.LED_GRAMS,
    download=Download(
        url="https://www.kingbrightusa.com/images/catalog/3D/STEP/WP7113.STEP",
        sha256="064c6dac47aa208490b792aee598b5053237b4a2f82e5411dab2ae2c80f39857",
    ),
)
OVERMOLD_SOURCE = (
    "Micro-USB plug overmold envelope as quoted by ora.it.com; the USB-IF drawing was not opened"
)
LED_BODY_FACES = 2  # the WP7113 STEP splits its body cylinder into two half faces
STEPPER_TABS = 2
STEPPER_TAB_HOLE = (3.4, 3.6)  # the Adafruit 858 STEP's tab bores, Ø3.5
SHAFT_RADIUS = models.SHAFT_DIAMETER / 2
CAROUSEL_TURN = "carousel on stepper"
DRAWER_SLIDE = "drawer in base"
PLATE_SCREWS = 4
PLATE_SCREWS_START = 45.0  # the plate screws sit on the diagonals, clear of the drawer and boards
FEET = 4
FEET_START = 0.0  # the feet sit between the plate screws


@cache
def stepper_tab_holes() -> list[Axis]:
    found = by_axis(bores(cylinders(solids_of(STEPPER), Axis.Z.direction), *STEPPER_TAB_HOLE))
    return [hole.axis for hole in exactly(found, STEPPER_TABS, "stepper tab holes")]


@cache
def led_axis() -> Axis:
    found = [
        face
        for face in cylinders(solids_of(LED), Axis.X.direction)
        if abs(radius_of(face) - models.LED_BODY / 2) < 0.01
    ]
    first, _ = exactly(found, LED_BODY_FACES, "LED body faces")
    return axis_of(first)


@cache
def stepper_shaft() -> Axis:
    found = [
        face
        for face in cylinders(solids_of(STEPPER), Axis.Z.direction)
        if abs(radius_of(face) - SHAFT_RADIUS) < 0.01
    ]
    (face,) = exactly(found, 1, "stepper shaft faces")
    return axis_of(face)


@dataclass(frozen=True)
class DispenserMaster(Master):
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
            inserts={Metric.M3: "M3-0.5-5.7", Metric.M2: "M2-0.4-3", Metric.M2_5: "M2.5-0.45-4"},
            insert_maker="CNCKitchen",
            screw_lengths={},
            fastener_grade=STAINLESS_A2_70,
        ),
        STOCK_UNITS,
        why="CNC Kitchen heat-set inserts: M3 for the shell, M2 and M2.5 for the boards",
        source="bd_warehouse HeatSetNut CNCKitchen data; CNC Kitchen store listings",
    )
    screw: Metric = given(
        Metric.M3,
        "-",
        why="One screw type holds the shell and the stepper (M8)",
        source="the 28BYJ-48's Ø3.5 tab holes pass M3; ISO 4762",
    )
    doses: int = given(
        28, "-", why="R2: a week of four daily doses between refills", source="prd.md R2"
    )
    pocket_reach: float = given(
        115.0,
        "mm",
        why="R3: each pocket's outer end is wider than a fingertip, so pills can be pushed in",
        source="design input, checked against a fingertip by test_r3",
    )
    pocket_start: float = given(
        40.0,
        "mm",
        why="The pockets start outside the stepper's screws and the carousel's web",
        source="design input",
    )
    pocket_height: float = given(
        25.0,
        "mm",
        why="R2: a large capsule lies flat or stands in a pocket",
        source="estimate: a 1000 mg fish-oil softgel is about 25 mm long, not measured",
    )
    pull_width: float = given(
        100.0,
        "mm",
        why="R7: the drawer's pull takes the four fingers of a large hand",
        source="estimate: 95th-percentile male hand breadth 95 mm, Pheasant, Bodyspace, not opened",
    )
    pull_height: float = given(
        8.0,
        "mm",
        why="R7: fingertips hook under the drawer's front lip",
        source="estimate: a fingertip's thickness, not measured",
    )
    tray_depth: float = given(
        12.0,
        "mm",
        why="R1: the drawer's tray takes a whole dose; test_r1 checks it against a pocket",
        source="design input",
    )
    pico_screw: Metric = given(
        Metric.M2,
        "-",
        why="The Pico 2 W's Ø2.1 mounting holes are made for M2",
        source="Raspberry Pi Pico 2 W datasheet, mechanical drawing",
    )
    driver_screw: Metric = given(
        Metric.M2_5,
        "-",
        why="The DRV8833 breakout's mounting holes are made for M2.5",
        source="Adafruit DRV8833 Eagle board (Ø2.5 holes)",
    )
    plug_width: float = given(
        10.6, "mm", why="The widest micro-USB plug body the port must take", source=OVERMOLD_SOURCE
    )
    plug_height: float = given(
        8.5, "mm", why="The tallest micro-USB plug body the port must take", source=OVERMOLD_SOURCE
    )
    plug_reach: float = given(
        20.0, "mm", why="Room behind the drum for the power plug's body", source="design input"
    )
    cable_run: float = given(
        60.0,
        "mm",
        why="How far behind the drum the power cable reaches the counter",
        source="design input",
    )
    material: str = given(
        "PETG brown",
        "-",
        why="S4: one warm earthy matte colour for every printed part, never white (P1)",
        source="design/language.md, colour; the spool is in the catalogue",
    )
    pull_reach: float = given(
        20.0,
        "mm",
        why="R7: fingers reach under the drawer's front lip to their first joint",
        source="estimate: a fingertip to its first joint, not measured",
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
    def sectors(self) -> int:
        return self.doses + 1

    @property
    def sector(self) -> float:
        return 360 / self.sectors

    @property
    def poses(self) -> tuple[Pose, ...]:
        return (
            Pose(name="rest", joints={}),
            Pose(name="first dose released", joints={CAROUSEL_TURN: self.sector}),
            Pose(name="drawer out", joints={DRAWER_SLIDE: self.drawer_travel}),
        )

    @property
    def wall(self) -> float:
        return self.fits.structural_wall

    @property
    def insert_depth(self) -> float:
        return insert_size(self.screw, fits=self.fits, stock=self.stock).length + self.fits.min_wall

    @property
    def screw_land(self) -> float:
        return insert_land(self.screw, fits=self.fits, stock=self.stock)

    @property
    def screw_sunk(self) -> float:
        return head_height(self.screw) + self.fits.sliding

    @property
    def rim_radius(self) -> float:
        return self.pocket_reach + self.wall

    @property
    def inside_radius(self) -> float:
        return self.rim_radius + self.fits.sliding

    @property
    def radius(self) -> float:
        return self.inside_radius + self.wall

    @property
    def plate_bottom(self) -> Plane:
        return Plane.XY.offset(models.BUMPER_HEIGHT)

    @property
    def plate_thickness(self) -> float:
        return self.wall

    @property
    def plate_bosses(self) -> Plane:
        return self.plate_top.offset(self.screw_sunk)

    @property
    def plate_top(self) -> Plane:
        return self.plate_bottom.offset(self.plate_thickness)

    @property
    def plate_radius(self) -> float:
        return self.inside_radius - self.fits.sliding

    @property
    def drawer_height(self) -> float:
        return self.pull_height + self.wall + self.tray_depth

    @property
    def drawer_bottom(self) -> Plane:
        return self.plate_top.offset(self.fits.sliding)

    @property
    def drawer_top(self) -> Plane:
        return self.drawer_bottom.offset(self.drawer_height)

    @property
    def light_band(self) -> float:
        sleeve = models.LED_FLANGE + 2 * self.fits.min_wall
        sensor = models.REED_HEIGHT + head_height(self.screw) + self.fits.sliding
        return max(sleeve, sensor)

    @property
    def floor_under(self) -> Plane:
        return self.drawer_top.offset(self.fits.sliding + self.light_band)

    @property
    def floor_top(self) -> Plane:
        return self.floor_under.offset(self.wall)

    @property
    def carousel_bottom(self) -> Plane:
        return self.floor_top.offset(self.fits.sliding)

    @property
    def carousel_top(self) -> Plane:
        return self.carousel_bottom.offset(self.pocket_height)

    @property
    def plug_bottom(self) -> Plane:
        return self.carousel_top.offset(self.fits.sliding)

    @property
    def rim(self) -> Plane:
        return self.plug_bottom.offset(self.wall)

    @property
    def top(self) -> Plane:
        return self.rim.offset(self.wall)

    @cached_property
    def stepper_depth(self) -> float:
        return -vendor_extent(STEPPER).min.Z

    @property
    def stepper_at(self) -> Location:
        shaft = stepper_shaft().position
        return Location(self.floor_under) * HALF_TURN * Pos(X=-shaft.X, Y=-shaft.Y)

    @property
    def shaft_top(self) -> Plane:
        return self.floor_under.offset(vendor_extent(STEPPER).max.Z)

    @property
    def shaft_boss_radius(self) -> float:
        return models.SHAFT_BOSS_DIAMETER / 2 + self.fits.sliding

    @property
    def stepper_spots(self) -> list[Location]:
        tabs = [self.stepper_at * Pos(hole.position) for hole in stepper_tab_holes()]
        return [Location(self.floor_under) * Pos(X=at.position.X, Y=at.position.Y) for at in tabs]

    @property
    def stepper_boss_top(self) -> Plane:
        return self.floor_under.offset(self.insert_depth)

    @property
    def web_bottom(self) -> Plane:
        return self.stepper_boss_top.offset(self.fits.sliding)

    @property
    def web_top(self) -> Plane:
        return self.web_bottom.offset(self.wall)

    @property
    def hub_radius(self) -> float:
        return SHAFT_RADIUS + 2 * self.wall

    def turned(self, sectors: int) -> Location:
        return Rot(Z=sectors * self.sector)

    @property
    def wall_spots(self) -> list[Location]:
        middle = (self.pocket_start + self.pocket_reach) / 2
        start = -90 + self.sector / 2
        return PolarLocations(middle, self.sectors, start_angle=start).locations

    @property
    def plate_spots(self) -> list[Location]:
        reach = self.inside_radius - self.screw_land
        corners = PolarLocations(reach, PLATE_SCREWS, start_angle=PLATE_SCREWS_START).locations
        return [Location(self.plate_bosses) * Pos(at.position) for at in corners]

    @property
    def feet_at(self) -> list[Location]:
        reach = self.plate_radius - models.BUMPER_DIAMETER
        corners = PolarLocations(reach, FEET, start_angle=FEET_START).locations
        return [Location(Plane.XY) * Pos(at.position) for at in corners]

    @property
    def drawer_width(self) -> float:
        return self.pull_width + 2 * self.wall

    @property
    def tray_back(self) -> float:
        return -self.pocket_start

    @property
    def drawer_back(self) -> float:
        return self.tray_back + 2 * self.wall + models.REED_WIDTH

    @property
    def drawer_front(self) -> float:
        return -self.radius

    @property
    def drawer_travel(self) -> float:
        return self.drawer_back - self.drawer_front

    @property
    def drawer_way(self) -> Location:
        return Location(Plane(self.drawer_bottom.origin, x_dir=(1, 0, 0), z_dir=(0, -1, 0)))

    @property
    def guide_x(self) -> float:
        return self.drawer_width / 2 + self.fits.sliding + self.wall / 2

    @property
    def actuator_at(self) -> Location:
        middle = (self.tray_back + self.drawer_back) / 2
        return Location(self.drawer_top) * Pos(Y=middle, Z=-models.REED_HEIGHT)

    @property
    def reed_spots(self) -> list[Location]:
        y = self.reed_at.position.Y
        pitch = models.REED_HOLE_PITCH / 2
        return [Location(self.floor_under) * Pos(X=x, Y=y) for x in (-pitch, pitch)]

    @property
    def reed_at(self) -> Location:
        return Location(self.floor_under) * Pos(Y=self.actuator_at.position.Y) * UPSIDE_DOWN

    @property
    def light_at(self) -> Location:
        middle = self.drawer_top.offset(self.fits.sliding + self.light_band / 2)
        return Location(middle) * Pos(Y=-self.radius)

    @property
    def flange_at(self) -> float:
        return -self.radius + models.LED_HEIGHT - models.LED_FLANGE_THICKNESS

    @cached_property
    def led_at(self) -> Location:
        tip = vendor_extent(LED).min.X
        middle = led_axis().position
        return self.light_at * Rot(Z=90) * Pos(X=-tip, Y=-middle.Y, Z=-middle.Z)

    @property
    def buzzer_spot(self) -> Location:
        return Location(self.plate_bottom) * Pos(Y=self.stepper_reach + models.BUZZER_DIAMETER)

    @cached_property
    def stepper_reach(self) -> float:
        return stepper_shaft().position.Y - vendor_extent(STEPPER).min.Y

    @cached_property
    def buzzer_at(self) -> Location:
        return self.buzzer_spot * Rot(X=-90) * Pos(Y=-vendor_extent(BUZZER).max.Y)

    @property
    def standoff(self) -> float:
        inserted = insert_size(self.pico_screw, fits=self.fits, stock=self.stock).length
        return inserted + self.fits.min_wall

    @property
    def driver_standoff(self) -> float:
        inserted = insert_size(self.driver_screw, fits=self.fits, stock=self.stock).length
        return inserted + self.fits.min_wall

    @cached_property
    def pico_mount(self) -> BoardMount:
        return board_mount(PICO, self.pico_screw, PICO_HOLES)

    @cached_property
    def driver_mount(self) -> BoardMount:
        return board_mount(DRIVER, self.driver_screw, DRIVER_HOLES)

    @cached_property
    def pico_at(self) -> Location:
        mouth = vendor_extent(PICO).max.Y
        back = self.inside_radius - self.fits.sliding - mouth
        hung = Location(self.floor_under) * Pos(Y=back, Z=-self.standoff) * END_FOR_END
        return hung * Pos(Z=-self.pico_mount.board_bottom)

    @property
    def driver_at(self) -> Location:
        aside = -self.pocket_start
        hung = Location(self.floor_under) * Pos(X=aside, Y=-aside, Z=-self.driver_standoff)
        return hung * UPSIDE_DOWN

    @property
    def usb_keepout(self) -> KeepOut:
        connector_middle = self.pico_mount.board_top + self.pico_mount.parts_above / 2
        mouth = self.pico_at * Pos(Y=vendor_extent(PICO).max.Y, Z=connector_middle)
        depth = self.radius + self.plug_reach - mouth.position.Y
        at = Pos(mouth.position) * Pos(Y=depth / 2, Z=-self.plug_height / 2)
        return KeepOut(
            block=Block(at=at, width=self.plug_width, depth=depth, height=self.plug_height),
            why="The power plug reaches the Pico's port through the back wall",
        )

    @property
    def cable_exit(self) -> Location:
        keepout = self.usb_keepout.block
        return keepout.at * Pos(Y=keepout.depth / 2, Z=keepout.height / 2)

    @property
    def cable_on_counter(self) -> Location:
        exit = self.cable_exit
        return Location(Plane.XY) * Pos(X=exit.position.X, Y=exit.position.Y + self.cable_run)

    @property
    def envelope(self) -> Envelope:
        return Envelope(
            block=Block(
                at=Location(),
                width=2 * self.radius,
                depth=2 * self.radius,
                height=self.top.origin.Z,
            ),
            why="The closed drum at rest (S2)",
        )


MASTER = DispenserMaster()
