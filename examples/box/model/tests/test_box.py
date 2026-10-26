import pytest

from box.master import MASTER
from box.parts.body import body
from box.parts.lid import lid


@pytest.mark.check(does_not_catch="Strength, fit and finish.", subjects=("body", "lid"))
def test_m3_the_body_and_lid_build_from_the_master_alone() -> None:
    assert [each(MASTER).solid().is_valid for each in (body, lid)] == [True, True]
