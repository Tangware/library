from dataclasses import dataclass
from functools import cached_property
from itertools import pairwise

from build123d import Axis, Location, Plane, Pos, Rot, Triangle
from cad.design.master import Master, Pose, given
from cad.library.bought.catalogue import Catalogue, Cleanup, Download
from cad.library.bought.vendor import vendor_extent, vendor_reach
from cad.library.fits import FITS_UNITS, STAINLESS_A2_70, Fits
from cad.library.printing import PRINT_SETTINGS_UNITS, PrintSettings
from cad.library.standard.fasteners import (
    STOCK_UNITS,
    Metric,
    Stock,
    clearance,
    insert_size,
    nut_height,
)
from cad.library.standard.profiles import TubeSize
from cad.standards import RatedTorque

from strandbeest.models import battery_holder, lock_nut, motor

CRANK = "crank"
HOLY = "Theo Jansen's link proportions, en.wikipedia.org/wiki/Jansen's_linkage, read 2026-11-01"
HOLY_WHY = "One of Jansen's proportions, which set the foot's path"
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
LOCK_NUT = Catalogue(file="din985_m3", grams=lock_nut.GRAMS_ESTIMATED, model=lock_nut.solid)
BATTERY_HOLDER = Catalogue(
    file="pololu_1159", grams=battery_holder.GRAMS_ESTIMATED, model=battery_holder.solid
)
LEFT = -1.0
RIGHT = 1.0
ANTICLOCKWISE = 1.0
CLOCKWISE = -1.0
ACROSS = (0.0, 1.0, 0.0)
ALONG = (1.0, 0.0, 0.0)
TOWARD_THE_MIDDLE = (0.0, -1.0, 0.0)
HALF_TURN_DEG = 180.0
PHASES_DEG = (0.0, 120.0, 240.0, 60.0, 300.0, 180.0)
GAIT_STEP_DEG = 30.0
TURN_DEG = 360.0


def third_corner(
    first: Location, second: Location, from_first: float, from_second: float, turn: float
) -> Location:
    span = (first.inverse() * second).position.length
    angle = Triangle(a=from_second, b=from_first, c=span).A
    plane = Plane(origin=first.position, x_dir=second.position - first.position, z_dir=ACROSS)
    return Location(plane) * Rot(Z=-turn * angle) * Pos(X=from_first)


@dataclass(frozen=True)
class Joints:
    crank_pin: Location
    frame_pivot: Location
    upper: Location
    outer: Location
    lower: Location
    knee: Location
    tip: Location


@dataclass(frozen=True)
class Module:
    index: int
    phase: float

    @property
    def fore_phase(self) -> float:
        return HALF_TURN_DEG - self.phase


@dataclass(frozen=True)
class CrankPiece:
    index: int
    low: float | None
    high: float | None

    @property
    def name(self) -> str:
        return f"crank {self.index + 1}"


@dataclass(frozen=True)
class StrandbeestMaster(Master):
    a: float = given(38.0, "-", why=HOLY_WHY, source=HOLY)
    b: float = given(41.5, "-", why=HOLY_WHY, source=HOLY)
    c: float = given(39.3, "-", why=HOLY_WHY, source=HOLY)
    d: float = given(40.1, "-", why=HOLY_WHY, source=HOLY)
    e: float = given(55.8, "-", why=HOLY_WHY, source=HOLY)
    f: float = given(39.4, "-", why=HOLY_WHY, source=HOLY)
    g: float = given(36.7, "-", why=HOLY_WHY, source=HOLY)
    h: float = given(65.7, "-", why=HOLY_WHY, source=HOLY)
    i: float = given(49.0, "-", why=HOLY_WHY, source=HOLY)
    j: float = given(50.0, "-", why=HOLY_WHY, source=HOLY)
    k: float = given(61.9, "-", why=HOLY_WHY, source=HOLY)
    height_offset: float = given(7.8, "-", why=HOLY_WHY, source=HOLY)
    m: float = given(15.0, "-", why=HOLY_WHY, source=HOLY)
    scale: float = given(
        1.25,
        "mm per unit",
        why="The lower link clears the frame tube at its nearest pass, with the pivots' bosses",
        source="estimate: the proportions are dimensionless; the smallest round scale that clears",
    )
    axle_height: float = given(
        115.0,
        "mm",
        why="The feet's flat run lands on the ground",
        source="the proportions' foot depth at this scale, checked by the feet test",
    )
    lead_reach: float = given(12.0, "mm", why="The lead clears the deck's edge", source="estimate")
    lead_rise: float = given(
        12.0, "mm", why="The lead turns down over the cap's slot", source="estimate"
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
    screw: Metric = given(
        Metric.M3, "-", why="One screw type for every pivot and joint", source="ISO 4762"
    )
    pin_screw_length: float = given(
        20.0,
        "mm",
        why="Through the crank arm into the full insert in the next pin's tip",
        source="ISO 4762 nominal lengths",
    )
    deck_screw_length: float = given(
        8.0, "mm", why="Through the deck into the full insert", source="ISO 4762 nominal lengths"
    )
    screw_length: float = given(
        16.0,
        "mm",
        why="Spans two link layers, the foot's floor and a lock nut, two threads past",
        source="ISO 4762 nominal lengths",
    )
    layer: float = given(
        4.0,
        "mm",
        why="Two layers plus the foot's floor and a lock nut fill the 16 mm screw",
        source="the ISO 4762 length, less the DIN 985 nut and the foot's floor",
    )
    rod: Metric = given(
        Metric.M4, "-", why="The M4 rod fits the frame tube's bore", source="DIN 976-1"
    )
    tube: TubeSize = given(
        TubeSize(outside=6.0, wall=1.0),
        {"outside": "mm", "wall": "mm"},
        why="Both spaces the frame plates and carries the triangle and the rocker",
        source="common 6 x 1 aluminium tube; supplier not opened",
    )
    crank_pin_diameter: float = given(
        7.0,
        "mm",
        why="Holds a heat-set insert in its tip with the wall the table asks",
        source="the M3 x 5.7 insert's bore plus two structural walls, rounded up",
    )
    plate_thickness: float = given(
        8.0, "mm", why="Holds the motor's gearbox and the deck's inserts", source="design input"
    )
    deck_thickness: float = given(
        3.0, "mm", why="Carries the battery holder", source="estimate: not sized by a load test"
    )
    sail_x: float = given(
        50.0, "mm", why="Masts along the deck, clear of the holder", source="estimate"
    )
    sail_height: float = given(
        80.0, "mm", why="64 Jansen units on teardown's beest, scaled", source="teardown beast.js"
    )
    sail_chord: float = given(
        65.0, "mm", why="52 Jansen units on teardown's beest, scaled", source="teardown beast.js"
    )
    sail_base: float = given(26.0, "mm", why="Clears the holder", source="estimate")
    sail_thickness: float = given(2.0, "mm", why="Printed sail", source="estimate")
    mast_diameter: float = given(5.0, "mm", why="Mast in its socket", source="estimate")
    mast_socket: float = given(6.0, "mm", why="Socket's depth on the deck", source="estimate")
    rim_height: float = given(
        5.0, "mm", why="Keeps the battery holder on the deck", source="estimate"
    )

    @property
    def link_thickness(self) -> float:
        return self.layer - 2 * self.fits.sliding

    @property
    def nut_height(self) -> float:
        return lock_nut.HEIGHT

    @property
    def nut_flats(self) -> float:
        return lock_nut.ACROSS_FLATS + 2 * self.fits.sliding

    @property
    def foot_boss(self) -> float:
        return self.pivot_radius + self.fits.structural_wall

    @property
    def two_layers(self) -> float:
        return 2 * self.layer

    @property
    def threads_past_the_nut(self) -> float:
        return 2 * self.screw.pitch

    @property
    def foot_floor(self) -> float:
        return self.screw_length - self.two_layers - self.nut_height - self.threads_past_the_nut

    @property
    def foot_thickness(self) -> float:
        return self.foot_floor + self.nut_height

    @property
    def module_pitch(self) -> float:
        half = self.two_layers + self.foot_thickness
        return 2 * (half + self.threads_past_the_nut + self.fits.sliding)

    @property
    def crank_web(self) -> float:
        return self.module_pitch - 2 * self.two_layers

    @property
    def crank_arm(self) -> float:
        return self.crank_web / 2

    @property
    def modules(self) -> tuple[Module, ...]:
        return tuple(Module(index, phase) for index, phase in enumerate(PHASES_DEG))

    @property
    def crank_pieces(self) -> tuple[CrankPiece, ...]:
        phases = (None, *PHASES_DEG, None)
        return tuple(
            CrankPiece(index, low, high) for index, (low, high) in enumerate(pairwise(phases))
        )

    def module_y(self, module: Module) -> float:
        return (module.index - (len(PHASES_DEG) - 1) / 2) * self.module_pitch

    def piece_y(self, piece: CrankPiece) -> float:
        return (piece.index - len(PHASES_DEG) / 2) * self.module_pitch

    @property
    def half_width(self) -> float:
        last = (len(PHASES_DEG) - 1) / 2 * self.module_pitch
        return last + self.two_layers + self.crank_web + self.fits.sliding

    @property
    def axle(self) -> Location:
        return Location((0.0, 0.0, self.axle_height))

    def joints(self, crank_deg: float) -> Joints:
        s = self.scale
        pin = self.axle * Rot(Y=-crank_deg) * Pos(X=self.m * s)
        pivot = self.axle * Pos(X=-self.a * s, Z=-self.height_offset * s)
        upper = third_corner(pin, pivot, self.j * s, self.b * s, CLOCKWISE)
        lower = third_corner(pin, pivot, self.k * s, self.c * s, ANTICLOCKWISE)
        outer = third_corner(upper, pivot, self.e * s, self.d * s, CLOCKWISE)
        knee = third_corner(outer, lower, self.f * s, self.g * s, CLOCKWISE)
        tip = third_corner(knee, lower, self.h * s, self.i * s, CLOCKWISE)
        return Joints(pin, pivot, upper, outer, lower, knee, tip)

    @cached_property
    def rest(self) -> Joints:
        return self.joints(0.0)

    def link_frame(self, start: Location, end: Location) -> Location:
        return Location(
            Plane(origin=start.position, x_dir=end.position - start.position, z_dir=ACROSS)
        )

    @property
    def triangle_outer(self) -> Location:
        at = self.rest
        return self.link_frame(at.frame_pivot, at.upper).inverse() * at.outer

    @property
    def foot_tip(self) -> Location:
        at = self.rest
        return self.link_frame(at.lower, at.knee).inverse() * at.tip

    @property
    def pivot_bore(self) -> float:
        return clearance(self.screw, fits=self.fits)

    @property
    def tube_bore(self) -> float:
        return self.fits.printed(self.tube.outside)

    @property
    def pin_bore(self) -> float:
        return self.fits.printed(self.crank_pin_diameter)

    @property
    def pivot_radius(self) -> float:
        return self.pivot_bore / 2 + self.fits.structural_wall

    @property
    def tube_boss_radius(self) -> float:
        return self.tube_bore / 2 + self.fits.structural_wall

    @property
    def pin_boss_radius(self) -> float:
        return self.pin_bore / 2 + self.fits.structural_wall

    def pivot_screw(self, placing: Location, joint: Location) -> Location:
        return placing * Location(
            Plane(origin=joint.position, x_dir=ALONG, z_dir=TOWARD_THE_MIDDLE)
        )

    def pivot_nut(self, placing: Location, joint: Location, seat: float) -> Location:
        at = Plane(origin=joint.position + Pos(Y=seat).position, x_dir=ALONG, z_dir=ACROSS)
        return placing * Location(at)

    def foot_nut(self, placing: Location, at: Joints, joint: Location) -> Location:
        along = at.knee.position - at.lower.position
        seat = joint.position + Pos(Y=self.two_layers + self.foot_floor).position
        return placing * Location(Plane(origin=seat, x_dir=along, z_dir=ACROSS))

    def hinge(self, placing: Location, joint: Location) -> Location:
        at = placing * joint
        return Location(Plane(origin=at.position, x_dir=ALONG, z_dir=ACROSS))

    def on_module(self, module: Module, fore: bool) -> Location:
        at = Location((0.0, self.module_y(module), 0.0))
        return at * Rot(Z=HALF_TURN_DEG) if fore else at

    def level(self, layer: float) -> Location:
        return Pos(Y=layer * self.layer)

    def across(self, y: float) -> Location:
        at = self.axle * Pos(Y=y)
        return Location(Plane(origin=at.position, x_dir=ALONG, z_dir=ACROSS))

    @property
    def against_the_crank(self) -> Location:
        return Location(Plane(origin=self.axle.position, x_dir=ALONG, z_dir=TOWARD_THE_MIDDLE))

    def crank_frame(self, piece: CrankPiece) -> Location:
        return self.across(self.piece_y(piece))

    def pin_spot(self, phase: float) -> Location:
        return Rot(Z=-phase) * Pos(X=self.m * self.scale)

    @property
    def motor_width(self) -> float:
        return vendor_extent(MOTOR).size.X

    @property
    def motor_height(self) -> float:
        return vendor_extent(MOTOR).size.Y

    @property
    def cap_spot_x(self) -> float:
        return self.motor_width / 2 + self.fits.structural_wall + self.pivot_radius

    @property
    def cap_flange(self) -> float:
        return self.screw_length - self.insert_length

    @property
    def motor_pocket_width(self) -> float:
        return self.motor_width + 2 * self.fits.sliding

    @property
    def motor_pocket_height(self) -> float:
        return self.motor_height + 2 * self.fits.sliding

    @property
    def rod_hole(self) -> float:
        return clearance(self.rod, fits=self.fits)

    @property
    def cap_spots(self) -> tuple[Location, ...]:
        return tuple(
            self.axle * Pos(X=x, Y=self.plate_outer_y) * Rot(X=-90.0)
            for x in (-self.cap_spot_x, self.cap_spot_x)
        )

    @property
    def plate_outer_y(self) -> float:
        return self.half_width + self.plate_thickness

    @property
    def motor_shaft_tip(self) -> Location:
        return Location((0.0, self.half_width - MOTOR_SHAFT, self.axle_height))

    @property
    def motor_at(self) -> Location:
        return self.motor_shaft_tip * Rot(X=90.0) * Pos(Z=-vendor_reach(MOTOR_OUTPUT, Axis.Z))

    @property
    def motor_behind_plate(self) -> float:
        box = vendor_extent(MOTOR)
        return motor.SHAFT_START - box.min.Z - self.plate_thickness

    @property
    def plate_half_length(self) -> float:
        return self.a * self.scale + self.tube_boss_radius + self.plate_thickness

    @property
    def plate_bottom(self) -> float:
        return self.rest.frame_pivot.position.Z - self.tube_boss_radius - self.plate_thickness

    @property
    def deck_level(self) -> float:
        top_of_the_swing = (self.b - self.height_offset) * self.scale
        return self.axle_height + top_of_the_swing + self.pivot_radius

    def deck_spots_on(self, side: float) -> tuple[Location, ...]:
        inset = self.plate_half_length - self.plate_thickness
        y = side * (self.half_width + self.plate_thickness / 2)
        return tuple(Location((x, y, self.deck_level)) for x in (-inset, inset))

    @property
    def deck_spots(self) -> tuple[Location, ...]:
        return (*self.deck_spots_on(LEFT), *self.deck_spots_on(RIGHT))

    @property
    def rod_length(self) -> float:
        return 2 * (self.plate_outer_y + nut_height(self.rod) + 2 * self.rod.pitch)

    @property
    def tube_length(self) -> float:
        return 2 * self.half_width

    def along_y(self, x: float, y: float) -> Location:
        z = self.rest.frame_pivot.position.Z
        return Location(Plane(origin=(x, y, z), x_dir=ALONG, z_dir=ACROSS))

    def sail_at(self, module: Module) -> Location:
        return self.deck_top * Pos(X=self.sail_x, Y=self.module_y(module))

    @property
    def sail_outline(self) -> tuple[tuple[float, float], ...]:
        return (
            (self.mast_diameter / 2, self.sail_base),
            (self.mast_diameter / 2, self.sail_height),
            (-self.sail_chord, self.sail_base),
        )

    @property
    def deck_top(self) -> Location:
        return Location((0.0, 0.0, self.deck_level + self.deck_thickness))

    def plate_frame(self, side: float) -> Location:
        return self.across(side * self.half_width)

    @property
    def insert_bore(self) -> float:
        return insert_size(self.screw, fits=self.fits, stock=self.stock).hole

    @property
    def insert_length(self) -> float:
        return insert_size(self.screw, fits=self.fits, stock=self.stock).length

    @property
    def lead_start(self) -> Location:
        rise = battery_holder.HEIGHT / 2
        return self.deck_top * Pos(Y=battery_holder.WIDTH / 2, Z=rise)

    @property
    def lead_over_the_edge(self) -> Location:
        reach = self.plate_outer_y + self.lead_reach - battery_holder.WIDTH / 2
        return self.lead_start * Pos(Y=reach)

    @property
    def lead_above_the_cap(self) -> Location:
        return self.axle * Pos(Y=self.lead_in, Z=self.motor_pocket_height / 2 + self.lead_rise)

    @property
    def lead_end(self) -> Location:
        return self.axle * Pos(Y=self.lead_in, Z=self.motor_pocket_height / 2)

    @property
    def lead_in(self) -> float:
        return self.plate_outer_y + self.motor_behind_plate

    @property
    def poses(self) -> tuple[Pose, ...]:
        count = int(TURN_DEG / GAIT_STEP_DEG)
        return tuple(
            Pose(name=f"crank at {n * GAIT_STEP_DEG:g}", joints={CRANK: n * GAIT_STEP_DEG})
            for n in range(count)
        )


MASTER = StrandbeestMaster()
