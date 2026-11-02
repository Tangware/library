from build123d import Keep, Plane, Solid
from cad.library.bought.servos import Servo, ServoModel
from cad.library.bought.vendor import Bought
from cad.library.shapes import Seat

SHAFT_START = 10.0
BODY_GRAMS_ESTIMATED = 9.2
SHAFT_GRAMS_ESTIMATED = 0.3


def body(solids: list[Solid]) -> list[Solid]:
    return [solid.split(Plane.XY.offset(SHAFT_START), keep=Keep.BOTTOM) for solid in solids]


def shaft(solids: list[Solid]) -> list[Solid]:
    return [solid.split(Plane.XY.offset(SHAFT_START), keep=Keep.TOP) for solid in solids]


GEARMOTOR = ServoModel(
    stall_nm=0.333,
    seconds_per_60_deg=0.09,
    armature_kg_m2=0.001,
    friction_nm=0.15,
    backlash_deg=1.0,
    p_coefficient=32,
)


class Gearmotor(Servo):
    def published(self) -> dict[str, Seat]:
        return Bought.published(self)
