from dataclasses import dataclass

from build123d import Align, Cylinder, Location

from cad.library.shapes import OUTSIDE, Brep, Part, Seat, seat_of


@dataclass(frozen=True)
class DiscSize:
    kind: str
    short_name: str
    diameter: float
    thickness: float
    pull_n: float


DISC_UNITS = {"kind": "-", "short_name": "-", "diameter": "mm", "thickness": "mm", "pull_n": "N"}


@dataclass(kw_only=True)
class Disc(Part):
    size: DiscSize
    material: str = "steel"

    @property
    def label(self) -> str:
        return f"Ø{self.size.diameter:g} x {self.size.thickness:g} mm {self.size.kind}"

    def shape(self) -> Brep:
        return Cylinder(
            self.size.diameter / 2,
            self.size.thickness,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )

    def published(self) -> dict[str, Seat]:
        return {OUTSIDE: seat_of(self.unposed().faces(), Location())}
