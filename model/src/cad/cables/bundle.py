from dataclasses import dataclass
from functools import cache
from math import cos, pi, radians, sin


@dataclass(frozen=True)
class Ring:
    count: int
    radius: float


def tight_ring(count: int, diameter: float) -> float:
    return diameter / (2 * sin(pi / count)) if count > 1 else 0.0


@cache
def rings(count: int, diameter: float) -> tuple[Ring, ...]:
    def around(core: tuple[Ring, ...], outer: int) -> tuple[Ring, ...]:
        beyond_the_core = core[-1].radius + diameter
        return (*core, Ring(count=outer, radius=max(tight_ring(outer, diameter), beyond_the_core)))

    one_ring = (Ring(count=count, radius=tight_ring(count, diameter)),)
    cored = (around(rings(count - outer, diameter), outer) for outer in range(1, count))
    return min((one_ring, *cored), key=lambda layout: layout[-1].radius)


def packed_diameter(count: int, diameter: float) -> float:
    return 2 * rings(count, diameter)[-1].radius + diameter


def packed(count: int, diameter: float) -> tuple[tuple[float, float], ...]:
    return tuple(
        (
            ring.radius * cos(radians(360 * step / ring.count)),
            ring.radius * sin(radians(360 * step / ring.count)),
        )
        for ring in rings(count, diameter)
        for step in range(ring.count)
    )
