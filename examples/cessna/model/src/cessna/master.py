from dataclasses import dataclass

from build123d import Axis, BoundBox, Edge, Location, Plane, Pos, Rot
from cad.design.master import Master, Pose, given
from cad.library.bought.catalogue import Catalogue, Cleanup, Download
from cad.library.bought.query import planes
from cad.library.bought.vendor import solids_of, vendor_extent, vendor_reach
from cad.library.features.planes import line_between, line_through, normal_to
from cad.library.fits import FITS_UNITS, STAINLESS_A2_70, Fits
from cad.library.gears import mesh_phase, pitch_radius
from cad.library.printing import PRINT_SETTINGS_UNITS, PrintSettings
from cad.library.standard.fasteners import STOCK_UNITS, Metric, Stock, clearance, insert_size
from cad.standards import RatedTorque

from cessna.models import battery_holder, cell, motor, sleeve, switch, wire

DRIVE = "drive"
TEARDOWN = "github.com/elvarofficial/teardown, sims/cessna-shared/gear.js, read 2026-11-01"
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
LEFT = -1.0
RIGHT = 1.0
SIDES = (LEFT, RIGHT)
ALONG = (1.0, 0.0, 0.0)
AFT = (0.0, 1.0, 0.0)
ACROSS = (0.0, 1.0, 0.0)
OUT_OF_THE_END = (-1.0, 0.0, 0.0)
UP = (0.0, 0.0, 1.0)
RETRACTED_DEG = 180.0
POSE_STEP_DEG = 45.0
POSE_COUNT = 5
PLATE_OUTLINE_M = (
    (-0.12, -0.62),
    (0.12, -0.62),
    (0.14, -0.32),
    (0.42, -0.22),
    (0.46, -0.12),
    (0.44, 0.16),
    (0.16, 0.16),
    (0.14, 0.78),
    (-0.14, 0.78),
    (-0.16, 0.16),
    (-0.44, 0.16),
    (-0.46, -0.12),
    (-0.42, -0.22),
    (-0.14, -0.32),
)


def tube_along(side: float) -> tuple[float, float, float]:
    return (side, 1.0, -0.6)


def second_along(side: float) -> tuple[float, float, float]:
    return (1.0, -side, 0.0)


def spider_up(side: float) -> tuple[float, float, float]:
    return (side, 1.0, 0.0)


def side_name(side: float, name: str) -> str:
    return f"{'left' if side == LEFT else 'right'} {name}"


def leg_along(side: float) -> tuple[float, float, float]:
    return (side, -0.8, -1.0)


@dataclass(frozen=True)
class CessnaMaster(Master):
    scale: float = given(
        1.0 / 6.0, "-", why="The whole gear prints on a desktop bed", source=ESTIMATE
    )
    wheel_radius_m: float = given(0.205, "m", why="The 6.00-6 tyre", source=TEARDOWN)
    wheel_width_m: float = given(0.135, "m", why="The 6.00-6 tyre", source=TEARDOWN)
    joint_m: float = given(
        0.28,
        "m",
        why="Clevis off the centreline, widened to clear the printed forks",
        source=ESTIMATE,
    )
    tube_m: float = given(
        0.36, "m", why="Side tube, lengthened for the printed hanger", source=ESTIMATE
    )
    leg_m: float = given(0.5, "m", why="Spring leg, tube to axle", source=TEARDOWN)
    shaft_drop_m: float = given(0.11, "m", why="Output shaft under the plate", source=TEARDOWN)
    module: float = given(1.0, "mm", why="Coarse enough for printed teeth", source=ESTIMATE)
    output_teeth: int = given(
        24, "-", why="Near the scaled 64 mm pinion; two motor turns per side", source=ESTIMATE
    )
    motor_teeth: int = given(12, "-", why="Turns the sector within one turn", source=ESTIMATE)
    rack_teeth: int = given(
        120, "-", why="A long radius, so the rack runs nearly straight", source=ESTIMATE
    )
    gear_width: float = given(9.0, "mm", why="The motor shaft's length", source=ESTIMATE)
    rack_width: float = given(6.0, "mm", why="Sector thickness", source=ESTIMATE)
    rack_rim: float = given(5.0, "mm", why="Sector rim behind the teeth", source=ESTIMATE)
    rack_margin_deg: float = given(
        7.0, "deg", why="Teeth past either end of the travel", source=ESTIMATE
    )
    rack_lead_deg: float = given(
        30.0, "deg", why="Sector arc ahead of the output pinion", source=ESTIMATE
    )
    shaft_diameter: float = given(8.0, "mm", why="Output shaft and side tube", source=ESTIMATE)
    spider: float = given(18.0, "mm", why="Holds four crossing inserts", source=ESTIMATE)
    fork_wall: float = given(5.0, "mm", why="Fork arm", source=ESTIMATE)
    fork_width: float = given(12.0, "mm", why="Fork arm across its pin", source=ESTIMATE)
    fork_reach: float = given(18.0, "mm", why="Clears the other fork at full bend", source=ESTIMATE)
    fork_boss: float = given(6.0, "mm", why="Fork past its pin", source=ESTIMATE)
    fork_base: float = given(10.0, "mm", why="Fork hub", source=ESTIMATE)
    tube_fork_base: float = given(5.0, "mm", why="Clears the hanger", source=ESTIMATE)
    plate_thickness: float = given(
        6.0, "mm", why="Takes the screws into the blocks", source=ESTIMATE
    )
    rail_x: float = given(18.5, "mm", why="Rails either side of the bracket", source=ESTIMATE)
    rail_thickness: float = given(3.0, "mm", why="Rail", source=ESTIMATE)
    rail_height: float = given(12.0, "mm", why="The 0.07 m rail, scaled", source=TEARDOWN)
    rail_length: float = given(180.0, "mm", why="The 1.1 m rail, scaled", source=TEARDOWN)
    rail_holes: int = given(6, "-", why="Lightening holes per rail", source=TEARDOWN)
    pillow_x: float = given(12.0, "mm", why="Close to the pinion", source=ESTIMATE)
    pillow_width: float = given(8.0, "mm", why="Holds an insert", source=ESTIMATE)
    pillow_depth: float = given(16.0, "mm", why="Two screws along it", source=ESTIMATE)
    spot_spacing: float = given(10.0, "mm", why="A block's two screws", source=ESTIMATE)
    hanger_at: float = given(42.0, "mm", why="Along the tube, past the fork", source=ESTIMATE)
    hanger_length: float = given(8.0, "mm", why="Bearing length on the tube", source=ESTIMATE)
    bracket_thickness: float = given(5.0, "mm", why="Bracket cheek", source=ESTIMATE)
    bracket_depth: float = given(24.0, "mm", why="Bracket foot along the plate", source=ESTIMATE)
    leg_width: float = given(12.0, "mm", why="The 96 mm leg, scaled", source=TEARDOWN)
    leg_thickness: float = given(6.0, "mm", why="Leg", source=ESTIMATE)
    boss_radius: float = given(7.0, "mm", why="Leg root and axle boss", source=ESTIMATE)
    boss_length: float = given(12.0, "mm", why="Axle boss", source=ESTIMATE)
    base_thickness: float = given(6.0, "mm", why="Stand's base", source=ESTIMATE)
    base_width: float = given(80.0, "mm", why="Holds the battery holder", source=ESTIMATE)
    column_width: float = given(30.0, "mm", why="Stand's column", source=ESTIMATE)
    column_depth: float = given(14.0, "mm", why="Stand's column", source=ESTIMATE)
    fore_column_y: float = given(-62.0, "mm", why="Under the fore boom", source=ESTIMATE)
    aft_column_y: float = given(100.0, "mm", why="Under the aft boom", source=ESTIMATE)
    lead_room: float = given(24.0, "mm", why="The lead turns clear of parts", source=ESTIMATE)
    lead_rise: float = given(30.0, "mm", why="The lead's straight runs", source=ESTIMATE)
    holder_recess: float = given(2.0, "mm", why="Locates the battery holder", source=ESTIMATE)
    switch_panel: float = given(
        2.0,
        "mm",
        why="Within the switch's panel range, so its clips hold",
        source="E-Switch RD11131100 drawing, suggested panel cutout",
    )
    wheel_gap: float = given(0.5, "mm", why="Wheel clear of the leg", source=ESTIMATE)
    screw: Metric = given(Metric.M3, "-", why="One screw type", source="ISO 4762")
    short_screw: float = given(
        10.0, "mm", why="Through one wall", source="ISO 4762 nominal lengths"
    )
    long_screw: float = given(
        16.0, "mm", why="Through the foot and plate", source="ISO 4762 nominal lengths"
    )
    dowel_diameter: float = given(3.0, "mm", why="Stock dowel", source="ISO 8734")
    short_dowel: float = given(12.0, "mm", why="Across a fork hub", source="ISO 8734")
    leg_dowel: float = given(14.0, "mm", why="Across the leg root", source="ISO 8734")
    pivot_dowel: float = given(20.0, "mm", why="Through the bracket", source="ISO 8734")
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

    structure_material: str = given(
        "PETG Anthracite Grey",
        "-",
        why="One dark tone for the stand, plate and brackets, so the gear reads against them",
        source="design input; the spool is in the catalogue",
    )
    gear_material: str = given(
        "PETG Signal White",
        "-",
        why="Every part that moves with the gear in one light tone, so the retraction reads",
        source="design input; the spool is in the catalogue",
    )
    tyre_material: str = given(
        "PETG Jet Black",
        "-",
        why="The wheels read as tyres",
        source="design input; the spool is in the catalogue",
    )

    def mm(self, metres: float) -> float:
        return metres * 1000.0 * self.scale

    @property
    def wheel_radius(self) -> float:
        return self.mm(self.wheel_radius_m)

    @property
    def wheel_width(self) -> float:
        return self.mm(self.wheel_width_m)

    @property
    def joint_x(self) -> float:
        return self.mm(self.joint_m)

    @property
    def tube_length(self) -> float:
        return self.mm(self.tube_m)

    @property
    def leg_length(self) -> float:
        return self.mm(self.leg_m)

    @property
    def plate_rise(self) -> float:
        return self.mm(self.shaft_drop_m)

    @property
    def plate_outline(self) -> tuple[tuple[float, float], ...]:
        return tuple((self.mm(x), self.mm(y)) for x, y in PLATE_OUTLINE_M)

    @property
    def fork_half(self) -> float:
        return self.spider / 2 + self.fits.sliding

    @property
    def bored(self) -> float:
        return self.shaft_diameter + 2 * self.fits.sliding

    @property
    def pivot_bore(self) -> float:
        return clearance(self.screw, fits=self.fits)

    @property
    def insert_length(self) -> float:
        return insert_size(self.screw, fits=self.fits, stock=self.stock).length

    @property
    def output_radius(self) -> float:
        return pitch_radius(self.output_teeth, self.module)

    @property
    def motor_radius(self) -> float:
        return pitch_radius(self.motor_teeth, self.module)

    @property
    def rack_radius(self) -> float:
        return pitch_radius(self.rack_teeth, self.module)

    @property
    def rack_travel_deg(self) -> float:
        return RETRACTED_DEG * self.output_teeth / self.rack_teeth

    def drive_turn(self, shaft_deg: float) -> float:
        return shaft_deg * self.output_teeth / self.motor_teeth

    def _level(self, shaft: float) -> Location:
        return Location(
            Plane(
                origin=(self.joint_x, 0.0, shaft),
                x_dir=second_along(RIGHT),
                z_dir=tube_along(RIGHT),
            )
        ) * Pos(Z=self.tube_length)

    @property
    def shaft_level(self) -> float:
        end = self._level(0.0)
        tip = Location(normal_to(leg_along(RIGHT), through=end)) * Pos(Z=self.leg_length)
        return self.wheel_radius - tip.position.Z

    @property
    def plate_bottom(self) -> float:
        return self.shaft_level + self.plate_rise

    @property
    def plate_top(self) -> float:
        return self.plate_bottom + self.plate_thickness

    @property
    def shaft_at(self) -> Location:
        return Location((0.0, 0.0, self.shaft_level))

    @property
    def shaft_frame(self) -> Location:
        return Location(Plane(origin=self.shaft_at.position, x_dir=AFT, z_dir=ALONG))

    @property
    def shaft_half(self) -> float:
        return self.joint_x - self.fork_reach

    def joint(self, side: float) -> Location:
        return Location((side * self.joint_x, 0.0, self.shaft_level))

    def yoke(self, side: float) -> Location:
        return Location(Plane(origin=self.joint(side).position, x_dir=UP, z_dir=(side, 0.0, 0.0)))

    def tube(self, side: float) -> Location:
        return Location(
            Plane(
                origin=self.joint(side).position, x_dir=second_along(side), z_dir=tube_along(side)
            )
        )

    def spider_frame(self, side: float) -> Location:
        return Location(Plane(origin=self.joint(side).position, x_dir=UP, z_dir=spider_up(side)))

    def first_pin(self, side: float) -> Location:
        return self.yoke(side) * Rot(Y=90.0)

    def second_pin(self, side: float) -> Location:
        return self.tube(side) * Rot(Y=90.0)

    def yoke_screw_spots(self, side: float) -> tuple[Location, ...]:
        turned = [Rot(Y=sign * 90.0) for sign in (1.0, -1.0)]
        return tuple(self.yoke(side) * each * Pos(Z=self.spider / 2) for each in turned)

    def tube_screw_spots(self, side: float) -> tuple[Location, ...]:
        turned = [Rot(Y=sign * 90.0) for sign in (1.0, -1.0)]
        return tuple(self.tube(side) * each * Pos(Z=self.spider / 2) for each in turned)

    def hub_pin(self, side: float) -> Location:
        at = -self.fork_reach - self.fork_base / 2
        return self.yoke(side) * Pos(Z=at, Y=-self.short_dowel / 2) * Rot(X=-90.0)

    def tube_end(self, side: float) -> Location:
        return self.tube(side) * Pos(Z=self.tube_length)

    def leg_pin(self, side: float) -> Location:
        return self.tube_end(side) * Pos(X=-self.leg_dowel / 2) * Rot(Y=90.0)

    def axle(self, side: float) -> Location:
        tip = Location(normal_to(leg_along(side), through=self.tube_end(side)))
        at = tip * Pos(Z=self.leg_length)
        return Location(Plane(origin=at.position, x_dir=AFT, z_dir=(side, 0.0, 0.0)))

    def axle_face(self, side: float) -> Location:
        return self.axle(side) * Pos(Z=-self.wheel_width / 2 - self.wheel_gap)

    def leg_boss(self, side: float) -> Location:
        return self.axle_face(side) * Pos(Z=-self.boss_length / 2)

    def leg_frame(self, side: float) -> Location:
        root, boss = self.tube_end(side), self.leg_boss(side)
        return Location(normal_to(line_through(root, boss).direction, through=root))

    def leg_reach(self, side: float) -> float:
        return line_between(self.tube_end(side), self.leg_boss(side)).length

    @property
    def head_room(self) -> float:
        return self.wheel_width + self.wheel_gap + self.insert_length - self.long_screw

    def axle_screw_at(self, side: float) -> Location:
        return self.axle_face(side) * Pos(Z=self.long_screw - self.insert_length)

    def hanger(self, side: float) -> Location:
        return self.tube(side) * Pos(Z=self.hanger_at)

    def hanger_top(self, side: float) -> Location:
        at = self.hanger(side).position
        return Location((at.X, at.Y, self.plate_bottom))

    def hanger_drop(self, side: float) -> float:
        return self.plate_bottom - self.hanger(side).position.Z

    @property
    def bracket_height(self) -> float:
        top = self.pivot.position.Z - self.plate_top
        return top + 2 * self.fork_wall + self.fits.structural_wall + self.plate_thickness

    def hanger_spots(self, side: float) -> tuple[Location, ...]:
        at = self.hanger(side).position
        half = self.spot_spacing / 2
        return tuple(Location((at.X, at.Y + y, self.plate_bottom)) for y in (-half, half))

    def pillow(self, side: float) -> Location:
        return Location((side * self.pillow_x, 0.0, self.plate_bottom))

    def pillow_spots(self, side: float) -> tuple[Location, ...]:
        half = self.spot_spacing / 2
        return tuple(self.pillow(side) * Pos(Y=y) for y in (-half, half))

    @property
    def pivot(self) -> Location:
        return self.shaft_at * Pos(Z=self.rack_radius + self.output_radius)

    @property
    def rack_frame(self) -> Location:
        return Location(Plane(origin=self.pivot.position, x_dir=AFT, z_dir=ALONG))

    @property
    def rack_phase(self) -> float:
        phase = mesh_phase(self.rack_frame, self.rack_teeth, self.shaft_frame, self.output_teeth)
        return phase % (360.0 / self.rack_teeth)

    @property
    def rack_pose(self) -> Location:
        return self.rack_frame * Rot(Z=self.rack_phase)

    @property
    def rack_ends(self) -> tuple[float, float]:
        mesh = -90.0
        start = mesh - self.rack_lead_deg - self.rack_travel_deg - self.rack_margin_deg
        end = mesh + self.rack_margin_deg
        return self.rack_gap(start - self.rack_phase), self.rack_gap(end - self.rack_phase)

    def rack_gap(self, angle: float) -> float:
        pitch = 360.0 / self.rack_teeth
        return (round(angle / pitch - 1 / 2) + 1 / 2) * pitch

    @property
    def rack_wedge(self) -> tuple[tuple[float, float], ...]:
        start, end = self.rack_ends
        reach = 2 * self.rack_radius
        rays = [Rot(Z=angle) * Pos(X=reach) for angle in (start, (start + end) / 2, end)]
        return ((0.0, 0.0), *((ray.position.X, ray.position.Y) for ray in rays))

    @property
    def pivot_dowel_at(self) -> Location:
        return self.rack_frame * Pos(Z=-self.pivot_dowel / 2)

    @property
    def motor_width(self) -> float:
        return vendor_extent(MOTOR).size.X

    @property
    def motor_height(self) -> float:
        return vendor_extent(MOTOR).size.Y

    @property
    def motor_length(self) -> float:
        return motor.SHAFT_START - vendor_extent(MOTOR).min.Z

    @property
    def motor_level(self) -> float:
        return self.plate_bottom - self.motor_height / 2 - self.fits.sliding

    @property
    def pinion_centre(self) -> Location:
        centre = self.rack_radius + self.motor_radius
        circle = Edge.make_circle(centre, Plane(origin=self.pivot.position, x_dir=AFT, z_dir=ALONG))
        far = 2 * centre
        line = Edge.make_line((0.0, -far, self.motor_level), (0.0, 0.0, self.motor_level))
        (found,) = circle.find_intersection_points(line)
        return Location(found)

    @property
    def pinion_frame(self) -> Location:
        return Location(Plane(origin=self.pinion_centre.position, x_dir=AFT, z_dir=ALONG))

    @property
    def pinion_turn(self) -> float:
        return mesh_phase(self.pinion_frame, self.motor_teeth, self.rack_pose, self.rack_teeth)

    @property
    def pinion_pose(self) -> Location:
        return self.pinion_frame * Rot(Z=self.pinion_turn)

    @property
    def drive_frame(self) -> Location:
        return Location(
            Plane(origin=self.pinion_centre.position, x_dir=AFT, z_dir=(-1.0, 0.0, 0.0))
        )

    @property
    def motor_tip(self) -> Location:
        return self.pinion_frame * Pos(Z=-self.gear_width / 2)

    @property
    def motor_at(self) -> Location:
        tip = Location(Plane(origin=self.motor_tip.position, x_dir=AFT, z_dir=(-1.0, 0.0, 0.0)))
        return tip * Pos(Z=-vendor_reach(MOTOR_OUTPUT, Axis.Z))

    @property
    def saddle(self) -> Location:
        at = self.pinion_centre.position
        return Location((self.gear_width / 2 + self.fits.sliding, at.Y, self.plate_bottom))

    @property
    def saddle_width(self) -> float:
        return self.motor_width + 2 * self.fits.sliding + 2 * self.pillow_width

    @property
    def saddle_spots(self) -> tuple[Location, ...]:
        off = (self.motor_width + self.pillow_width) / 2 + self.fits.sliding
        along = 3 * self.motor_length / 4
        return tuple(self.saddle * Pos(X=along, Y=y) for y in (-off, off))

    def column_spots(self, y: float) -> tuple[Location, ...]:
        off = self.column_width / 4
        return tuple(Location((x, y, self.plate_bottom)) for x in (-off, off))

    @property
    def holder_at(self) -> Location:
        at = Location((0.0, self.holder_y, self.base_thickness - self.holder_recess))
        return at * Rot(Z=-90.0)

    @property
    def holder_y(self) -> float:
        length = self.holder_box.size.X
        return self.fore_column_y + (self.column_depth + length) / 2 + self.lead_room

    @property
    def holder_box(self) -> BoundBox:
        return vendor_extent(BATTERY_HOLDER)

    @property
    def holder_length(self) -> float:
        return self.holder_box.size.X

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
    def lead_bend(self) -> float:
        return wire.BEND_DIAMETERS * wire.DIAMETER

    @property
    def switch_ends(self) -> switch.Terminals:
        return switch.terminals(SWITCH)

    @property
    def holder_leads(self) -> battery_holder.Leads:
        return battery_holder.leads(BATTERY_HOLDER)

    @property
    def switch_terminals(self) -> Location:
        return Location((self.switch_face * Pos(Z=-self.switch_depth)).position)

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
    def lead_up_the_column(self) -> Location:
        off = self.holder_box.size.X / 2 + self.lead_room / 2
        return self.holder_at * Pos(X=off, Z=self.holder_box.size.Z / 2 + self.lead_rise)

    @property
    def lead_end(self) -> Location:
        return self.saddle * Pos(X=self.motor_length, Z=self.plate_bottom_to_motor)

    @property
    def plate_bottom_to_motor(self) -> float:
        return self.motor_level - self.plate_bottom

    @property
    def lead_behind_the_motor(self) -> Location:
        return self.lead_end * Pos(X=self.lead_room)

    @property
    def lead_under_the_motor(self) -> Location:
        return self.lead_behind_the_motor * Pos(Z=-self.lead_rise)

    @property
    def poses(self) -> tuple[Pose, ...]:
        return tuple(
            Pose(
                name=f"gear at {n * POSE_STEP_DEG:g}",
                joints={DRIVE: self.drive_turn(n * POSE_STEP_DEG)},
            )
            for n in range(POSE_COUNT)
        )


MASTER = CessnaMaster()
