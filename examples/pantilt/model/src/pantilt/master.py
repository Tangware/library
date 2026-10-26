from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from build123d import Axis, GridLocations, Location, Locations, Plane, PolarLocations, Pos
from cad.design.master import Envelope, KeepOut, Master, Pose, given
from cad.library.bought.boards import BoardMount, board_mount
from cad.library.bought.catalogue import BoardKind, Catalogue, Download, Piece
from cad.library.bought.query import LENGTH_TOLERANCE, exactly
from cad.library.bought.vendor import piece, solids_of, vendor_extent
from cad.library.extension_spring import Spring
from cad.library.features.planes import halfway
from cad.library.fits import FITS_UNITS, Fits, STAINLESS_A2_70
from cad.library.mates import JointRange
from cad.library.printing import PRINT_SETTINGS_UNITS, PrintSettings
from cad.library.shapes import Block
from cad.library.standard.fasteners import (
    STOCK_UNITS,
    Ends,
    Metric,
    Stock,
    counterbore_radius,
    head_height,
    insert_size,
    screw_length,
)
from cad.library.turns import AGAINST_X, ALONG_X, ANTICLOCKWISE_QUARTER, HALF_TURN

from pantilt.models import stepper

ARM_HOLE_DEG = 70.0
CLIPS_DEG = 140.0
LID_HOLE_DEG = 210.0
LID_SCREWS_FROM_DEG = 240.0
LID_SCREWS_SPREAD_DEG = 60.0
DEGREES = {"low": "deg", "high": "deg"}
SPRING_UNITS = {
    "part": "-",
    "wire": "mm",
    "outer_diameter": "mm",
    "free_length": "mm",
    "rate": "N/mm",
    "preload": "N",
    "rated_force": "N",
    "rated_stretch": "mm",
    "hook_pin": "mm",
}
VENDOR = Path(__file__).parents[2] / "vendor"
DRIVER = Catalogue(file="adafruit_6121_tmc2209", grams=4.4, folder=VENDOR, kind=BoardKind())
USB_C_BOARD = Catalogue(file="adafruit_4090_usb_c", grams=1.3, folder=VENDOR, kind=BoardKind())
XIAO_GRAMS_ESTIMATED = 5.0
CAMERA_BOARD = Catalogue(
    file="seeed_xiao_esp32s3_sense",
    grams=XIAO_GRAMS_ESTIMATED,
    download=Download(
        url="https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/seeed-studio-xiao-esp32s3-sense-3d_model.zip",
        sha256="a37c6b41d5660cd3310fea05edde0238762fe00da4de623936b7ca66814cb698",
        member="Seeed Studio XIAO-ESP32-S3-Sense.step",
    ),
)
MOTOR_GRAMS = 140.0
MOTOR = Catalogue(
    file="17hs08_1004s",
    grams=MOTOR_GRAMS,
    model=stepper.solid,
    pieces=(
        Piece(
            name=stepper.STATOR,
            grams=MOTOR_GRAMS - stepper.ROTOR_GRAMS_ESTIMATED,
            component=stepper.STATOR,
        ),
        Piece(name=stepper.ROTOR, grams=stepper.ROTOR_GRAMS_ESTIMATED, component=stepper.ROTOR),
    ),
)
STATOR = piece(MOTOR, stepper.STATOR)
ROTOR = piece(MOTOR, stepper.ROTOR)
DRIVER_HOLES = 4
USB_C_HOLES = 2
PAN = "pan motor's rotor in its stator"
TILT = "tilt motor's rotor in its stator"
JAW = "jaw on cradle"
USB_C_SOURCE = "USB Type-C Cable and Connector Specification R2.0, plug overmold; not opened"


@dataclass(frozen=True)
class ProductMaster(Master):
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
        why="Print allowances for an FDM printer",
        source="estimate: the library's example fits, not calibrated on a PAHT-CF printer",
    )
    stock: Stock = given(
        Stock(
            inserts={Metric.M3: "M3-0.5-5.7", Metric.M2: "M2-0.4-3"},
            insert_maker="CNCKitchen",
            screw_lengths={},
            fastener_grade=STAINLESS_A2_70,
        ),
        STOCK_UNITS,
        why="CNC Kitchen heat-set inserts for every screw into a made part",
        source="bd_warehouse HeatSetNut data, CNC Kitchen store listings",
    )
    screw: Metric = given(
        Metric.M3,
        "-",
        why="One screw type; the motor faces are tapped M3",
        source=stepper.FACE_STANDARD,
    )
    board_screw: Metric = given(
        Metric.M2,
        "-",
        why="The driver and USB-C boards' mounting holes take M2",
        source="Adafruit 6121 and 4090 STEP files, holes queried by board_mount",
    )
    body_diameter: float = given(
        70.0,
        "mm",
        why="One diameter for the base, the arm's foot and the tilt drum (S2); "
        "clears the pan motor's diagonal and stays within the widest phone (S4)",
        source="design input, checked by test_s4",
    )
    narrowest_phone: float = given(60.0, "mm", why="R1", source="founder: 60-85 mm wide")
    widest_phone: float = given(85.0, "mm", why="R1", source="founder: 60-85 mm wide")
    longest_phone: float = given(
        170.0,
        "mm",
        why="The arm clears the end of the longest phone in landscape",
        source="estimate: a 163 mm flagship in a case",
    )
    thickest_phone: float = given(
        12.0, "mm", why="The cradle takes a phone in a case", source="estimate: 8 mm + case"
    )
    heaviest_phone_kg: float = given(
        0.27, "kg", why="R5", source="estimate: a 227 g flagship plus a case"
    )
    landed_cost_target_usd: float = given(
        100.0, "USD", why="R8", source="founder: target landed cost under $100 at 500 units"
    )
    landing_share: float = given(
        0.15,
        "-",
        why="Shipping and duties on top of the parts, as a share of their price",
        source="estimate: not quoted",
    )
    phone_middle: float = given(
        -40.0,
        "mm",
        why="The phone sits off the pan axis, away from the drum, so the stand's centre of "
        "mass stays over the base (R5)",
        source="estimate, checked by test_r5",
    )
    pan_range: JointRange = given(
        JointRange(low=-90.0, high=90.0), DEGREES, why="R2: a quarter turn each way", source="R2"
    )
    spring: Spring = given(
        Spring(
            part="LE 031C 05 S",
            wire=0.787,
            outer_diameter=6.1,
            free_length=38.1,
            rate=0.665,
            preload=3.11,
            rated_force=23.1,
            rated_stretch=30.1,
            hook_pin=0.0,
        ),
        SPRING_UNITS,
        why="Pulls the jaw down onto the phone's top edge (R1, R5)",
        source="Lee Spring LE-031C-5SS via the Olander listing (search summary, not opened): "
        "0.031 in wire, 1.500 in free, 0.7 lb initial tension, 3.8 lb/in, 5.20 lb max; "
        "outside diameter 0.240 in is an estimate",
    )
    spring_preload_stretch: float = given(
        2.0, "mm", why="The spring stays taut on the narrowest phone", source="estimate"
    )
    tilt_range: JointRange = given(
        JointRange(low=-15.0, high=30.0), DEGREES, why="R3: up a third, down a sixth", source="R3"
    )
    cable_bay: float = given(
        8.0,
        "mm",
        why="Flat cables run between the boards and the pan motor",
        source="estimate, checked by the cables check",
    )
    pan_slack: float = given(
        40.0,
        "mm",
        why="Slack in the arm's chamber for its quarter turn each way",
        source="estimate: the 32 mm between the arm's clip and the lid's clip at a pan limit, "
        "plus margin",
    )
    flat_cable_width: float = given(
        12.0,
        "mm",
        why="The flat cables through the arm and lid: the four-wire motor lead and the "
        "three-wire harness side by side",
        source="estimate: 4 x 1.0 mm and 3 x 1.4 mm wires plus clearance",
    )
    cable_clearance: float = given(
        8.0,
        "mm",
        why="A cable's centre line keeps this far from the faces it runs along",
        source="estimate: half the widest flat cable plus a millimetre",
    )
    wiring_room: float = given(
        3.0,
        "mm",
        why="Room for plugs and wires between a board and the part beside it",
        source="estimate: a 2.54 mm header plug",
    )
    tilt_clearance: float = given(
        5.0,
        "mm",
        why="The cradle clears the arm over the whole tilt range",
        source="estimate, checked by test_r3",
    )
    lip: float = given(
        5.0,
        "mm",
        why="How far the ledge and the jaw reach over the phone's edges",
        source="estimate: covers a phone's bezel, not its screen",
    )
    plug_width: float = given(12.35, "mm", why="USB-C plug overmold", source=USB_C_SOURCE)
    plug_height: float = given(6.5, "mm", why="USB-C plug overmold", source=USB_C_SOURCE)
    plug_reach: float = given(
        20.0, "mm", why="Room behind the base for a USB-C plug", source="design input"
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
        up = {PAN: self.pan_range.high, TILT: self.tilt_range.high}
        down = {PAN: self.pan_range.low, TILT: self.tilt_range.low}
        return (
            Pose(name="rest", joints={}),
            Pose(name="turned and looking up", joints=up),
            Pose(name="turned and looking down", joints=down),
        )

    @property
    def wall(self) -> float:
        return self.fits.structural_wall

    @property
    def radius(self) -> float:
        return self.body_diameter / 2

    @property
    def inside_radius(self) -> float:
        return self.radius - self.wall

    @property
    def screw_plate(self) -> float:
        return head_height(self.screw) + self.wall

    @cached_property
    def driver_mount(self) -> BoardMount:
        return board_mount(DRIVER, self.board_screw, DRIVER_HOLES)

    @cached_property
    def usb_mount(self) -> BoardMount:
        return board_mount(USB_C_BOARD, self.board_screw, USB_C_HOLES)

    @property
    def ground(self) -> Plane:
        return Plane.XY

    @property
    def floor(self) -> Plane:
        return self.ground.offset(self.wall)

    @property
    def standoff(self) -> float:
        insert = insert_size(self.board_screw, fits=self.fits, stock=self.stock)
        return insert.length + self.fits.min_wall

    def on_posts(self, mount: BoardMount, middle: Location) -> Location:
        centred = Pos(X=-mount.middle.position.X, Y=-mount.middle.position.Y)
        return Location(self.floor) * middle * Pos(Z=self.standoff - mount.board_bottom) * centred

    @property
    def drivers_at(self) -> list[Location]:
        half = self.driver_mount.length / 2 + self.wiring_room / 2
        return [
            self.on_posts(self.driver_mount, Pos(X=-half) * HALF_TURN),
            self.on_posts(self.driver_mount, Pos(X=half)),
        ]

    @property
    def usb_board_at(self) -> Location:
        middle = self.inside_radius - self.usb_mount.width / 2 - self.wall
        return self.on_posts(self.usb_mount, Pos(Y=middle) * HALF_TURN)

    @property
    def lid_screws(self) -> list[Location]:
        with Locations(Location(self.pan_flange)):
            return PolarLocations(
                self.inside_radius
                - counterbore_radius(self.screw, fits=self.fits)
                - self.fits.sliding,
                3,
                start_angle=LID_SCREWS_FROM_DEG,
                angular_range=LID_SCREWS_SPREAD_DEG,
                endpoint=True,
            ).locations

    @property
    def harness_at(self) -> Location:
        middle = (self.driver_mount.width / 2 + self.inside_radius) / 2
        return Location(self.floor) * Pos(Y=-middle)

    @property
    def driver_top(self) -> Plane:
        return self.floor.offset(self.standoff + vendor_extent(DRIVER).size.Z)

    @property
    def pan_flange(self) -> Plane:
        return self.driver_top.offset(self.cable_bay + stepper.BODY)

    @property
    def pan_motor_at(self) -> Location:
        return Location(self.pan_flange) * HALF_TURN

    @property
    def pan_motor_screws(self) -> list[Location]:
        with Locations(Location(self.pan_flange)):
            return GridLocations(stepper.HOLE_SPACING, stepper.HOLE_SPACING, 2, 2).locations

    @property
    def cable_slot_inner(self) -> float:
        corner = Pos(X=stepper.HOLE_SPACING / 2, Y=stepper.HOLE_SPACING / 2).position.length
        return corner + counterbore_radius(self.screw, fits=self.fits) + self.fits.min_wall

    @property
    def cable_slot_outer(self) -> float:
        return self.inside_radius - self.fits.min_wall

    @property
    def clamp_screw_length(self) -> float:
        insert = insert_size(self.screw, fits=self.fits, stock=self.stock)
        return screw_length(self.screw, insert.length, Ends.PAST, stock=self.stock)

    def clamp_spot(self, flange: Location) -> Location:
        flat = stepper.SHAFT_DIAMETER / 2 - stepper.FLAT_DEPTH
        engaged = Pos(Z=stepper.SHAFT_LENGTH - stepper.FLAT_LENGTH / 2)
        return flange * engaged * Pos(X=flat + self.clamp_screw_length) * ALONG_X

    @property
    def pan_clamp(self) -> Location:
        return self.clamp_spot(self.pan_motor_at)

    @property
    def tilt_clamp(self) -> Location:
        return self.clamp_spot(self.tilt_motor_at)

    @property
    def tilt_motor_screws(self) -> list[Location]:
        with Locations(self.tilt_motor_at):
            return GridLocations(stepper.HOLE_SPACING, stepper.HOLE_SPACING, 2, 2).locations

    @property
    def base_top(self) -> Plane:
        return self.pan_flange.offset(self.screw_plate)

    @property
    def arm_bottom(self) -> Plane:
        return self.base_top.offset(self.fits.sliding)

    @property
    def arm_top(self) -> Plane:
        return self.pan_flange.offset(stepper.SHAFT_LENGTH + self.wall)

    @property
    def cradle_bottom(self) -> Plane:
        return self.arm_top.offset(self.tilt_clearance)

    @property
    def camera_board(self) -> Block:
        extent = vendor_extent(CAMERA_BOARD)
        return Block(at=Location(), width=extent.size.X, depth=extent.size.Y, height=extent.size.Z)

    @property
    def camera_board_middle(self) -> Location:
        return Pos(vendor_extent(CAMERA_BOARD).center())

    @property
    def ledge(self) -> Plane:
        room = self.camera_board.height + 2 * self.fits.sliding
        return self.cradle_bottom.offset(room + 2 * self.wall)

    @property
    def phone_back(self) -> float:
        return self.thickest_phone / 2

    @property
    def phone_front(self) -> float:
        return -self.thickest_phone / 2

    @property
    def cradle_back(self) -> float:
        return self.phone_back + self.wall

    @property
    def cradle_front(self) -> float:
        return self.phone_front - self.wall

    @property
    def tilt_level(self) -> Plane:
        return self.ledge.offset((self.narrowest_phone + self.widest_phone) / 4)

    @property
    def tilt_height(self) -> float:
        return self.tilt_level.origin.Z

    @property
    def tilt_axis(self) -> Axis:
        return Axis((0, 0, self.tilt_height), (1, 0, 0))

    @property
    def hub_inside(self) -> float:
        return self.phone_middle + self.longest_phone / 2 + self.wall

    @property
    def hub_thickness(self) -> float:
        return stepper.SHAFT_LENGTH - self.screw_plate - self.fits.sliding + self.wall

    @property
    def column_inside(self) -> float:
        return self.hub_inside + self.hub_thickness + self.fits.sliding

    @property
    def tilt_flange(self) -> float:
        return self.column_inside + self.screw_plate

    @property
    def tilt_motor_at(self) -> Location:
        at = Location((self.tilt_flange, 0, self.tilt_height))
        return at * AGAINST_X * ANTICLOCKWISE_QUARTER

    @property
    def drum_rim(self) -> float:
        return self.tilt_flange + stepper.BODY + self.fits.sliding

    @property
    def drum_end(self) -> float:
        return self.drum_rim + self.screw_plate

    @property
    def cap_rim(self) -> Plane:
        return Plane(Location((self.drum_rim, 0, self.tilt_height)) * ALONG_X)

    @property
    def cap_screws(self) -> list[Location]:
        with Locations(Location(self.cap_rim)):
            return PolarLocations(self.drum_screw_radius, 4).locations

    @property
    def drum_screw_radius(self) -> float:
        return (stepper.FRAME / 2 + self.radius) / 2

    @property
    def phone_top(self) -> float:
        return self.ledge.origin.Z + self.widest_phone

    @property
    def jaw_length(self) -> float:
        return self.longest_phone / 2

    @property
    def jaw_thickness(self) -> float:
        return 2 * self.wall

    @property
    def jaw_travel(self) -> float:
        return self.widest_phone - self.narrowest_phone

    @property
    def jaw_range(self) -> JointRange:
        stretched = self.jaw_travel + self.spring_preload_stretch
        return JointRange(low=-self.jaw_travel, high=self.spring.rated_stretch - stretched)

    @property
    def stem_side(self) -> float:
        return self.spring.outer_diameter

    @property
    def guide_middle(self) -> float:
        return self.cradle_back + self.fits.sliding + self.spring.outer_diameter / 2

    @property
    def stem_at(self) -> Location:
        beside = (self.stem_side + self.fits.sliding) / 2
        return Location((self.phone_middle - beside, self.guide_middle, self.phone_top))

    @property
    def spring_lug_at(self) -> Location:
        beside = (self.stem_side + self.fits.sliding) / 2
        return Location((self.phone_middle + beside, self.guide_middle, self.phone_top))

    @property
    def spring_post_at(self) -> Location:
        span = self.spring.free_length + self.spring_preload_stretch + self.jaw_travel
        return self.spring_lug_at * Pos(Z=-span)

    @property
    def stem_length(self) -> float:
        floor = self.spring_post_at.position.Z + self.fits.sliding
        return self.phone_top - self.jaw_travel - floor

    @property
    def guide(self) -> Block:
        inside_left = self.stem_at.position.X - self.stem_side / 2 - self.fits.sliding
        inside_right = self.spring_lug_at.position.X + self.spring.outer_diameter / 2
        inside_right += self.fits.sliding
        bottom = self.spring_post_at.position.Z - self.wall
        depth = self.spring.outer_diameter + 2 * self.fits.sliding + self.wall
        return Block(
            at=Location(((inside_left + inside_right) / 2, self.cradle_back + depth / 2, bottom)),
            width=inside_right - inside_left + 2 * self.wall,
            depth=depth,
            height=self.back_plate_top.origin.Z - bottom,
        )

    @property
    def cable_points(self) -> dict[str, Location]:
        c = self.cable_clearance
        behind, low = self.radius + c, self.ledge.origin.Z + c
        column = self.column_inside + self.screw_plate / 2
        over_the_arm = self.arm_top.origin.Z + c
        slot = (self.cable_slot_inner + self.cable_slot_outer) / 2
        drum_middle = self.tilt_flange + stepper.BODY / 2
        chamber = self.chamber_middle.origin.Z
        inner = self.pan_hub_radius + self.flat_cable_width
        return {
            "behind the cradle": Location((self.hub_inside - c, self.cradle_back + c, low)),
            "behind the tilt hub": Location((self.hub_inside - c, behind, low)),
            "behind the drum": Location((drum_middle, behind, self.tilt_height)),
            "behind the column": Location((column, behind, self.tilt_height)),
            "behind the leg": Location((column, behind, over_the_arm)),
            "over the arm's cable hole": self.chamber_at(slot, ARM_HOLE_DEG, over_the_arm),
            "under the arm's cable hole": self.chamber_at(slot, ARM_HOLE_DEG, chamber),
            "on the arm's clip": self.chamber_at(slot, CLIPS_DEG, chamber),
            "on the lid's clip": self.chamber_at(inner, CLIPS_DEG, chamber),
            "over the lid's hole": self.lid_hole * Pos(Z=chamber - self.pan_flange.origin.Z),
            "under the lid": self.lid_hole * Pos(Z=-c),
            "in the cable bay": self.lid_hole
            * Pos(Z=self.driver_top.origin.Z + self.cable_bay / 2 - self.pan_flange.origin.Z),
        }

    @property
    def cable_way(self) -> float:
        return self.cable_slot_outer - self.cable_slot_inner

    @property
    def board_plugs(self) -> dict[str, Location]:
        driver, usb, camera = (vendor_extent(each) for each in (DRIVER, USB_C_BOARD, CAMERA_BOARD))
        over = self.cable_bay / 2
        return {
            "driver header": Pos(X=driver.center().X, Y=driver.center().Y, Z=driver.max.Z + over),
            "driver terminal": Pos(X=driver.max.X, Y=driver.center().Y, Z=driver.max.Z + over),
            "USB-C pins": Pos(X=usb.center().X, Y=usb.center().Y, Z=usb.max.Z + over),
            "camera pins": Pos(
                X=camera.center().X, Y=camera.min.Y - self.cable_clearance, Z=camera.center().Z
            ),
            "motor lead": Pos(X=stepper.FRAME / 2, Z=-stepper.BODY / 2),
        }

    @property
    def drum_lead_hole(self) -> Location:
        drum_middle = self.tilt_flange + stepper.BODY / 2
        return Location((drum_middle, stepper.FRAME / 2, self.tilt_height))

    @property
    def pan_hub_radius(self) -> float:
        flat = stepper.SHAFT_DIAMETER / 2 - stepper.FLAT_DEPTH
        return flat + self.clamp_screw_length + self.wall

    @property
    def chamber_top(self) -> Plane:
        return self.arm_top.offset(-self.wall)

    @property
    def chamber_middle(self) -> Plane:
        return halfway(self.arm_bottom, self.chamber_top)

    def chamber_at(self, radius: float, angle: float, height: float) -> Location:
        with Locations(Location((0, 0, height))):
            (found,) = PolarLocations(radius, 1, start_angle=angle).locations
        return found * ANTICLOCKWISE_QUARTER

    @property
    def lid_hole(self) -> Location:
        slot = (self.cable_slot_inner + self.cable_slot_outer) / 2
        with Locations(Location(self.pan_flange)):
            (found,) = PolarLocations(slot, 1, start_angle=LID_HOLE_DEG).locations
        return found * ANTICLOCKWISE_QUARTER

    @property
    def tilt_loop(self) -> float:
        return 2 * self.radius

    @property
    def pan_loop(self) -> float:
        return self.pan_slack

    @property
    def back_plate_top(self) -> Plane:
        return self.ledge.offset(self.narrowest_phone - self.lip)

    @cached_property
    def camera_module(self) -> Block:
        extent = vendor_extent(CAMERA_BOARD)
        (camera,) = exactly(
            [
                solid
                for solid in solids_of(CAMERA_BOARD)
                if abs(solid.bounding_box().max.Y - extent.max.Y) <= LENGTH_TOLERANCE
            ],
            1,
            "camera modules at the front of the XIAO",
        )
        box = camera.bounding_box()
        middle = box.center()
        return Block(
            at=Pos(X=middle.X, Z=middle.Z), width=box.size.X, depth=box.size.Y, height=box.size.Z
        )

    @property
    def lens(self) -> Location:
        return self.camera_module.at

    @property
    def camera_at(self) -> Location:
        extent = vendor_extent(CAMERA_BOARD)
        window = self.cradle_front + self.fits.sliding
        bottom = self.cradle_bottom.origin.Z + self.wall + self.fits.sliding
        to_the_lens = Pos(X=-self.lens.position.X, Y=-extent.max.Y, Z=-extent.min.Z)
        return Pos(X=self.phone_middle, Y=window, Z=bottom) * HALF_TURN * to_the_lens

    @property
    def phone(self) -> KeepOut:
        block = Block(
            at=Location((self.phone_middle, 0, self.ledge.origin.Z)),
            width=self.longest_phone,
            depth=self.thickest_phone,
            height=self.widest_phone,
        )
        return KeepOut(block=block, why="The largest phone sits here at rest")

    @property
    def usb_plug(self) -> KeepOut:
        port = self.usb_board_at.position
        at = Location((0, self.radius + self.plug_reach / 2, port.Z))
        block = Block(at=at, width=self.plug_width, depth=self.plug_reach, height=self.plug_height)
        return KeepOut(block=block, why="A USB-C plug reaches the port through the base's back")

    @property
    def envelope(self) -> Envelope:
        block = Block(
            at=Location(),
            width=2 * self.drum_end,
            depth=self.body_diameter,
            height=self.tilt_height + self.radius,
        )
        return Envelope(block=block, why="The stand at rest, without the phone")


MASTER = ProductMaster()
