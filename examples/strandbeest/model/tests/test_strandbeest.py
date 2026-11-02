import pytest

from strandbeest.master import MASTER
from strandbeest.parts.links import FOOT

FLAT_RUN_MM = 0.75
GROUND_BAND_MM = 1.0


@pytest.mark.check(
    does_not_catch="Whether the walker stays upright.",
    subjects=(FOOT,),
)
def test_m2_the_foot_runs_flat_on_the_ground_for_its_stride() -> None:
    lows = [MASTER.joints(float(angle)).tip.position.Z for angle in range(0, 360, 5)]
    assert min(lows) == pytest.approx(0.0, abs=GROUND_BAND_MM)
    assert sum(low < min(lows) + FLAT_RUN_MM for low in lows) * 5 >= 120
