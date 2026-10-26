from collections.abc import Callable
from dataclasses import dataclass

from build123d import Align, Box, BuildPart

from cad.library.shapes import Brep, built


@dataclass(frozen=True)
class Model:
    name: str
    source: str
    shape: Callable[[], Brep]

    def build(self) -> Brep:
        part = self.shape()
        part.label = f"{self.name}, from {self.source}"
        return part


@dataclass(frozen=True)
class Block:
    width: float
    length: float
    height: float

    def shape(self) -> Brep:
        with BuildPart() as block:
            Box(self.width, self.length, self.height, align=(Align.CENTER, Align.CENTER, Align.MIN))
        return built(block)
