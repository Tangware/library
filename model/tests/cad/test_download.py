import hashlib

import pytest

from cad.library.bought.catalogue import Download
from cad.library.bought.vendor import maker_step

STEP = b"ISO-10303-21;\nEND-ISO-10303-21;\n"


def test_m5_a_maker_step_that_changed_upstream_fails_the_download() -> None:
    published = Download(
        url="https://maker.example/part.step", sha256=hashlib.sha256(STEP).hexdigest()
    )
    with pytest.raises(ValueError, match="sha256"):
        maker_step(published, STEP + b"changed\n")
