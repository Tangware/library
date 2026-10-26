from collections import Counter
from pathlib import Path

from build123d import (
    Align,
    Box,
    BuildPart,
    Color,
    Compound,
    Cylinder,
    GridLocations,
    Locations,
    Mode,
    Pos,
    Solid,
    Sphere,
    add,
)
from cad.library.bought.vendor import placed_solids
from cad.library.shapes import Brep, built

VENDOR = Path(__file__).parents[2] / "vendor"
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)

STEPPER_GRAMS = 37.0  # Adafruit product 858 page
SHAFT_DIAMETER = 5.0  # 28BYJ-48 drawing, Adafruit: Ø5 shaft
SHAFT_FLATS = 3.0  # same drawing: 3 mm across the flats
FLAT_LENGTH = 6.0  # same drawing: the flats run 6 mm down from the shaft's end
SHAFT_BOSS_DIAMETER = 9.0  # the Adafruit 858 STEP: the Ø9 boss round the shaft

BUMPER_DIAMETER = 7.92  # 3M Bumpon SJ5302 product data, Digi-Key SJ5302-7-ND
BUMPER_HEIGHT = 2.16  # same
BUMPER_GRAMS = 0.1  # estimate: a 7.9 mm polyurethane dome

LED_FLANGE = 5.8  # T-1 3/4 (5 mm) LED package: Ø5.8 flange, common outline


def bumper() -> Brep:
    with BuildPart() as foot:
        Cylinder(BUMPER_DIAMETER / 2, BUMPER_HEIGHT, align=BOTTOM)
        with Locations(Pos(Z=BUMPER_HEIGHT)):
            Sphere(BUMPER_DIAMETER / 2, mode=Mode.INTERSECT)
    return built(foot)


STEPPER_STEP = VENDOR / "stepper_28byj48.step.gz"
STATOR = "stator"
ROTOR = "rotor"
STATOR_SOLIDS = 4  # the Adafruit 858 STEP: the body, its boss, the wire box and the tabs
ROTOR_GRAMS = 0.9  # estimate: a Ø5 x 8.8 mm steel shaft; its gear train counts in the stator


def is_shaft(solid: Solid) -> bool:
    size = solid.bounding_box().size
    return abs(size.X - SHAFT_DIAMETER) < 0.01 and abs(size.Y - SHAFT_DIAMETER) < 0.01


def flatted_shaft(solids: list[Solid]) -> list[Solid]:
    (shaft,) = [solid for solid in solids if is_shaft(solid)]
    box = shaft.bounding_box()
    with BuildPart() as flatted:
        add(shaft)
        with (
            Locations(Pos(box.center().X, box.center().Y, box.max.Z)),
            GridLocations(SHAFT_FLATS + (SHAFT_DIAMETER - SHAFT_FLATS) / 2, 0, 2, 1),
        ):
            Box(
                (SHAFT_DIAMETER - SHAFT_FLATS) / 2,
                SHAFT_DIAMETER,
                FLAT_LENGTH,
                align=(Align.CENTER, Align.CENTER, Align.MAX),
                mode=Mode.SUBTRACT,
            )
    (cut,) = flatted.part.solids()
    return [cut if solid is shaft else solid for solid in solids]


def stepper() -> Compound:
    pieces = []
    for solid, look, _ in placed_solids(STEPPER_STEP, flatted_shaft):
        ((colour, _),) = Counter(look).most_common(1)
        if colour is not None:
            solid.color = Color(*colour)
        solid.label = ROTOR if is_shaft(solid) else STATOR
        pieces.append(solid)
    return Compound(children=pieces)


LED_BODY = 5.0  # T-1 3/4 (5 mm) LED package: Ø5 body, common outline
LED_HEIGHT = 8.6  # Kingbright WP7113ID5V datasheet: dome tip to flange underside
LED_FLANGE_THICKNESS = 1.0  # same datasheet: flange 1.0 mm thick at most
LED_GRAMS = 0.3  # estimate: a 5 mm epoxy LED with leads

BUZZER_GRAMS = 2.0  # Soberton WST-1205S datasheet
BUZZER_DIAMETER = 12.0  # same datasheet
BUZZER_BODY = 9.5  # same datasheet: body height without pins
BUZZER_DB = 85.0  # same datasheet: 85 dB(A) at 10 cm, 5 V
BUZZER_AMPS = 0.040  # same datasheet: mean current, 40 mA max

PICO_GRAMS = 4.0  # estimate: the Pico 2 W's mass is not in its datasheet
PICO_AMPS = 0.1  # estimate: an RP2350 with the Wi-Fi radio on, not measured

STEPPER_VOLTS = 5.0  # 28BYJ-48 datasheet, MikroElektronika
STEPPER_PHASE_OHMS = 50.0  # same datasheet, 50 Ω ± 7 % per phase
STEPPER_PHASES_ON = 2  # two phases on at once in full-step drive
STEPPER_PULL_IN_NM = 0.0294  # 28BYJ-48 datasheet: pull-in torque ≥ 300 gf·cm at 100 pps
LED_AMPS = 0.0175  # Kingbright WP7113ID5V datasheet, maximum at 5 V

DRIVER_GRAMS = 1.5  # Adafruit product 3297 page
DRIVER_LENGTH = 25.4  # Adafruit DRV8833 Eagle board outline (adafruit/Adafruit-DRV8833-PCB)
DRIVER_WIDTH = 17.78  # same board outline
DRIVER_HOLE_PITCH = 20.32  # same board, two plated holes along one long edge
DRIVER_HOLE_INSET = 2.54  # same board, hole centres in from the long edge
DRIVER_HOLE = 2.5  # same board, plated hole drill
DRIVER_BOARD = 1.6  # estimate: standard FR4 thickness
DRIVER_PARTS = 1.5  # estimate: the HTSSOP package and passives; Adafruit gives 3 mm overall


def drv8833() -> Brep:
    with BuildPart() as board:
        Box(DRIVER_LENGTH, DRIVER_WIDTH, DRIVER_BOARD, align=BOTTOM)
        with Locations(Pos(Z=DRIVER_BOARD)):
            Box(DRIVER_LENGTH / 2, DRIVER_WIDTH / 2, DRIVER_PARTS, align=BOTTOM)
        with (
            Locations(Pos(Y=DRIVER_WIDTH / 2 - DRIVER_HOLE_INSET)),
            GridLocations(DRIVER_HOLE_PITCH, 0, 2, 1),
        ):
            Cylinder(DRIVER_HOLE / 2, DRIVER_BOARD, align=BOTTOM, mode=Mode.SUBTRACT)
    return built(board)


REED_LENGTH = 23.0  # Littelfuse 59140 datasheet: body 23 x 14 x 6 mm
REED_WIDTH = 14.0  # same
REED_HEIGHT = 6.0  # same
REED_HOLE_PITCH = 14.0  # same: two mounting slots at 14.00 mm pitch
REED_HOLE = 3.2  # same: slots 3.20 x 3.81 mm, modelled as Ø3.2 holes
REED_GRAMS = 3.0  # estimate: the datasheet gives no mass
REED_ACTIVATES = 9.0  # same datasheet, sensitivity S: activates within 9 mm with the 57140 actuator
ACTUATOR_GRAMS = 4.0  # estimate: a 23 x 14 x 6 mm magnet in a plastic case


def reed_sensor() -> Brep:
    with BuildPart() as sensor:
        Box(REED_LENGTH, REED_WIDTH, REED_HEIGHT, align=BOTTOM)
        with GridLocations(REED_HOLE_PITCH, 0, 2, 1):
            Cylinder(REED_HOLE / 2, REED_HEIGHT, align=BOTTOM, mode=Mode.SUBTRACT)
    return built(sensor)


def actuator() -> Brep:
    with BuildPart() as block:
        Box(REED_LENGTH, REED_WIDTH, REED_HEIGHT, align=BOTTOM)
    return built(block)
