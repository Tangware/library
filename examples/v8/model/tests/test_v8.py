import pytest

from v8.master import CYLINDERS, FIRING_ORDER, MASTER, VALVES
from v8.parts.valvetrain import CAMSHAFT

SOLVED_TOLERANCE_MM = 0.5
MM = 0.001
STALL_NM = 0.333
FIRING_STEP_DEG = 90.0
LIFT_SWEEP_DEG = range(0, 720, 10)
MIN_LIFT_MM = 2.5
SHUT_SHARE = 0.15
WRIST_PIN_DOUBLE_SHEAR_N = 1000.0
PETG_YIELD_MPA = 50.0


@pytest.mark.check(
    does_not_catch="Ignition, compression, and which stroke each top dead centre belongs to.",
    subjects=("piston 1",),
)
def test_m2_the_pistons_reach_the_top_in_firing_order() -> None:
    by_number = {each.number: each for each in CYLINDERS}
    for n, number in enumerate(FIRING_ORDER):
        cylinder = by_number[number]
        crown = MASTER.bank_axis(cylinder).inverse() * MASTER.wrist(cylinder, n * FIRING_STEP_DEG)
        assert pytest.approx(MASTER.throw + MASTER.rod, abs=SOLVED_TOLERANCE_MM) == crown.position.Z


@pytest.mark.check(
    does_not_catch="Real gas flow; the lobes are harmonic, so the valves open wider than a cam's.",
    subjects=(CAMSHAFT,),
)
def test_m2_each_valve_opens_on_its_stroke_and_is_nearly_shut_at_firing() -> None:
    for valve in VALVES:
        most = max(MASTER.valve_lift(valve, valve.fires_at + t) for t in LIFT_SWEEP_DEG)
        assert most == pytest.approx(MASTER.valve_lift(valve, valve.fires_at + valve.peak_deg))
        assert most >= MIN_LIFT_MM
        assert MASTER.valve_lift(valve, valve.fires_at) <= most * SHUT_SHARE


@pytest.mark.check(
    does_not_catch="Fatigue; printed friction in the valvetrain, which the tests here leave out.",
    subjects=(CAMSHAFT,),
)
def test_m22_the_motors_stall_stays_inside_the_pins_and_stub_pins() -> None:
    force = STALL_NM / MM / MASTER.throw
    assert force <= WRIST_PIN_DOUBLE_SHEAR_N
    bearing = force / (MASTER.wrist_pin_diameter * MASTER.rod_thickness)
    assert bearing <= PETG_YIELD_MPA
