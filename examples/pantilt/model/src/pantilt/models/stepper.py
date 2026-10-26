from build123d import (
    Align,
    Box,
    BuildPart,
    Compound,
    Cylinder,
    GridLocations,
    Locations,
    Mode,
    Pos,
    Solid,
)
from cad.library.shapes import built

DATASHEET = (
    "StepperOnline 17HS08-1004S product page, opened 2026-10-23: "
    "https://www.omc-stepperonline.com/nema-17-bipolar-1-8deg-16ncm-22-6oz-in-1a-3-7v-42x42x20mm-4-wires-17hs08-1004s"
)
FACE_STANDARD = "NEMA ICS 16 frame 17 mounting face (31 mm M3 square, 22 mm pilot); not opened"
FRAME = 42.3
HOLDING_TORQUE_NM = 0.16
BODY = 21.5
SHAFT_DIAMETER = 5.0
SHAFT_LENGTH = 20.0
FLAT_LENGTH = 16.5
FLAT_DEPTH = 0.5
PILOT_DIAMETER = 22.0
PILOT_HEIGHT = 2.0
HOLE_SPACING = 31.0
TAPPED_DEPTH = 4.5
M3_TAP_DRILL = 2.5
BELOW = (Align.CENTER, Align.CENTER, Align.MAX)
ABOVE = (Align.CENTER, Align.CENTER, Align.MIN)
FROM_THE_TIP = (Align.CENTER, Align.CENTER, Align.MAX)


STATOR = "stator"
ROTOR = "rotor"
ROTOR_GRAMS_ESTIMATED = 40.0
ROTOR_REACH_INSIDE = BODY / 2
LEAD_LENGTH = 400.0
LEAD_WIRE_MM = 1.0
LEAD_EXIT = Pos(X=-FRAME / 2, Z=-BODY / 2)
BORE_CLEARANCE = 0.1


def stator() -> Solid:
    with BuildPart() as body:
        Box(FRAME, FRAME, BODY, align=BELOW)
        with GridLocations(HOLE_SPACING, HOLE_SPACING, 2, 2):
            Cylinder(M3_TAP_DRILL / 2, TAPPED_DEPTH, align=BELOW, mode=Mode.SUBTRACT)
        Cylinder(PILOT_DIAMETER / 2, PILOT_HEIGHT, align=ABOVE)
        with Locations(Pos(Z=PILOT_HEIGHT)):
            Cylinder(
                SHAFT_DIAMETER / 2 + BORE_CLEARANCE,
                PILOT_HEIGHT + ROTOR_REACH_INSIDE + BORE_CLEARANCE,
                align=BELOW,
                mode=Mode.SUBTRACT,
            )
    (found,) = built(body).solids()
    return found


def rotor() -> Solid:
    with BuildPart() as shaft:
        with Locations(Pos(Z=-ROTOR_REACH_INSIDE)):
            Cylinder(SHAFT_DIAMETER / 2, SHAFT_LENGTH + ROTOR_REACH_INSIDE, align=ABOVE)
        with Locations(Pos(X=SHAFT_DIAMETER / 2, Z=SHAFT_LENGTH)):
            Box(2 * FLAT_DEPTH, SHAFT_DIAMETER, FLAT_LENGTH, align=FROM_THE_TIP, mode=Mode.SUBTRACT)
    (found,) = built(shaft).solids()
    return found


def solid() -> Compound:
    body, shaft = stator(), rotor()
    body.label, shaft.label = STATOR, ROTOR
    return Compound(children=[body, shaft])
