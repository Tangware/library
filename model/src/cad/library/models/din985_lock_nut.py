from dataclasses import dataclass

from build123d import BuildPart, BuildSketch, Circle, Mode, RegularPolygon, extrude

from cad.library.shapes import Brep, built

SOURCE = "DIN 985's dimension table, https://www.fasteners.eu/standards/DIN/985/"


@dataclass(frozen=True)
class LockNutSize:
    across_flats: float
    height: float


SIZES = {
    "M5": LockNutSize(across_flats=8.0, height=5.0),
    "M6": LockNutSize(across_flats=10.0, height=6.0),
}


def lock_nut(size: str, thread: float) -> Brep:
    nut = SIZES[size]
    with BuildPart() as body:
        with BuildSketch():
            RegularPolygon(nut.across_flats / 2, 6, major_radius=False)
            Circle(thread / 2, mode=Mode.SUBTRACT)
        extrude(amount=nut.height)
    return built(body)
