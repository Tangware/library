from dataclasses import dataclass

from cad.library.why import Why


@dataclass(frozen=True, kw_only=True)
class PrintSettings:
    preset: str
    walls: int
    top_layers: int
    bottom_layers: int
    infill: float
    extrusion_width: float
    layer_height: float
    pattern: str = "gyroid"

    @property
    def wall_thickness(self) -> float:
        return self.walls * self.extrusion_width

    @property
    def top_thickness(self) -> float:
        return self.top_layers * self.layer_height

    @property
    def bottom_thickness(self) -> float:
        return self.bottom_layers * self.layer_height


PRINT_SETTINGS_UNITS = {
    "preset": "-",
    "walls": "-",
    "top_layers": "-",
    "bottom_layers": "-",
    "infill": "-",
    "extrusion_width": "mm",
    "layer_height": "mm",
    "pattern": "-",
}


def with_supports(where: str, reason: str) -> Why:
    return Why(f"Prints with supports {where}", reason)
