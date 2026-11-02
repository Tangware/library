from dataclasses import dataclass

from build123d import Axis, BoundBox, Location, Plane, Pos, Rot
from cad.design.master import Master, Pose, given
from cad.library.bought.catalogue import STEEL, Catalogue, Cleanup, Download
from cad.library.bought.query import planes
from cad.library.bought.vendor import solids_of, vendor_extent, vendor_reach
from cad.library.features.planes import line_between
from cad.library.fits import FITS_UNITS, STAINLESS_A2_70, Fits
from cad.library.printing import PRINT_SETTINGS_UNITS, PrintSettings
from cad.library.standard.fasteners import STOCK_UNITS, Metric, Stock, clearance, insert_size
from cad.standards import RatedTorque

from octopus.models import battery_holder, cell, motor, switch

ESTIMATE = "estimate"
LOOK = "docs/octopus.gif of github.com/elvarofficial/teardown, read by eye 2026-11-01"
MOTOR_PAGE = "https://www.pololu.com/product/3069"
MOTOR_ZIP = "https://www.pololu.com/file/0J2042/Pololu%20Micro%20Metal%20Gearmotor%203D%20(STEP)%20Models.zip"
MOTOR_SHAFT = 9.0
MOTOR_SHAFT_DIAMETER = 3.0
MOTOR_SHAFT_FLAT = 0.5
STALL_SOURCE = "Pololu #3069 specs, 3.4 kg-cm at 6 V, theoretical"
MOTOR_STEP = Download(
    url=MOTOR_ZIP,
    sha256="203cec51bb3c7537266c230459960bd4a061e18f3619b9e0358805bf63a08652",
    member="No Encoder/mmgm-cb.step",
)
MOTOR = Catalogue(
    file="pololu_mmgm_cb_body",
    grams=motor.BODY_GRAMS_ESTIMATED,
    download=MOTOR_STEP,
    cleanup=Cleanup(correct=motor.body),
    torque=RatedTorque(nm=0.333, source=STALL_SOURCE),
)
MOTOR_OUTPUT = Catalogue(
    file="pololu_mmgm_cb_shaft",
    grams=motor.SHAFT_GRAMS_ESTIMATED,
    download=MOTOR_STEP,
    cleanup=Cleanup(correct=motor.shaft),
)
HOLDER_STEP = Download(
    url="https://www.memoryprotectiondevices.com/3D/download.php?pn=BC4AAW&id=1128",
    sha256="519a122d7cbe67743a60f53c39d0c0ae0a357e3c907473270d59d9688d3601b3",
)
BATTERY_HOLDER = Catalogue(
    file="mpd_bc4aaw",
    grams=battery_holder.GRAMS_ESTIMATED,
    download=HOLDER_STEP,
    frame=Plane(origin=(0.0, 0.0, 0.0), x_dir=(1.0, 0.0, 0.0), z_dir=(0.0, 1.0, 0.0)),
    cleanup=Cleanup(centred=True, correct=battery_holder.without_leads),
)
SWITCH = Catalogue(
    file="e_switch_rd11131121",
    grams=switch.GRAMS_ESTIMATED,
    download=Download(
        url="https://configured-product-images.s3.amazonaws.com/stp3dmodels/RD111x1121.stp",
        sha256="859448e73c12301613201f681d6fafb3808db4bfabf7075e29ba1eea382e606a",
    ),
)
CELL = Catalogue(
    file="energizer_e91", grams=cell.GRAMS, model=cell.solid, cleanup=Cleanup(colour=STEEL)
)
CELLS = 4
ARMS = range(8)
SEGMENTS = (1, 2, 3, 4)
RODS = (1, 2, 3)
ARM_STEP_DEG = 45.0
POSE_COUNT = 8
UP = (0.0, 0.0, 1.0)
ACROSS = (0.0, 1.0, 0.0)
OUTWARD = (1.0, 0.0, 0.0)
MANTLE_SPOTS_DEG = (0.0, 90.0, 150.0, 270.0)
LOW_ARMS = (0, 2, 4, 6)
HIGH_ARMS = (1, 3, 5, 7)


def is_low(arm: int) -> bool:
    return arm in LOW_ARMS


def crank_joint(arm: int) -> str:
    return f"arm {arm + 1} crank"


@dataclass(frozen=True)
class OctopusMaster(Master):
    lengths: tuple[float, ...] = given(
        (26.0, 24.0, 22.0, 17.0), "mm", why="Segments, tapering outward", source=LOOK
    )
    root_x: float = given(68.0, "mm", why="First hinge off the body's axis", source=ESTIMATE)
    body_height: float = given(110.0, "mm", why="Arms clear the desk when curled", source=ESTIMATE)
    layer: float = given(5.0, "mm", why="Each layer of the arm's stack", source=ESTIMATE)
    offset: float = given(4.0, "mm", why="Rod anchor above a tip hinge", source=ESTIMATE)
    low_offset: float = given(
        7.0, "mm", why="Rod anchor below a root hinge, so the linkage turns on", source=ESTIMATE
    )
    lever: float = given(14.0, "mm", why="First segment's drive lever", source=ESTIMATE)
    high_lever: float = given(
        10.0, "mm", why="Square to the longer rod of a high motor", source=ESTIMATE
    )
    crank_throw: float = given(6.0, "mm", why="Swings an arm a quarter radian", source=ESTIMATE)
    crank_lean_deg: float = given(
        20.0, "deg", why="Rest off the rod's dead centre", source=ESTIMATE
    )
    motor_x: float = given(44.0, "mm", why="Ring of eight motors", source=ESTIMATE)
    low_motor_z: float = given(
        18.0, "mm", why="Motors of the odd arms, on the deck", source=ESTIMATE
    )
    high_motor_z: float = given(
        44.0,
        "mm",
        why="Motors of the even arms, clear of their neighbours' cranks",
        source=ESTIMATE,
    )
    drum: float = given(8.0, "mm", why="Arm segment's radius at the root", source=LOOK)
    tip: float = given(4.0, "mm", why="Arm's last radius", source=LOOK)
    eye: float = given(3.5, "mm", why="Round a stub pin's hole", source=ESTIMATE)
    pin_diameter: float = given(3.0, "mm", why="Stub pins", source=ESTIMATE)
    sucker_radius: float = given(2.5, "mm", why="Suckers under a segment", source=LOOK)
    deck_thickness: float = given(6.0, "mm", why="Deck", source=ESTIMATE)
    deck_radius: float = given(60.0, "mm", why="Past the first hinge", source=ESTIMATE)
    stem_radius: float = given(16.0, "mm", why="Body's stem", source=ESTIMATE)
    foot_radius: float = given(60.0, "mm", why="Stands the body up", source=ESTIMATE)
    foot_thickness: float = given(5.0, "mm", why="Foot", source=ESTIMATE)
    saddle_wall: float = given(2.5, "mm", why="Round a motor", source=ESTIMATE)
    cap_thickness: float = given(5.0, "mm", why="Motor cap", source=ESTIMATE)
    shelf_z: float = given(56.0, "mm", why="Over the high motors", source=ESTIMATE)
    shelf_thickness: float = given(6.0, "mm", why="Battery shelf", source=ESTIMATE)
    shelf_radius: float = given(80.0, "mm", why="Carries the mantle's flange", source=ESTIMATE)
    flange_spot: float = given(75.5, "mm", why="Mantle screws, outside the dome", source=ESTIMATE)
    flange_radius: float = given(79.0, "mm", why="Past the dome", source=ESTIMATE)
    mantle_radius: float = given(72.0, "mm", why="Domes over the holder", source=LOOK)
    mantle_wall: float = given(3.0, "mm", why="Hollow printed shell", source=ESTIMATE)
    flange: float = given(5.0, "mm", why="Mantle's seat", source=ESTIMATE)
    eye_radius: float = given(16.0, "mm", why="Eye ring", source=LOOK)
    eye_depth: float = given(4.0, "mm", why="Eye ring", source=LOOK)
    eye_tilt_deg: float = given(35.0, "deg", why="Eyes apart", source=LOOK)
    siphon_radius: float = given(6.0, "mm", why="Siphon", source=LOOK)
    siphon_length: float = given(20.0, "mm", why="Siphon", source=LOOK)
    beak_radius: float = given(14.0, "mm", why="Beak under the deck", source=LOOK)
    beak_length: float = given(12.0, "mm", why="Beak under the deck", source=LOOK)
    lead_turn: float = given(12.0, "mm", why="Lead's last turn, under the rods", source=ESTIMATE)
    lead_clear: float = given(10.0, "mm", why="Past the next arm's drive rod", source=ESTIMATE)
    lead_rise: float = given(16.0, "mm", why="Over the holder", source=ESTIMATE)
    switch_panel: float = given(
        2.0,
        "mm",
        why="Within the switch's panel range, so its clips hold",
        source="E-Switch RD11131100 drawing, suggested panel cutout",
    )
    screw: Metric = given(Metric.M3, "-", why="One screw type", source="ISO 4762")
    short_screw: float = given(
        10.0, "mm", why="Through a cap or the shelf", source="ISO 4762 nominal lengths"
    )
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
            bridge=10.0,
            print_volume=(250.0, 210.0, 220.0),
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
            inserts={Metric.M3: "M3-0.5-5.7"},
            insert_maker="CNCKitchen",
            screw_lengths={},
            fastener_grade=STAINLESS_A2_70,
        ),
        STOCK_UNITS,
        why="CNC Kitchen heat-set inserts where a screw must hold fast",
        source="bd_warehouse HeatSetNut data, CNC Kitchen store listings",
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
        source="estimate: the library's example structural preset",
    )

    @property
    def pivot_bore(self) -> float:
        return clearance(self.screw, fits=self.fits)

    @property
    def insert_length(self) -> float:
        return insert_size(self.screw, fits=self.fits, stock=self.stock).length

    @property
    def thin(self) -> float:
        return self.layer - 2 * self.fits.sliding

    @property
    def stub_hole(self) -> float:
        return self.fits.printed(self.pin_diameter)

    def arm_frame(self, arm: int) -> Location:
        return Location((0.0, 0.0, self.body_height)) * Rot(Z=arm * ARM_STEP_DEG)

    def hinge_x(self, k: int) -> float:
        return self.root_x + sum(self.lengths[: k - 1])

    def plane_y(self, order: int) -> float:
        return (order - 0.5) * self.layer

    def segment_y(self, k: int) -> float:
        return self.plane_y(1) if k % 2 else self.plane_y(0)

    def rod_y(self, k: int) -> float:
        return self.plane_y(2) if k % 2 == 0 else self.plane_y(-1)

    def spot(self, arm: int, x: float, y: float, z: float) -> Location:
        return self.arm_frame(arm) * Pos(X=x, Y=y, Z=z) * Rot(X=-90.0)

    def hinge(self, arm: int, k: int, y: float, z: float = 0.0) -> Location:
        return self.spot(arm, self.hinge_x(k), y, z)

    def segment_frame(self, arm: int, k: int) -> Location:
        return self.hinge(arm, k, self.segment_y(k))

    def forward(self, arm: int) -> Axis:
        frame = self.arm_frame(arm)
        return Axis(frame.position, frame.y_axis.direction)

    def rod_frame(self, arm: int, k: int) -> Location:
        y = self.rod_y(k)
        low = self.hinge(arm, k, y, self.offset)
        high = self.hinge(arm, k + 1, y, -self.low_offset)
        return Location(
            Plane(
                origin=low.position, x_dir=high.position - low.position, z_dir=low.z_axis.direction
            )
        )

    def rod_length(self, k: int) -> float:
        return (self.lengths[k - 1] ** 2 + (self.offset + self.low_offset) ** 2) ** 0.5

    @property
    def crank_y(self) -> float:
        return self.plane_y(2)

    @property
    def drive_rod_y(self) -> float:
        return self.plane_y(3)

    def motor_z(self, arm: int) -> float:
        return self.low_motor_z if is_low(arm) else self.high_motor_z

    def motor_axis(self, arm: int) -> Location:
        return self.spot(arm, self.motor_x, self.crank_y, self.motor_z(arm))

    def crank_pin(self, arm: int) -> Location:
        return self.motor_axis(arm) * Rot(Z=self.crank_lean_deg) * Pos(Y=-self.crank_throw)

    def lever_out(self, arm: int) -> float:
        return 0.0 if is_low(arm) else self.high_lever

    def lever_up(self, arm: int) -> float:
        return self.lever if is_low(arm) else self.high_lever

    def lever_pin(self, arm: int, y: float) -> Location:
        return self.spot(arm, self.root_x + self.lever_out(arm), y, self.lever_up(arm))

    def drive_rod_frame(self, arm: int) -> Location:
        y = self.drive_rod_y
        pin = self.crank_pin(arm)
        at = self.arm_frame(arm).inverse() * pin
        low = self.spot(arm, at.position.X, y, at.position.Z)
        high = self.lever_pin(arm, y)
        return Location(
            Plane(
                origin=low.position, x_dir=high.position - low.position, z_dir=low.z_axis.direction
            )
        )

    def drive_rod_length(self, arm: int) -> float:
        return line_between(self.drive_rod_frame(arm), self.lever_pin(arm, self.drive_rod_y)).length

    @property
    def motor_width(self) -> float:
        return vendor_extent(MOTOR).size.X

    @property
    def motor_height(self) -> float:
        return vendor_extent(MOTOR).size.Y

    @property
    def motor_length(self) -> float:
        return motor.SHAFT_START - vendor_extent(MOTOR).min.Z

    def motor_tip(self, arm: int) -> Location:
        return self.motor_axis(arm) * Pos(Z=self.thin / 2)

    def drive_frame(self, arm: int) -> Location:
        at = self.motor_axis(arm)
        return Location(
            Plane(
                origin=at.position,
                x_dir=self.arm_frame(arm).z_axis.direction,
                z_dir=self.arm_frame(arm).y_axis.direction,
            )
        )

    def motor_at(self, arm: int) -> Location:
        return self.drive_frame(arm) * Pos(Z=self.thin / 2 - vendor_reach(MOTOR_OUTPUT, Axis.Z))

    @property
    def saddle_y(self) -> float:
        return self.crank_y - MOTOR_SHAFT - self.thin / 2

    @property
    def saddle_length(self) -> float:
        return 2 * self.motor_length / 3

    @property
    def saddle_width(self) -> float:
        return self.motor_height + 2 * self.fits.sliding + 4 * self.saddle_wall

    @property
    def saddle_floor(self) -> float:
        return -self.deck_thickness / 2

    def saddle_open(self, arm: int) -> float:
        half = self.motor_width / 2
        return self.low_motor_z + half if is_low(arm) else self.high_motor_z - half

    def saddle_bed(self, arm: int) -> float:
        return self.saddle_floor if is_low(arm) else self.shelf_z

    @property
    def window_width(self) -> float:
        return self.saddle_width + 2 * self.saddle_wall

    @property
    def window_length(self) -> float:
        return self.motor_length + self.crank_y - self.saddle_y + 2 * self.eye + 2 * self.eye

    def saddle_window(self, arm: int) -> Location:
        z = self.shelf_z if is_low(arm) else self.saddle_floor - self.deck_thickness
        y = (self.crank_y + self.saddle_y - self.motor_length) / 2
        return self.arm_frame(arm) * Pos(X=self.motor_x, Y=y, Z=z)

    def saddle_window_depth(self, arm: int) -> float:
        return self.shelf_thickness if is_low(arm) else self.deck_thickness

    def saddle_bed_depth(self, arm: int) -> float:
        return abs(self.saddle_open(arm) - self.saddle_bed(arm))

    def saddle_at(self, arm: int) -> Location:
        turned = Location() if is_low(arm) else Rot(X=180.0)
        return (
            self.arm_frame(arm)
            * Pos(X=self.motor_x, Y=self.saddle_y - self.saddle_length / 2, Z=self.saddle_open(arm))
            * turned
        )

    def saddle_spots(self, arm: int) -> tuple[Location, ...]:
        off = self.motor_height / 2 + self.saddle_wall + self.fits.sliding
        return tuple(self.saddle_at(arm) * Pos(X=side * off) for side in (-1.0, 1.0))

    @property
    def seat_height(self) -> float:
        return self.body_height + self.shelf_z + self.shelf_thickness

    @property
    def mantle_seat(self) -> Location:
        return Location((0.0, 0.0, self.seat_height))

    @property
    def mantle_spots(self) -> tuple[Location, ...]:
        return tuple(
            self.mantle_seat * Rot(Z=deg) * Pos(X=self.flange_spot) for deg in MANTLE_SPOTS_DEG
        )

    @property
    def holder_at(self) -> Location:
        return self.mantle_seat * Rot(Z=self.switch_turn - 180.0)

    @property
    def holder_box(self) -> BoundBox:
        return vendor_extent(BATTERY_HOLDER)

    @property
    def holder_floor(self) -> float:
        return min(face.center().Z for face in planes(solids_of(BATTERY_HOLDER), Axis.Z.direction))

    @property
    def cell_spots(self) -> tuple[Location, ...]:
        pitch = self.holder_box.size.Y / CELLS
        lift = self.holder_floor + cell.DIAMETER / 2
        return tuple(
            self.holder_at
            * Pos(X=-cell.LENGTH / 2, Y=(k - (CELLS - 1) / 2) * pitch, Z=lift)
            * Rot(Y=90.0)
            for k in range(CELLS)
        )

    @property
    def switch_seat(self) -> float:
        return vendor_reach(SWITCH, Axis.Z) - switch.ABOVE_THE_PANEL

    @property
    def switch_depth(self) -> float:
        return self.switch_seat + vendor_reach(SWITCH, -Axis.Z)

    @property
    def switch_cutout(self) -> float:
        return switch.cutout_length(self.switch_panel)

    @property
    def switch_at(self) -> Location:
        return self.switch_face * Pos(Z=-self.switch_seat)

    @property
    def switch_terminals(self) -> Location:
        return Location((self.switch_face * Pos(Z=-self.switch_depth)).position)

    @property
    def holder_leads_out(self) -> Location:
        end = self.holder_at * Pos(X=-self.holder_box.size.X / 2, Z=self.holder_box.size.Z / 2)
        return Location(end.position)

    @property
    def switch_turn(self) -> float:
        _, side, back, _ = MANTLE_SPOTS_DEG
        return (side + back) / 2

    @property
    def switch_face(self) -> Location:
        over_the_flange = self.flange + switch.BEZEL_WIDTH / 2 + self.fits.sliding
        inside = self.mantle_radius - self.mantle_wall
        return (
            self.mantle_seat
            * Rot(Z=self.switch_turn)
            * Location(Plane(origin=(inside, 0.0, over_the_flange), x_dir=ACROSS, z_dir=OUTWARD))
        )

    @property
    def recess_length(self) -> float:
        return switch.BEZEL_LENGTH + 2 * self.fits.sliding

    @property
    def recess_width(self) -> float:
        return switch.BEZEL_WIDTH + 2 * self.fits.sliding

    def lead_hole(self, arm: int) -> Location:
        y = self.saddle_y - self.motor_length + 2 * self.eye
        out = self.lead_clear if is_low(arm) else 0.0
        return self.arm_frame(arm) * Pos(
            X=self.motor_x + out, Y=y, Z=self.shelf_z + self.shelf_thickness
        )

    def lead_up(self) -> Location:
        return self.holder_at * Pos(Z=self.holder_box.size.Z + self.lead_rise)

    def lead_over(self, arm: int) -> Location:
        top = (self.lead_hole(arm).inverse() * self.lead_up()).position.Z
        return self.lead_hole(arm) * Pos(Z=top)

    def lead_low(self, arm: int) -> Location:
        y = self.saddle_y - self.motor_length + 2 * self.eye
        return self.arm_frame(arm) * Pos(
            X=self.motor_x + self.lead_clear, Y=y, Z=self.motor_z(arm) + self.lead_turn
        )

    def lead_end(self, arm: int) -> Location:
        y = self.saddle_y - self.motor_length + 2 * self.eye
        side = self.motor_height / 2 + self.fits.structural_wall
        if is_low(arm):
            return self.arm_frame(arm) * Pos(X=self.motor_x + side, Y=y, Z=self.motor_z(arm))
        top = self.motor_z(arm) + self.motor_width / 2 + self.fits.sliding
        return self.arm_frame(arm) * Pos(X=self.motor_x, Y=y, Z=top)

    def wave_turn(self, arm: int, n: int) -> float:
        return n * ARM_STEP_DEG * (1 + arm / len(ARMS))

    def drum_at(self, k: int) -> float:
        share = (k - 1) / len(SEGMENTS)
        return self.drum + share * (self.tip - self.drum)

    @property
    def lug_foot(self) -> float:
        return -self.saddle_floor

    @property
    def poses(self) -> tuple[Pose, ...]:
        return tuple(
            Pose(
                name=f"wave at {n * ARM_STEP_DEG:g}",
                joints={crank_joint(arm): self.wave_turn(arm, n) for arm in ARMS},
            )
            for n in range(POSE_COUNT)
        )


MASTER = OctopusMaster()
