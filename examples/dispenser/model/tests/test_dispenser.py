from pathlib import Path

import pytest
from build123d import Align, Box, Cylinder, Location, Pos, Rot, extrude
from cad.assembly.mass import weight
from cad.assembly.tree import assembled
from cad.design.bom import bom
from cad.design.build import built
from cad.design.catalogue import Kind
from cad.design.package import load
from cad.design.world import World
from cad.library.bought.vendor import Bought
from cad.library.features.hardware import Fastening
from cad.library.standard.fasteners import SCREWS

from dispenser import models
from dispenser.assemblies.dispenser import (
    ACTUATOR_NAME,
    BUZZER_NAME,
    LED_NAME,
    PICO_NAME,
    POWER_NAME,
    PRODUCT,
    REED_NAME,
    harness,
)
from dispenser.catalogue import CATALOGUE
from dispenser.features import front_sector
from dispenser.master import MASTER
from dispenser.parts.base import base
from dispenser.parts.carousel import carousel
from dispenser.parts.drawer import drawer
from dispenser.parts.lid import lid
from dispenser.parts.plate import plate

TARGET_LANDED_USD = 110.0  # prd.md R8, the founder's target
FREIGHT_AND_DUTY_SHARE = 0.10  # estimate: small-parcel freight and duty on the parts, not quoted
PER_UNIT_CONSUMABLE_USD = 1.0  # consumables priced per unit sit under this; spools above
FINGERTIP_MM = 20.0  # estimate: a large index fingertip's breadth, Pheasant, Bodyspace, not opened
HAND_BREADTH_MM = 95.0  # estimate: 95th-percentile male hand breadth, Pheasant, not opened
REED_RELEASES_MM = 17.0  # Littelfuse 59140 datasheet, sensitivity S: releases by 17 mm
LOUD_DB = 85.0  # prd.md R4
DOSE_GRAMS = 3.2  # estimate: eight tablets of about 0.4 g, not weighed
PILL_ON_PETG_FRICTION = 0.3  # estimate: coated tablet sliding on printed PETG, not measured
STANDARD_GRAVITY_M_S2 = 9.80665
MM_PER_M = 1000.0
G_PER_KG = 1000.0
SLICE_MM = 0.1
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)
DESIGN = Path(__file__).parents[2]


@pytest.fixture(scope="session")
def dispenser() -> Fastening:
    return assembled(PRODUCT)


def gate_slice(height: float) -> object:
    on = Location(MASTER.carousel_bottom) * Pos(Z=height)
    return extrude(front_sector(MASTER, on), amount=SLICE_MM)


@pytest.mark.check(
    does_not_catch="Pills smaller than the running gap creeping under the home sector, and"
    " pills thrown over the pocket walls when the drum is tipped.",
    subjects=("carousel", "base"),
)
def test_r1_at_rest_the_home_sector_closes_the_gate() -> None:
    covering = gate_slice(MASTER.wall / 2)
    assert abs((covering & carousel(MASTER).solid()).volume - covering.volume) < 1e-3


@pytest.mark.check(
    does_not_catch="How pills tumble and pile as they drop; a dose that bridges in its pocket.",
    subjects=("drawer", "carousel"),
)
def test_r1_the_tray_takes_a_whole_pocket() -> None:
    sector = front_sector(MASTER, Location(MASTER.carousel_bottom))
    pocket = sector.area * MASTER.pocket_height
    tray = drawer(MASTER).solid()
    floor = MASTER.drawer_bottom.offset(MASTER.pull_height + MASTER.wall)
    room = Location(floor) * Cylinder(MASTER.radius, MASTER.tray_depth, align=BOTTOM)
    assert room.volume - (room & tray).volume > pocket


@pytest.mark.check(
    does_not_catch="Pills that do not fit a pocket at all; the schedule set in firmware.",
    subjects=("carousel",),
)
def test_r2_the_carousel_holds_four_doses_a_day_for_a_week() -> None:
    made = carousel(MASTER).solid()
    floor = Location(MASTER.carousel_bottom) * Pos(Z=MASTER.wall / 2)
    middle = (MASTER.pocket_start + MASTER.pocket_reach) / 2
    turns = [Rot(Z=-90 + n * MASTER.sector) * Pos(X=middle) for n in range(MASTER.sectors)]
    open_bottoms = [turn for turn in turns if not made.is_inside((floor * turn).position)]
    assert len(open_bottoms) == 4 * 7


@pytest.mark.check(
    does_not_catch="Dexterity, tremor, eyesight, and how hard the lid is to lift off.",
    subjects=("carousel", "lid"),
)
def test_r3_a_fingertip_reaches_into_every_pocket_and_the_lid_is_held_by_nothing(
    dispenser: Fastening,
) -> None:
    reach = MASTER.pocket_reach - MASTER.fits.sliding - FINGERTIP_MM / 2
    tip = Location(MASTER.carousel_bottom) * Rot(Z=-90 + MASTER.sector) * Pos(X=reach)
    finger = tip * Cylinder(FINGERTIP_MM / 2, MASTER.pocket_height, align=BOTTOM)
    assert (finger & carousel(MASTER).solid()).volume < 1e-6
    lid_mates = [mate for mate in dispenser.mates if mate.child_part.name == "lid"]
    assert lid_mates
    assert all(not mate.fasteners for mate in lid_mates)


@pytest.mark.check(
    does_not_catch="Sound through the plate's bore and the feet's gap, the parent's hearing, and"
    " how bright the light reads in daylight; the dB figure is the maker's at 10 cm and 3 V.",
    subjects=(BUZZER_NAME, LED_NAME),
)
def test_r4_a_loud_sounder_and_a_light_on_the_front(dispenser: Fastening) -> None:
    names = [part.name for part in dispenser.parts]
    assert names.count(BUZZER_NAME) == 1
    assert models.BUZZER_DB >= LOUD_DB
    (light,) = [part for part in dispenser.parts if part.name == LED_NAME]
    assert -MASTER.radius + MASTER.fits.sliding >= light.solid().bounding_box().min.Y


@pytest.mark.check(
    does_not_catch="The Littelfuse figures hold for its own actuator in free air; the PETG"
    " between them, stray fields and the firmware's debounce are not checked.",
    subjects=(REED_NAME, ACTUATOR_NAME),
)
def test_r5_the_sensor_sees_the_drawer_shut_and_lets_go_when_it_opens(
    dispenser: Fastening,
) -> None:
    (sensor,) = [part for part in dispenser.parts if part.name == REED_NAME]
    (magnet,) = [part for part in dispenser.parts if part.name == ACTUATOR_NAME]
    shut = sensor.solid().distance_to(magnet.solid())
    opened = sensor.solid().distance_to(Pos(Y=-MASTER.drawer_travel) * magnet.solid())
    assert shut <= models.REED_ACTIVATES
    assert opened >= REED_RELEASES_MM


@pytest.mark.check(
    does_not_catch="Wi-Fi range and setup, the message service, and a power cut.",
    subjects=(PICO_NAME,),
)
def test_r6_a_wifi_board_is_powered_from_the_wall(dispenser: Fastening) -> None:
    assert [part.name for part in dispenser.parts].count(PICO_NAME) == 1
    powered = [route for route in harness(MASTER) if route.cable.name == POWER_NAME]
    (route,) = powered
    assert route.plugged[0].part.name == PICO_NAME


@pytest.mark.check(
    does_not_catch="The pull's force, and grip with arthritis.",
    subjects=("drawer", "base"),
)
def test_r7_a_large_hand_fits_the_pull_and_no_button_shows(dispenser: Fastening) -> None:
    lip = Location(MASTER.drawer_bottom) * Pos(Y=MASTER.drawer_front + MASTER.pull_reach / 2)
    fingers = lip * Box(
        HAND_BREADTH_MM,
        MASTER.pull_reach / 2,
        MASTER.pull_height - MASTER.fits.sliding,
        align=BOTTOM,
    )
    assert (fingers & drawer(MASTER).solid()).volume < 1e-6
    bought_outside = [
        part.name
        for part in dispenser.parts
        if isinstance(part, Bought) and -MASTER.inside_radius > part.solid().bounding_box().min.Y
    ]
    assert bought_outside == [LED_NAME]


@pytest.mark.check(
    does_not_catch="Packaging, payment fees and exchange rates; the printing rate and several"
    " prices are estimates (see the catalogue).",
    subjects=("bill",),
)
def test_r8_the_landed_cost_is_under_the_target(dispenser: Fastening) -> None:
    lines = bom(World(built=built(load(DESIGN))))
    bought = sum(line["qty"] * line["unit_price"] for line in lines if line["kind"] == "bought")
    plastic = sum(line["unit_price"] for line in lines if line["kind"] == "made")
    consumed = sum(
        item.unit_price
        for item in CATALOGUE
        if item.kind is Kind.CONSUMABLE and item.unit_price < PER_UNIT_CONSUMABLE_USD
    )
    landed = (bought + plastic + consumed) * (1 + FREIGHT_AND_DUTY_SHARE)
    assert landed < TARGET_LANDED_USD, f"landed ${landed:.2f}"


@pytest.mark.check(
    does_not_catch="The real dose weight and tablet friction (both estimated), the carousel"
    " rubbing the floor, and the stepper's torque at the firmware's step rate.",
    subjects=("carousel", "Adafruit 858 28BYJ-48 stepper"),
)
def test_r9_the_stepper_turns_a_full_carousel() -> None:
    pills_n = MASTER.doses * DOSE_GRAMS / G_PER_KG * STANDARD_GRAVITY_M_S2
    middle_m = (MASTER.pocket_start + MASTER.pocket_reach) / 2 / MM_PER_M
    assert pills_n * PILL_ON_PETG_FRICTION * middle_m < models.STEPPER_PULL_IN_NM
    assert weight(carousel(MASTER)) > 0


@pytest.mark.check(
    does_not_catch="Screws seen through the plate's buzzer bore.",
    subjects=("base", "plate"),
)
def test_s1_every_screw_head_faces_down(dispenser: Fastening) -> None:
    screws = [part for part in dispenser.parts if isinstance(part, SCREWS)]
    assert screws
    for screw in screws:
        assert (screw.pose * Pos(Z=1)).position.Z < screw.pose.position.Z


@pytest.mark.check(
    does_not_catch="The seam's gap and colour match.",
    subjects=("base", "lid"),
)
def test_s2_base_and_lid_are_one_low_drum() -> None:
    shell = base(MASTER).solid().bounding_box()
    cap = lid(MASTER).solid().bounding_box()
    assert abs(shell.size.X - cap.size.X) < 1e-6
    assert cap.max.Z < shell.size.X


@pytest.mark.check(
    does_not_catch="The power cable at the back, the feet, and the plate's bore underneath.",
    subjects=("base", "lid", "drawer"),
)
def test_s3_only_the_drawer_and_the_light_break_the_drum(dispenser: Fastening) -> None:
    ring = Cylinder(MASTER.radius + 1, MASTER.top.origin.Z, align=BOTTOM) - Cylinder(
        MASTER.inside_radius + MASTER.fits.sliding, MASTER.top.origin.Z, align=BOTTOM
    )
    reaching = {
        part.name
        for part in dispenser.parts
        if part.name not in ("base", "lid") and (part.solid() & ring).volume > 1e-6
    }
    assert reaching == {"drawer", LED_NAME}


@pytest.mark.check(
    does_not_catch="The colour of a real spool against a sample.",
    subjects=("base", "plate", "carousel", "lid", "drawer"),
)
def test_s4_every_printed_part_is_one_material(dispenser: Fastening) -> None:
    assert len({part.material for part in dispenser.parts if part.printed}) == 1


@pytest.mark.check(
    does_not_catch="Strength, fit and finish.",
    subjects=("base", "plate", "carousel", "lid", "drawer"),
)
@pytest.mark.parametrize("build", [base, plate, carousel, lid, drawer])
def test_m3_each_part_builds_from_the_master_alone(build) -> None:
    assert build(MASTER).solid().is_valid
