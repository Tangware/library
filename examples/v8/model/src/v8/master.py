from dataclasses import dataclass
from enum import StrEnum

from build123d import Axis, BoundBox, Edge, Location, Plane, Pos, Rot, Triangle
from cad.design.master import Master, Pose, given
from cad.library.bought.catalogue import Catalogue, Cleanup, Download
from cad.library.bought.query import planes
from cad.library.bought.vendor import solids_of, vendor_extent, vendor_reach
from cad.library.features.planes import line_between, line_through
from cad.library.fits import FITS_UNITS, STAINLESS_A2_70, Fits
from cad.library.gears import mesh_phase, pitch_radius
from cad.library.printing import PRINT_SETTINGS_UNITS, PrintSettings
from cad.library.standard.fasteners import STOCK_UNITS, Metric, Stock, clearance, insert_size
from cad.library.turns import turn_to
from cad.standards import RatedTorque

from v8.models import battery_holder, cell, motor, sleeve, switch, wire

CRANK = "crank"
INCH = 25.4
SPECS = "Chevrolet 350 specifications, speedwaymotors.com and JEGS tech pages, searched 2026-11-01"
FORUM = "bore spacing 4.40 in: one forum thread only, no maker source found"
ESTIMATE = "estimate"
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
    file="energizer_en91", grams=cell.GRAMS, model=cell.solid, cleanup=Cleanup(colour=cell.LABEL)
)
SLEEVE = Catalogue(
    file="te_rnf_100_3_32",
    grams=sleeve.GRAMS_ESTIMATED,
    model=sleeve.solid,
    cleanup=Cleanup(colour=sleeve.COLOUR),
)
CELLS = 4
ALONG = (1.0, 0.0, 0.0)
ACROSS = (0.0, 1.0, 0.0)
OUT_OF_THE_END = (-1.0, 0.0, 0.0)
TOWARD_THE_FRONT = (0.0, -1.0, 0.0)
LEFT_BANK_DEG = 45.0
RIGHT_BANK_DEG = -45.0
JOURNAL_PHASES_DEG = (45.0, 135.0, -45.0, -135.0)
FIRING_ORDER = (1, 8, 4, 3, 6, 5, 7, 2)
FIRING_STEP_DEG = 90.0
POSE_STEP_DEG = 45.0
REST_TURN_DEG = 22.5
POSE_COUNT = 16
EXHAUST_PEAK_DEG = 250.0
INTAKE_PEAK_DEG = 460.0
VALVE_SIDES = (-1.0, 1.0)
HEAD_SPOTS = (-1.0, 0.0, 1.0)
POSTS = (-17.0, -2.0, 12.0)
JOURNALS = range(4)
REACH_PAST = 2.0


@dataclass(frozen=True)
class Cylinder:
    number: int
    journal: int
    bank_deg: float
    side: float

    @property
    def name(self) -> str:
        return f"cylinder {self.number}"


CYLINDERS = tuple(
    Cylinder(number=2 * journal + extra, journal=journal, bank_deg=bank, side=side)
    for journal in JOURNALS
    for extra, bank, side in ((1, LEFT_BANK_DEG, -1.0), (2, RIGHT_BANK_DEG, 1.0))
)


class Port(StrEnum):
    INTAKE = "intake"
    EXHAUST = "exhaust"


@dataclass(frozen=True)
class Valve:
    cylinder: Cylinder
    port: Port
    side: float

    @property
    def name(self) -> str:
        return f"{self.cylinder.name} {self.port}"

    @property
    def peak_deg(self) -> float:
        return INTAKE_PEAK_DEG if self.port is Port.INTAKE else EXHAUST_PEAK_DEG

    @property
    def fires_at(self) -> float:
        return FIRING_ORDER.index(self.cylinder.number) * FIRING_STEP_DEG


VALVES = tuple(
    Valve(cylinder=cylinder, port=port, side=side)
    for cylinder in CYLINDERS
    for port, side in ((Port.EXHAUST, -1.0), (Port.INTAKE, 1.0))
)


@dataclass(frozen=True)
class CrankPiece:
    index: int
    low: float | None
    high: float | None

    @property
    def name(self) -> str:
        return f"crank {self.index + 1}"


@dataclass(frozen=True)
class V8Master(Master):
    bore_inches: float = given(4.0, "in", why="The 350's bore", source=SPECS)
    stroke_inches: float = given(3.48, "in", why="The 350's stroke", source=SPECS)
    rod_inches: float = given(5.7, "in", why="The 350's rod, centre to centre", source=SPECS)
    deck_inches: float = given(9.025, "in", why="The 350's deck height", source=SPECS)
    spacing_inches: float = given(4.4, "in", why="The small block's bore spacing", source=FORUM)
    rod_journal_inches: float = given(
        2.1, "in", why="The large-journal 350's rod journal", source=f"{ESTIMATE}: recalled"
    )
    compression_height_inches: float = given(
        1.56,
        "in",
        why="Wrist pin to crown, so the crown meets the deck",
        source=f"{ESTIMATE}: recalled",
    )
    scale: float = given(
        1.0 / 3.0, "-", why="Prints on a desktop bed and fits the bought parts", source=ESTIMATE
    )
    rod_pitch: float = given(
        8.0, "mm", why="A rod's width on the journal, and so the banks' stagger", source=ESTIMATE
    )
    wrist_pin_diameter: float = given(3.0, "mm", why="Stock dowel", source="ISO 8734")
    wrist_pin_length: float = given(
        30.0, "mm", why="Stock dowel within the bore", source="ISO 8734"
    )
    skirt: float = given(6.0, "mm", why="Clears the crank webs at the bottom", source=ESTIMATE)
    wall: float = given(4.0, "mm", why="Block's walls", source=ESTIMATE)
    flywheel: float = given(6.0, "mm", why="Flywheel behind the last web", source=ESTIMATE)
    timing_module: float = given(1.0, "mm", why="Printable timing teeth", source=ESTIMATE)
    crank_teeth: int = given(36, "-", why="Lifts the cam clear of the banks", source=ESTIMATE)
    timing_width: float = given(6.0, "mm", why="Timing gear", source=ESTIMATE)
    pulley_radius: float = given(14.0, "mm", why="Crank pulley", source=ESTIMATE)
    head_access: float = given(3.5, "mm", why="A screw head through the flywheel", source=ESTIMATE)
    pulley_width: float = given(6.0, "mm", why="Crank pulley", source=ESTIMATE)
    cam_diameter: float = given(5.0, "mm", why="Camshaft", source=ESTIMATE)
    cam_pad: float = given(10.0, "mm", why="Bearing pad at each end", source=ESTIMATE)
    throw_cam: float = given(4.0, "mm", why="Each eccentric lobe's throw", source=ESTIMATE)
    layer: float = given(4.0, "mm", why="Valvetrain's two planes", source=ESTIMATE)
    strap_length: float = given(16.0, "mm", why="Lobe centre to lifter pin", source=ESTIMATE)
    lifter_span: float = given(32.0, "mm", why="Between its two holes", source=ESTIMATE)
    pin_diameter: float = given(3.0, "mm", why="Stub pins on the printed links", source=ESTIMATE)
    eye: float = given(3.5, "mm", why="Radius round a stub pin's hole", source=ESTIMATE)
    rail_low: float = given(66.0, "mm", why="Above the lifter's strap", source=ESTIMATE)
    rail_height: float = given(11.0, "mm", why="Lifter guide's length", source=ESTIMATE)
    rail_width: float = given(10.0, "mm", why="Lifter rail and keeper", source=ESTIMATE)
    head_height: float = given(11.0, "mm", why="Cylinder head", source=ESTIMATE)
    chamber: float = given(4.0, "mm", why="Valves open clear of the crown", source=ESTIMATE)
    valve_x: float = given(7.0, "mm", why="Valves off the bore's axis", source=ESTIMATE)
    valve_y: float = given(8.0, "mm", why="Valves apart along the bank", source=ESTIMATE)
    valve_head: float = given(5.0, "mm", why="Valve head radius", source=ESTIMATE)
    valve_head_thickness: float = given(1.5, "mm", why="Valve head", source=ESTIMATE)
    stem_diameter: float = given(3.0, "mm", why="Valve stem", source=ESTIMATE)
    pivot_x: float = given(22.0, "mm", why="Rocker shaft off the bore's axis", source=ESTIMATE)
    pivot_rise: float = given(12.0, "mm", why="Rocker shaft over the head", source=ESTIMATE)
    rocker_arm: float = given(12.0, "mm", why="Pivot to pushrod", source=ESTIMATE)
    rocker_nose: float = given(8.0, "mm", why="Pivot to link", source=ESTIMATE)
    link_length: float = given(
        10.0, "mm", why="Rocker to valve, in toggle when shut", source=ESTIMATE
    )
    head_overhang: float = given(6.0, "mm", why="Carries the rocker posts", source=ESTIMATE)
    post_width: float = given(4.0, "mm", why="Rocker shaft post", source=ESTIMATE)
    plug_diameter: float = given(5.0, "mm", why="Spark plug", source=ESTIMATE)
    plug_length: float = given(12.0, "mm", why="Spark plug", source=ESTIMATE)
    header_diameter: float = given(11.0, "mm", why="Exhaust header", source=ESTIMATE)
    tray_thickness: float = given(4.0, "mm", why="Battery tray", source=ESTIMATE)
    tab_thickness: float = given(6.0, "mm", why="Battery tray's tab", source=ESTIMATE)
    tray_lip: float = given(4.0, "mm", why="Tray past the holder", source=ESTIMATE)
    lead_rise: float = given(24.0, "mm", why="The lead turns down to the cap", source=ESTIMATE)
    switch_panel: float = given(
        2.0,
        "mm",
        why="Within the switch's panel range, so its clips hold",
        source="E-Switch RD11131100 drawing, suggested panel cutout",
    )
    foot: float = given(8.0, "mm", why="Block's feet, wide enough for inserts", source=ESTIMATE)
    plate_thickness: float = given(6.0, "mm", why="Takes the rear plate's inserts", source=ESTIMATE)
    screw: Metric = given(Metric.M3, "-", why="One screw type", source="ISO 4762")
    long_screw: float = given(
        16.0, "mm", why="Through a head, rail, header or gear", source="ISO 4762 nominal lengths"
    )
    pin_screw_length: float = given(
        30.0, "mm", why="Through a crank pin into the next piece", source="ISO 4762 nominal lengths"
    )
    plate_screw_length: float = given(
        10.0, "mm", why="Through the plate into the full insert", source="ISO 4762 nominal lengths"
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
    def bore(self) -> float:
        return self.bore_inches * INCH * self.scale

    @property
    def throw(self) -> float:
        return self.stroke_inches * INCH * self.scale / 2

    @property
    def rod(self) -> float:
        return self.rod_inches * INCH * self.scale

    @property
    def deck(self) -> float:
        return self.deck_inches * INCH * self.scale

    @property
    def spacing(self) -> float:
        return self.spacing_inches * INCH * self.scale

    @property
    def crank_pin_diameter(self) -> float:
        return self.rod_journal_inches * INCH * self.scale

    @property
    def compression_height(self) -> float:
        return self.compression_height_inches * INCH * self.scale

    block_material: str = given(
        "PETG Prusa Orange",
        "-",
        why="The block, heads and rear plate in one engine-paint orange, like a small-block",
        source="design input; the spool is in the catalogue",
    )
    moving_material: str = given(
        "PETG Urban Grey",
        "-",
        why="Every part that turns or slides in one steel grey, so the motion reads",
        source="design input; the spool is in the catalogue",
    )
    exhaust_material: str = given(
        "PETG Anthracite Grey",
        "-",
        why="The headers and the battery tray in a dark cast-iron tone",
        source="design input; the spool is in the catalogue",
    )
    plug_material: str = given(
        "PETG Signal White",
        "-",
        why="The spark plugs read by their white insulators",
        source="design input; the spool is in the catalogue",
    )

    @property
    def rod_thickness(self) -> float:
        return self.rod_pitch - 2 * self.fits.sliding

    @property
    def pin_length(self) -> float:
        return 2 * self.rod_pitch

    @property
    def web(self) -> float:
        return self.spacing - self.pin_length

    @property
    def arm(self) -> float:
        return self.web / 2

    @property
    def pin_bore(self) -> float:
        return self.fits.printed(self.crank_pin_diameter)

    @property
    def big_end_radius(self) -> float:
        return self.pin_bore / 2 + self.fits.structural_wall

    @property
    def small_end_radius(self) -> float:
        return self.fits.printed(self.wrist_pin_diameter) / 2 + self.fits.structural_wall

    @property
    def swing_radius(self) -> float:
        return self.throw + self.big_end_radius + self.fits.structural_wall

    @property
    def axle_height(self) -> float:
        return self.swing_radius + self.foot

    @property
    def axle(self) -> Location:
        return Location((0.0, 0.0, self.axle_height))

    def journal_y(self, journal: int) -> float:
        return (journal - 1.5) * self.spacing

    def piece_y(self, piece: CrankPiece) -> float:
        return (piece.index - 2) * self.spacing

    def cylinder_y(self, cylinder: Cylinder) -> float:
        return self.journal_y(cylinder.journal) + cylinder.side * self.rod_pitch / 2

    @property
    def crank_pieces(self) -> tuple[CrankPiece, ...]:
        phases = (None, *(phase + REST_TURN_DEG for phase in JOURNAL_PHASES_DEG), None)
        return tuple(CrankPiece(k, phases[k], phases[k + 1]) for k in range(5))

    def crank_pin(self, journal: int, turned: float, y: float) -> Location:
        angle = JOURNAL_PHASES_DEG[journal] + turned
        return self.axle * Pos(Y=y) * Rot(Y=angle) * Pos(Z=self.throw)

    def bank_axis(self, cylinder: Cylinder) -> Location:
        return self.axle * Pos(Y=self.cylinder_y(cylinder)) * Rot(Y=cylinder.bank_deg)

    def wrist(self, cylinder: Cylinder, turned: float) -> Location:
        pin = self.crank_pin(cylinder.journal, turned, self.cylinder_y(cylinder))
        circle = Edge.make_circle(self.rod, Plane(origin=pin.position, x_dir=ALONG, z_dir=ACROSS))
        axis = self.bank_axis(cylinder)
        line = Edge.make_line(axis.position, (axis * Pos(Z=self.deck)).position)
        (found,) = circle.find_intersection_points(line)
        at = Location(Plane(axis))
        return Location(Plane(origin=found, x_dir=at.x_axis.direction, z_dir=at.z_axis.direction))

    def rod_frame(self, cylinder: Cylinder) -> Location:
        wrist = self.wrist(cylinder, REST_TURN_DEG)
        pin = self.crank_pin(cylinder.journal, REST_TURN_DEG, self.cylinder_y(cylinder))
        along = pin.position - wrist.position
        return Location(Plane(origin=wrist.position, x_dir=along, z_dir=ACROSS))

    def hinge_at(self, at: Location) -> Location:
        return Location(Plane(origin=at.position, x_dir=ALONG, z_dir=ACROSS))

    def wrist_pin_at(self, cylinder: Cylinder) -> Location:
        wrist = self.wrist(cylinder, REST_TURN_DEG)
        return self.hinge_at(wrist) * Pos(Z=-self.wrist_pin_length / 2)

    @property
    def wrist_access(self) -> float:
        return 2 * self.spacing

    @property
    def crank_turn(self) -> Location:
        return Location(Plane(origin=self.axle.position, x_dir=ALONG, z_dir=TOWARD_THE_FRONT))

    def crank_frame(self, piece: CrankPiece) -> Location:
        return self.across(self.piece_y(piece))

    def across(self, y: float) -> Location:
        at = self.axle * Pos(Y=y)
        return Location(Plane(origin=at.position, x_dir=ALONG, z_dir=ACROSS))

    def pin_spot(self, piece: CrankPiece, phase: float) -> Location:
        at = self.axle * Pos(Y=self.piece_y(piece)) * Rot(Y=phase) * Pos(Z=self.throw)
        return Location((self.crank_frame(piece).inverse() * at).position)

    @property
    def rear(self) -> float:
        return 2 * self.spacing + self.arm + self.flywheel + self.fits.sliding

    @property
    def wall_inside(self) -> float:
        return -2 * self.spacing - self.arm - self.fits.sliding

    @property
    def front(self) -> float:
        return self.wall_inside - self.wall

    @property
    def length(self) -> float:
        return self.rear - self.front

    @property
    def case_half(self) -> float:
        return self.swing_radius + self.foot

    @property
    def bank_width(self) -> float:
        return self.bore + 2 * self.wall

    @property
    def plate_top(self) -> float:
        return self.axle_height + self.case_half

    @property
    def plate_spots(self) -> tuple[Location, ...]:
        x = self.swing_radius + self.foot / 2
        return tuple(
            Location(Plane(origin=(sx, self.rear, z), x_dir=ALONG, z_dir=ACROSS))
            for sx in (-x, x)
            for z in (self.foot, self.axle_height - self.foot)
        )

    def plate_screw_at(self, spot: Location) -> Location:
        return spot * Pos(Z=self.plate_thickness)

    @property
    def pivot_bore(self) -> float:
        return clearance(self.screw, fits=self.fits)

    @property
    def insert_length(self) -> float:
        return insert_size(self.screw, fits=self.fits, stock=self.stock).length

    @property
    def motor_width(self) -> float:
        return vendor_extent(MOTOR).size.X

    @property
    def motor_height(self) -> float:
        return vendor_extent(MOTOR).size.Y

    @property
    def motor_pocket_width(self) -> float:
        return self.motor_width + 2 * self.fits.sliding

    @property
    def motor_pocket_height(self) -> float:
        return self.motor_height + 2 * self.fits.sliding

    @property
    def motor_at(self) -> Location:
        tip = Location((0.0, self.rear - MOTOR_SHAFT, self.axle_height))
        return tip * Rot(X=90.0) * Pos(Z=-vendor_reach(MOTOR_OUTPUT, Axis.Z))

    @property
    def motor_behind_plate(self) -> float:
        return motor.SHAFT_START - vendor_extent(MOTOR).min.Z - self.plate_thickness

    @property
    def plate_outer_y(self) -> float:
        return self.rear + self.plate_thickness

    @property
    def cap_flange(self) -> float:
        return self.plate_screw_length - self.insert_length

    @property
    def cap_spot_x(self) -> float:
        return self.motor_width / 2 + self.fits.structural_wall + self.pivot_bore

    @property
    def cap_spots(self) -> tuple[Location, ...]:
        return tuple(
            self.axle * Pos(X=x, Y=self.plate_outer_y) * Rot(X=-90.0)
            for x in (-self.cap_spot_x, self.cap_spot_x)
        )

    @property
    def crank_radius(self) -> float:
        return pitch_radius(self.crank_teeth, self.timing_module)

    @property
    def cam_teeth(self) -> int:
        return 2 * self.crank_teeth

    @property
    def cam_radius(self) -> float:
        return pitch_radius(self.cam_teeth, self.timing_module)

    @property
    def cam_height(self) -> float:
        return self.crank_radius + self.cam_radius

    @property
    def nose_y(self) -> float:
        return self.front - self.fits.sliding

    @property
    def gear_y(self) -> float:
        return self.nose_y - self.timing_width

    @property
    def cam_axis(self) -> Location:
        return self.axle * Pos(Z=self.cam_height)

    @property
    def cam_frame(self) -> Location:
        at = self.cam_axis * Pos(Y=self.gear_y)
        return Location(Plane(origin=at.position, x_dir=ALONG, z_dir=ACROSS))

    @property
    def cam_turn(self) -> Location:
        return self.cam_frame

    @property
    def camshaft_length(self) -> float:
        return self.rear - self.gear_y

    @property
    def crank_gear_frame(self) -> Location:
        return self.across(self.gear_y)

    @property
    def cam_phase(self) -> float:
        return mesh_phase(
            self.cam_frame, self.cam_teeth, self.crank_gear_frame, self.crank_teeth
        ) % (360.0 / self.cam_teeth)

    @property
    def cam_pose(self) -> Location:
        return self.cam_frame * Rot(Z=self.cam_phase)

    @property
    def nose_spots(self) -> tuple[Location, ...]:
        arm = self.crank_pin_diameter / 4
        face = self.across(self.nose_y) * Rot(X=180.0)
        return tuple(face * Pos(X=x) for x in (-arm, arm))

    def bank(self, deg: float, y: float) -> Location:
        turned = self.axle * Pos(Y=y) * Rot(Y=deg)
        inward = -1.0 if deg > 0 else 1.0
        return Location(
            Plane(
                origin=turned.position,
                x_dir=turned.x_axis.direction * inward,
                z_dir=turned.z_axis.direction,
            )
        )

    @property
    def bank_cam_centre(self) -> Location:
        return Location((self.bank(LEFT_BANK_DEG, 0.0).inverse() * self.cam_axis).position)

    @property
    def lobe_radius(self) -> float:
        return self.throw_cam + self.cam_diameter / 2 + self.fits.structural_wall

    @property
    def strap_radius(self) -> float:
        return self.fits.printed(2 * self.lobe_radius) / 2 + self.fits.structural_wall

    @property
    def stub_hole(self) -> float:
        return self.fits.printed(self.pin_diameter)

    @property
    def cam_bore(self) -> float:
        return self.fits.printed(self.cam_diameter)

    def valve_y_at(self, valve: Valve) -> float:
        return self.cylinder_y(valve.cylinder) + valve.side * self.valve_y

    def plane_a(self, valve: Valve) -> float:
        return self.valve_y_at(valve) - self.layer

    def bank_of(self, valve: Valve, y: float) -> Location:
        return self.bank(valve.cylinder.bank_deg, y)

    def in_plane(self, valve: Valve, y: float, x: float, z: float) -> Location:
        return self.bank_of(valve, y) * Pos(X=x, Z=z)

    def hinge_on(self, at: Location, x_toward: Location | None = None) -> Location:
        along = ALONG if x_toward is None else line_through(at, x_toward).direction
        return Location(Plane(origin=at.position, x_dir=along, z_dir=ACROSS))

    def peak_turn(self, valve: Valve) -> float:
        return valve.cylinder.bank_deg + (valve.fires_at + valve.peak_deg) / 2

    def lobe_turn(self, valve: Valve, turned: float) -> float:
        return self.peak_turn(valve) - turned / 2

    def lobe_centre(self, valve: Valve, turned: float) -> Location:
        centre = self.cam_axis * Pos(Y=self.plane_a(valve))
        return centre * Rot(Y=self.lobe_turn(valve, turned)) * Pos(Z=self.throw_cam)

    @property
    def lifter_x(self) -> float:
        return self.bank_cam_centre.position.X

    @property
    def cam_z(self) -> float:
        return self.bank_cam_centre.position.Z

    def lifter_pin(self, valve: Valve, turned: float) -> Location:
        centre = self.lobe_centre(valve, turned)
        y = self.plane_a(valve)
        low = self.in_plane(valve, y, self.lifter_x, self.cam_z)
        high = low * Pos(Z=2 * self.strap_length)
        circle = Edge.make_circle(
            self.strap_length, Plane(origin=centre.position, x_dir=ALONG, z_dir=ACROSS)
        )
        (found,) = circle.find_intersection_points(Edge.make_line(low.position, high.position))
        return Location(found)

    def lifter_top(self, valve: Valve, turned: float) -> Location:
        along = self.bank_of(valve, 0.0)
        return Location(
            Plane(
                origin=self.lifter_pin(valve, turned).position,
                x_dir=along.x_axis.direction,
                z_dir=along.z_axis.direction,
            )
        ) * Pos(Z=self.lifter_span)

    def rocker_pivot(self, valve: Valve, y: float | None = None) -> Location:
        at = self.valve_y_at(valve) if y is None else y
        z = self.deck + self.head_height + self.pivot_rise
        return self.in_plane(valve, at, self.pivot_x, z)

    def rocker_mid(self, valve: Valve) -> Location:
        return self.rocker_pivot(valve) * Pos(X=self.rocker_arm)

    def pushrod_length(self, valve: Valve) -> float:
        y = self.valve_y_at(valve)
        mid = self.in_plane(
            valve, y, self.lifter_x, self.cam_z + self.strap_length + self.lifter_span
        )
        return line_between(mid, self.rocker_mid(valve)).length

    def rocker_end(self, valve: Valve, turned: float) -> Location:
        y = self.valve_y_at(valve)
        top = self.lifter_top(valve, turned)
        at = Location((top.position.X, y, top.position.Z))
        pivot = self.rocker_pivot(valve)
        span = line_between(pivot, at).length
        angle = Triangle(a=self.pushrod_length(valve), b=self.rocker_arm, c=span).A
        toward = self.hinge_on(pivot, at)
        wanted = self.rocker_mid(valve)
        found = [toward * Rot(Z=turn * angle) * Pos(X=self.rocker_arm) for turn in (1.0, -1.0)]
        return min(found, key=lambda each: line_between(each, wanted).length)

    def lowest_turn(self, valve: Valve) -> float:
        return valve.fires_at + valve.peak_deg - 360.0

    def tip_shut(self, valve: Valve) -> Location:
        z = self.deck + self.head_height + self.pivot_rise
        pivot = self.rocker_pivot(valve)
        reach = self.rocker_nose + self.link_length
        level = self.in_plane(valve, self.valve_y_at(valve), self.valve_x, z)
        circle = Edge.make_circle(reach, Plane(origin=pivot.position, x_dir=ALONG, z_dir=ACROSS))
        line = Edge.make_line(level.position, (level * Pos(Z=reach)).position)
        (found,) = circle.find_intersection_points(line)
        return level * Pos(Z=line_between(level, Location(found)).length)

    def nose_bend(self, valve: Valve) -> float:
        pivot = self.rocker_pivot(valve)
        end = self.rocker_end(valve, self.lowest_turn(valve))
        return turn_to(
            Plane(self.hinge_on(pivot, end)), line_through(pivot, self.tip_shut(valve)).direction
        )

    def rocker_frame(self, valve: Valve) -> Location:
        return self.hinge_on(self.rocker_pivot(valve), self.rocker_end(valve, REST_TURN_DEG))

    def nose_at(self, valve: Valve, turned: float) -> Location:
        pivot = self.rocker_pivot(valve)
        frame = self.hinge_on(pivot, self.rocker_end(valve, turned))
        return frame * Rot(Z=self.nose_bend(valve)) * Pos(X=self.rocker_nose)

    def valve_tip(self, valve: Valve, turned: float) -> Location:
        nose = self.nose_at(valve, turned)
        shut = self.tip_shut(valve)
        top = shut * Pos(Y=0.0)
        along = self.bank_of(valve, 0.0).z_axis.direction
        high = Location(top.position + along * self.fits.sliding)
        low = Location(top.position - along * self.link_length)
        circle = Edge.make_circle(
            self.link_length, Plane(origin=nose.position, x_dir=ALONG, z_dir=ACROSS)
        )
        (found,) = circle.find_intersection_points(Edge.make_line(high.position, low.position))
        return Location(found)

    def valve_frame(self, valve: Valve) -> Location:
        tip = self.valve_tip(valve, REST_TURN_DEG)
        along = self.bank_of(valve, 0.0)
        return Location(
            Plane(origin=tip.position, x_dir=along.x_axis.direction, z_dir=along.z_axis.direction)
        )

    def valve_lift(self, valve: Valve, turned: float) -> float:
        return (self.valve_tip(valve, turned).position - self.tip_shut(valve).position).length

    def stem_length(self, valve: Valve) -> float:
        return line_between(
            self.tip_shut(valve),
            self.in_plane(valve, self.valve_y_at(valve), self.valve_x, self.deck + self.chamber),
        ).length

    def counter_spot(self, piece: CrankPiece, phase: float) -> Location:
        return self.pin_spot(piece, phase + 180.0)

    def head_frame(self, deg: float) -> Location:
        return self.bank(deg, (self.front + self.rear) / 2) * Pos(Z=self.deck)

    def head_spots(self, deg: float) -> tuple[Location, ...]:
        frame = self.bank(deg, 0.0) * Pos(Z=self.deck)
        off = self.bank_width / 2 - 2 * self.pivot_bore
        return tuple(frame * Pos(X=-off, Y=2 * k * self.spacing) for k in HEAD_SPOTS)

    def post_ys(self, deg: float) -> tuple[float, ...]:
        centres = [self.cylinder_y(each) for each in CYLINDERS if each.bank_deg == deg]
        return tuple(y + off for y in centres for off in POSTS)

    @property
    def pad_x(self) -> float:
        return (self.bank_width / 2 + self.lifter_x + self.rail_width) / 2

    @property
    def pad_width(self) -> float:
        return self.lifter_x + self.rail_width - self.bank_width / 2 + self.fits.structural_wall

    @property
    def pad_height(self) -> float:
        return self.rail_low - self.cam_z + self.lobe_radius

    @property
    def left_bank(self) -> float:
        return LEFT_BANK_DEG

    @property
    def right_bank(self) -> float:
        return RIGHT_BANK_DEG

    @property
    def rocker_shaft(self) -> float:
        return self.wrist_pin_diameter

    @property
    def pressed_shaft(self) -> float:
        return self.fits.pressed(self.rocker_shaft)

    @property
    def tray_width(self) -> float:
        return self.holder_box.size.Y + self.tray_lip

    @property
    def tray_length(self) -> float:
        return self.motor_behind_plate + self.lead_rise + self.holder_box.size.X + self.switch_bay

    @property
    def tab_height(self) -> float:
        return 2 * self.foot

    @property
    def tab_width(self) -> float:
        return 2 * (self.swing_radius + self.foot / 2 - self.foot)

    def flat_turn(self, frame: Location) -> float:
        return turn_to(Plane(frame), self.cam_frame.y_axis.direction * -1.0) + 90.0

    def lifter_frame(self, valve: Valve) -> Location:
        along = self.bank_of(valve, 0.0)
        at = Pos(Y=self.layer) * self.lifter_pin(valve, REST_TURN_DEG)
        return Location(
            Plane(origin=at.position, x_dir=along.x_axis.direction, z_dir=along.z_axis.direction)
        )

    def pushrod_frame(self, valve: Valve) -> Location:
        low = self.lifter_top(valve, REST_TURN_DEG)
        high = Pos(Y=-self.layer) * self.rocker_end(valve, REST_TURN_DEG)
        return self.hinge_on(low, high)

    def link_frame(self, valve: Valve) -> Location:
        low = Pos(Y=-self.layer) * self.nose_at(valve, REST_TURN_DEG)
        high = Pos(Y=-self.layer) * self.valve_tip(valve, REST_TURN_DEG)
        return self.hinge_on(low, high)

    def rocker_shaft_at(self, deg: float) -> Location:
        y = self.front - self.fits.sliding
        at = self.bank(deg, y) * Pos(
            X=self.pivot_x, Z=self.deck + self.head_height + self.pivot_rise
        )
        return Location(Plane(origin=at.position, x_dir=ALONG, z_dir=ACROSS))

    @property
    def rocker_shaft_length(self) -> float:
        return self.length

    def rail_spots(self, deg: float) -> tuple[Location, ...]:
        return self._pad_spots(deg, self.lifter_x - self.rail_width + self.eye)

    def keeper_spots(self, deg: float) -> tuple[Location, ...]:
        return self._pad_spots(deg, self.lifter_x + self.rail_width - self.eye)

    def _pad_spots(self, deg: float, x: float) -> tuple[Location, ...]:
        ends = (self.front + self.cam_pad / 2, self.rear - self.cam_pad / 2)
        return tuple(self.bank(deg, y) * Pos(X=x, Z=self.rail_low) for y in ends)

    def plug_at(self, cylinder: Cylinder) -> Location:
        y = self.cylinder_y(cylinder)
        return self.bank(cylinder.bank_deg, y) * Pos(X=-self.valve_x, Z=self.deck)

    def header_frame(self, deg: float) -> Location:
        off = self.bank_width / 2 + self.header_diameter / 2
        middle = (self.front + self.rear) / 2
        return self.bank(deg, middle) * Pos(X=-off, Z=self.deck + self.head_height / 2)

    def header_spots(self, deg: float) -> tuple[Location, ...]:
        side = self.bank_width / 2
        frame = self.bank(deg, (self.front + self.rear) / 2) * Pos(
            X=-side, Z=self.deck + self.head_height / 2
        )
        return tuple(frame * Pos(Y=y) * Rot(Y=-90.0) for y in (-self.spacing, self.spacing))

    @property
    def tray_spots(self) -> tuple[Location, ...]:
        arm = self.motor_pocket_width / 2 + 2 * self.pivot_bore + self.cap_spot_x
        return tuple(
            Location(Plane(origin=(x, self.plate_outer_y, self.foot), x_dir=ALONG, z_dir=ACROSS))
            for x in (-arm, arm)
        )

    @property
    def tray_top(self) -> float:
        return self.tray_thickness

    @property
    def tray_frame(self) -> Location:
        return Location((0.0, self.plate_outer_y, 0.0))

    @property
    def holder_at(self) -> Location:
        lead = self.motor_behind_plate + self.lead_rise
        at = Location((0.0, self.plate_outer_y + lead + self.holder_box.size.X / 2, self.tray_top))
        return at * Rot(Z=-90.0)

    @property
    def holder_box(self) -> BoundBox:
        return vendor_extent(BATTERY_HOLDER)

    @property
    def holder_width(self) -> float:
        return self.holder_box.size.Y

    @property
    def holder_height(self) -> float:
        return self.holder_box.size.Z

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
    def switch_bay(self) -> float:
        return self.fits.sliding + self.lead_bend + self.switch_depth + self.switch_panel

    @property
    def switch_face(self) -> Location:
        end = self.holder_box.size.X / 2 + self.switch_bay
        middle = self.holder_box.size.Z / 2
        return self.holder_at * Location(
            Plane(origin=(-end, 0.0, middle), x_dir=ACROSS, z_dir=OUT_OF_THE_END)
        )

    @property
    def switch_at(self) -> Location:
        return self.switch_face * Pos(Z=-self.switch_seat)

    @property
    def switch_terminals(self) -> Location:
        return Location((self.switch_face * Pos(Z=-self.switch_depth)).position)

    @property
    def lead_bend(self) -> float:
        return wire.BEND_DIAMETERS * wire.DIAMETER

    @property
    def switch_ends(self) -> switch.Terminals:
        return switch.terminals(SWITCH)

    @property
    def holder_leads(self) -> battery_holder.Leads:
        return battery_holder.leads(BATTERY_HOLDER)

    @property
    def sleeve_at(self) -> Location:
        return Location(self.lead_over_the_switch.position) * Pos(Z=-sleeve.LENGTH / 2)

    @property
    def holder_leads_out(self) -> Location:
        return Location((self.holder_at * self.holder_leads.out).position)

    @property
    def lead_over_the_switch(self) -> Location:
        return self.switch_terminals * Pos(Z=self.lead_bend)

    @property
    def lead_end(self) -> Location:
        return Location(
            (0.0, self.plate_outer_y + self.motor_behind_plate, self.axle_height)
        ) * Pos(Z=self.motor_pocket_height / 2 + self.fits.structural_wall)

    @property
    def lead_above(self) -> Location:
        return self.lead_end * Pos(Z=self.lead_rise)

    @property
    def poses(self) -> tuple[Pose, ...]:
        return tuple(
            Pose(name=f"crank at {n * POSE_STEP_DEG:g}", joints={CRANK: -n * POSE_STEP_DEG})
            for n in range(POSE_COUNT)
        )


MASTER = V8Master()
