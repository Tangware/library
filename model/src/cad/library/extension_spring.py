from dataclasses import dataclass

from build123d import Location, Plane

from cad.library.features.planes import line_between, line_through, normal_to
from cad.library.fits import Fits
from cad.library.shapes import Seat, Tube, flat_faces, seat_of
from cad.standards import Direction, RatedForce

LOW_HOOK = "low hook"
HIGH_HOOK = "high hook"


@dataclass(frozen=True)
class Spring:
    part: str
    wire: float
    outer_diameter: float
    free_length: float
    rate: float
    preload: float
    rated_force: float
    rated_stretch: float
    hook_pin: float

    @property
    def free_span(self) -> float:
        return self.free_length - self.hook_pin

    @property
    def zero_force_span(self) -> float:
        return self.free_span - self.preload / self.rate


@dataclass(kw_only=True)
class ExtensionSpring(Tube):
    spring: Spring
    material: str = "steel"

    @classmethod
    def hooked(cls, *, name: str, spring: Spring, low: Location, high: Location) -> ExtensionSpring:
        between = line_between(low, high)
        return cls(
            name=name,
            pose=Location(normal_to(line_through(low, high).direction, through=low)),
            outside_radius=spring.outer_diameter / 2,
            inside_radius=spring.outer_diameter / 2 - spring.wire,
            bottom=0.0,
            top=between.length,
            spring=spring,
        )

    @property
    def label(self) -> str:
        return f"extension spring {self.spring.part}"

    def rating(self, fits: Fits) -> RatedForce:
        return RatedForce(
            check="spring catalogue force",
            rated_n=self.spring.rated_force,
            direction=Direction.ANY,
            connectors=(LOW_HOOK, HIGH_HOOK),
        )

    def published(self) -> dict[str, Seat]:
        return {
            hook: seat_of(flat_faces(self.unposed(), end), Location(Plane.XY.offset(end)))
            for hook, end in ((LOW_HOOK, self.bottom), (HIGH_HOOK, self.top))
        }
