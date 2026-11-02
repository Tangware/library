import pytest
from build123d import Location, Plane, Pos, Rot
from cad.library.turns import turn_to

from cessna.master import MASTER, RIGHT, tube_along
from cessna.parts.moving import OUTPUT_SHAFT, RACK
from cessna.parts.structure import MAIN_PLATE

RESTING_TOLERANCE_MM = 0.5
MM = 0.001
STALL_NM = 0.333
LEWIS_12_TEETH = 0.245
PETG_YIELD_MPA = 50.0


def tube_turn(side: float, shaft_deg: float) -> float:
    pin = (Rot(X=shaft_deg) * Pos(Z=1.0)).position
    across = Plane(origin=(0.0, 0.0, 0.0), x_dir=tube_along(side), z_dir=pin)
    return turn_to(Plane(MASTER.tube(side)), -across.y_dir)


def wanted_wheel(side: float, shaft_deg: float) -> Location:
    tube = MASTER.tube(side)
    return tube * Rot(Z=tube_turn(side, shaft_deg)) * tube.inverse() * MASTER.axle(side)


@pytest.mark.check(
    does_not_catch="A desk that is not flat, and the tyre's give.",
    subjects=(MAIN_PLATE,),
)
def test_m2_the_tyres_stand_on_the_desk_and_retract_level_with_the_plate() -> None:
    down = wanted_wheel(RIGHT, 0.0)
    assert down.position.Z - MASTER.wheel_radius == pytest.approx(0.0, abs=RESTING_TOLERANCE_MM)
    up = wanted_wheel(RIGHT, -180.0)
    assert abs(up.position.Z - MASTER.plate_top) <= MASTER.wheel_radius


@pytest.mark.check(
    does_not_catch="Fatigue, and any load a tooth sheds to its neighbour.",
    subjects=(RACK, OUTPUT_SHAFT),
)
def test_m22_the_teeth_carry_the_motors_stall_torque() -> None:
    force = STALL_NM / MM / MASTER.motor_radius
    assert force / (MASTER.rack_width * MASTER.module * LEWIS_12_TEETH) <= PETG_YIELD_MPA
