import pytest

from octopus.master import MASTER
from octopus.parts.arm import segment_name

MM = 0.001
STALL_NM = 0.333
PETG_YIELD_MPA = 50.0


@pytest.mark.check(
    does_not_catch="Fatigue of the printed stub pins.",
    subjects=(segment_name(0, 1),),
)
def test_m22_a_stall_stays_inside_the_stub_pin_in_bearing() -> None:
    force = STALL_NM / MM / MASTER.crank_throw
    assert force / (MASTER.pin_diameter * MASTER.thin) <= PETG_YIELD_MPA
