from collections.abc import Sequence

from build123d import Keep, Plane, Solid

LENGTH = 56.8
GRAMS_ESTIMATED = 11.76


def without_leads(solids: list[Solid]) -> Sequence[Solid | None]:
    end_wall = Plane.YZ.offset(-LENGTH / 2)
    return [solid.split(end_wall, keep=Keep.TOP) for solid in solids]
