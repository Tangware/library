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
SWEEP = "head on stepper"
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)

FAN_GRAMS = 80.0  # Delta AFB0805L specification
STEPPER_GRAMS = 37.0  # Adafruit product 858 page
STEPPER_HOLDING_NM = 0.015  # same page: holding torque 150 g-cm, 15 N-mm
XIAO_TOP = 4.4  # the XIAO STEP: its tallest part stands 4.4 mm off the board's underside
XIAO_GRAMS = 3.0  # estimate: Seeed lists the XIAO family at about 3 g
BUTTON_GRAMS = 4.6  # Adafruit product 1445 page
DRIVER_GRAMS = 1.5  # Adafruit product 3297 page

DRIVER_LENGTH = 25.4  # Adafruit DRV8833 Eagle board outline (adafruit/Adafruit-DRV8833-PCB)
DRIVER_WIDTH = 17.78  # same board outline
DRIVER_HOLE_PITCH = 20.32  # same board, two plated holes along one long edge
DRIVER_HOLE_INSET = 2.54  # same board, hole centres in from the long edge
DRIVER_HOLE = 2.5  # same board, plated hole drill
DRIVER_BOARD = 1.6  # estimate: standard FR4 thickness
DRIVER_PARTS = (
    1.5  # estimate: the DRV8833's HTSSOP package and passives, Adafruit gives 3 mm overall
)


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


BUMPER_DIAMETER = 7.92  # 3M Bumpon SJ5302 product data, Digi-Key SJ5302-7-ND
BUMPER_HEIGHT = 2.16  # same
BUMPER_GRAMS = 0.1  # estimate: a 7.9 mm polyurethane dome


def bumper() -> Brep:
    with BuildPart() as foot:
        Cylinder(BUMPER_DIAMETER / 2, BUMPER_HEIGHT, align=BOTTOM)
        with Locations(Pos(Z=BUMPER_HEIGHT)):
            Sphere(BUMPER_DIAMETER / 2, mode=Mode.INTERSECT)
    return built(foot)


SHAFT_DIAMETER = 5.0  # 28BYJ-48 drawing, Adafruit: Ø5 shaft
SHAFT_FLATS = 3.0  # same drawing: 3 mm across the flats
FLAT_LENGTH = 6.0  # same drawing: the flats run 6 mm down from the shaft's end


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
    for solid, look, _ in placed_solids(STEPPER_STEP, flatted_shaft, detailed=True):
        ((colour, _),) = Counter(look).most_common(1)
        if colour is not None:
            solid.color = Color(*colour)
        solid.label = ROTOR if is_shaft(solid) else STATOR
        pieces.append(solid)
    return Compound(children=pieces)


XIAO_PORT_PART = "type-c v2"  # the XIAO STEP's name for its USB-C receptacle
XIAO_PORT_SOLIDS = 24  # the XIAO STEP models the receptacle as 24 solids
TAPE_THICKNESS = 1.1  # 3M VHB 5952 product data: 1.1 mm
XIAO_WIDTH = 17.5  # the XIAO STEP: 17.5 x 21 mm board
XIAO_LENGTH = 21.0  # same
XIAO_EDGE_PADS = (
    1.5  # estimate: the castellated pads' reach in from each long edge; the tape stays off them
)
TAPE_GRAMS = 0.4  # estimate: a 14.5 x 21 x 1.1 mm acrylic foam pad

FAN_DBA = 25.0  # Delta AFB0805L specification: average at 1 m, rated voltage
FAN_AMPS = 0.24  # same specification: rated input current; its limit spec is 0.45 A
STEPPER_VOLTS = 5.0  # 28BYJ-48 datasheet, MikroElektronika
STEPPER_PHASE_OHMS = 50.0  # same datasheet, 50 Ω ± 7 % per phase
STEPPER_PHASES_ON = 2  # two phases energised at once in full-step drive
XIAO_AMPS = 0.05  # estimate: an RP2040 board running, no radio
FAN_HUB = 20.0  # the fan STEP's rotor hub, Ø40


def vhb_pad() -> Brep:
    with BuildPart() as pad:
        Box(XIAO_WIDTH - 2 * XIAO_EDGE_PADS, XIAO_LENGTH, TAPE_THICKNESS, align=BOTTOM)
    return built(pad)


WIRE_26_AWG = 1.4  # estimate: silicone-insulated 26 AWG hook-up wire, outside diameter
BUTTON_TERMINALS = 5.5  # the Adafruit 1445 STEP: the terminals reach 5.5 mm below the body
DRIVER_BOARD_TOP = DRIVER_BOARD + DRIVER_PARTS


FAN_LEAD_WIRE = (
    1.4  # estimate: a UL 1007 24 AWG lead's outside diameter, the Delta AFB0805L's leads
)
FAN_LEAD_LENGTH = 309.0  # Delta AFB0805L specification: 309 ± 10 mm leads
STEPPER_LEAD = (0.0, -20.5, -8.0)  # estimate: the lead's exit on the Adafruit 858 STEP's wire box
STEPPER_LEAD_WIRE = 1.0  # estimate: the 28BYJ-48's five leads
STEPPER_LEAD_LENGTH = 250.0  # Adafruit 858 drawing: 250 mm leads
