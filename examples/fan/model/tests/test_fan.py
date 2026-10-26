from pathlib import Path

import pytest
from build123d import Align, Axis, Cylinder, GeomType, Location, Pos, Rot
from cad.assembly.tree import assembled
from cad.design.bom import bom
from cad.design.build import built
from cad.design.catalogue import Kind
from cad.design.package import load
from cad.design.world import World
from cad.library.bought.query import axis_of
from cad.library.bought.vendor import Bought
from cad.library.features.hardware import Fastening
from cad.library.shapes import Part, radius_of
from cad.library.standard.fasteners import SCREWS

from fan import models
from fan.assemblies.fan import BUTTON_NAME, DRIVER_NAME, FAN_NAME, PRODUCT, STEPPER_NAME, XIAO_NAME
from fan.catalogue import CATALOGUE
from fan.master import MASTER
from fan.parts.cover import cover
from fan.parts.floor import floor
from fan.parts.head import head
from fan.parts.puck import puck

QUIET_ROOM_DBA = 25.0  # prd.md R1
TARGET_LANDED_USD = 36.0  # prd.md R8, the founder's target
FREIGHT_AND_DUTY_SHARE = 0.10  # estimate: small-parcel freight and duty on the parts, not quoted
USB_DEFAULT_AMPS = 0.5  # USB 2.0 default port current, what a USB-C source gives unasked
TEST_FINGER = 12.0  # IEC 61032 test probe B, Ø12 mm
PER_FAN_CONSUMABLE_USD = 1.0  # consumables priced per fan sit under this; spools and rolls above
TURNING = ("head", "cover", FAN_NAME)
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)
DESIGN = Path(__file__).parents[2]


@pytest.fixture(scope="session")
def fan() -> Fastening:
    return assembled(PRODUCT)


def turns(part: Part) -> bool:
    return part.name in TURNING or part.group.startswith("fan/head")


@pytest.mark.check(
    does_not_catch="The stepper's and driver's noise, grille turbulence, shell resonance; "
    "the fan's dB(A) is its maker's figure at full speed, not measured in the shell.",
    subjects=(FAN_NAME,),
)
def test_r1_the_only_fan_is_rated_no_louder_than_a_quiet_room(fan: Fastening) -> None:
    fans = [part for part in fan.parts if isinstance(part, Bought) and part.name == FAN_NAME]
    assert len(fans) == 1
    assert models.FAN_DBA <= QUIET_ROOM_DBA


@pytest.mark.check(
    does_not_catch="The sweep's period and smoothness, set by firmware; shaft load and wear.",
    subjects=("head", "puck"),
)
@pytest.mark.parametrize("angle", [-MASTER.sweep, MASTER.sweep])
def test_r2_the_head_sweeps_45_degrees_each_way_clear_of_the_puck(angle: float) -> None:
    swung = Rot(Z=angle) * head(MASTER).solid()
    assert (swung & puck(MASTER).solid()).volume < 1e-6
    assert MASTER.sweep_range.high - MASTER.sweep_range.low == 2 * abs(angle)


@pytest.mark.check(
    does_not_catch="Inrush at start, the stepper's real drive current under the firmware, "
    "and sources that give less than USB 2.0 default power.",
    subjects=(FAN_NAME, STEPPER_NAME, XIAO_NAME),
)
def test_r3_it_draws_no_more_than_a_usb_port_gives_unasked(fan: Fastening) -> None:
    stepper = models.STEPPER_PHASES_ON * models.STEPPER_VOLTS / models.STEPPER_PHASE_OHMS
    drawn = {FAN_NAME: models.FAN_AMPS, STEPPER_NAME: stepper, XIAO_NAME: models.XIAO_AMPS}
    loads = [drawn[part.name] for part in fan.parts if part.name in drawn]
    assert len(loads) == len(drawn)
    assert sum(loads) <= USB_DEFAULT_AMPS


@pytest.mark.check(
    does_not_catch="What the firmware does with the button; the board's own reset and boot "
    "buttons, which sit inside the closed puck.",
    subjects=(BUTTON_NAME,),
)
def test_r4_one_button_is_the_only_control_outside(fan: Fastening) -> None:
    rise = MASTER.head_bottom.origin.Z - MASTER.top.origin.Z
    reach = Location(MASTER.top) * (
        Cylinder(MASTER.puck_radius, rise, align=BOTTOM)
        - Cylinder(MASTER.neck_radius, rise, align=BOTTOM)
    )
    outside = [
        part.name
        for part in fan.parts
        if isinstance(part, Bought) and not turns(part) and (part.solid() & reach).volume > 0
    ]
    assert outside == [BUTTON_NAME]


@pytest.mark.check(
    does_not_catch="Light through the white PETG wall itself, and through the USB-C opening "
    "around a plug.",
    subjects=(XIAO_NAME, DRIVER_NAME),
)
def test_r5_every_board_with_a_light_is_inside_the_closed_puck(fan: Fastening) -> None:
    boards = [part for part in fan.parts if part.name in (XIAO_NAME, DRIVER_NAME)]
    assert len(boards) == 2
    for board in boards:
        found = board.solid().bounding_box()
        assert found.min.Z > MASTER.floor_top.origin.Z
        assert found.max.Z < MASTER.top_under.origin.Z


@pytest.mark.check(
    does_not_catch="Smaller probes, the back grille, and a finger pushed at an angle.",
    subjects=("head",),
)
@pytest.mark.parametrize("turn", [22.5, 67.5])
def test_r7_a_test_finger_cannot_pass_the_front_grille(turn: float) -> None:
    first_slot = models.FAN_HUB + MASTER.grille_slot / 2
    middle = MASTER.fan_middle.position
    at = Location((0, MASTER.head_front, middle.Z)) * Rot(Y=turn) * Pos(X=first_slot)
    probe = Pos(at.position) * Rot(X=-90) * Cylinder(TEST_FINGER / 2, MASTER.insert_depth)
    assert (probe & head(MASTER).solid()).volume > 0


@pytest.mark.check(
    does_not_catch="Printer time, labour, packaging, payment fees; exchange rates move; "
    "several prices are estimates (see the catalogue).",
    subjects=("bill",),
)
def test_r8_the_landed_cost_is_under_the_target(fan: Fastening) -> None:
    lines = bom(World(built=built(load(DESIGN))))
    parts = sum(
        line["qty"] * line["unit_price"] for line in lines if line["kind"] in ("made", "bought")
    )
    consumed = sum(
        item.unit_price
        for item in CATALOGUE
        if item.kind is Kind.CONSUMABLE and item.unit_price < PER_FAN_CONSUMABLE_USD
    )
    landed = (parts + consumed) * (1 + FREIGHT_AND_DUTY_SHARE)
    assert landed < TARGET_LANDED_USD, f"landed ${landed:.2f}"


@pytest.mark.check(
    does_not_catch="Seams and gates seen from the front; screws seen through the grille.",
    subjects=("puck", "floor", "head", "cover"),
)
def test_s1_every_screw_seen_from_outside_faces_down_or_back(fan: Fastening) -> None:
    screws = [part for part in fan.parts if isinstance(part, SCREWS)]
    assert screws
    floor, ceiling = MASTER.floor_top.origin.Z, MASTER.top_under.origin.Z
    for screw in screws:
        out = Axis(screw.pose).direction
        inside = floor < screw.pose.position.Z < ceiling
        assert out.Z < -0.99 or out.Y > 0.99 or inside


@pytest.mark.check(
    does_not_catch="Edge breaks on the front and back outlines.",
    subjects=("head", "cover"),
)
@pytest.mark.parametrize("build", [head, cover])
def test_s2_every_corner_of_the_head_takes_one_radius(build) -> None:
    corners = {
        round(radius_of(face), 3)
        for face in build(MASTER).solid().faces()
        if face.geom_type == GeomType.CYLINDER
        and abs(axis_of(face).direction.Y) > 0.99
        and abs(face.center().X) > MASTER.fan_side / 2
    }
    assert len(corners) == 1


@pytest.mark.check(
    does_not_catch="The colour of a real spool against a sample.",
    subjects=("puck", "floor", "head", "cover"),
)
def test_s3_every_printed_part_is_one_material(fan: Fastening) -> None:
    assert len({part.material for part in fan.parts if part.printed}) == 1


@pytest.mark.check(
    does_not_catch="The USB-C cable and plug behind the puck.",
    subjects=("puck", "floor", "head"),
)
def test_s4_nothing_stands_wider_than_the_head(fan: Fastening) -> None:
    half = head(MASTER).solid().bounding_box().size.X / 2
    for part in fan.parts:
        found = part.solid().bounding_box()
        assert max(-found.min.X, found.max.X, -found.min.Y, found.max.Y) <= half + 1e-6


@pytest.mark.check(
    does_not_catch="Strength, fit and finish.", subjects=("puck", "floor", "head", "cover")
)
@pytest.mark.parametrize("build", [puck, floor, head, cover])
def test_m3_each_part_builds_from_the_master_alone(build) -> None:
    assert build(MASTER).solid().is_valid
