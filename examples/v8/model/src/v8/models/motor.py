from build123d import Keep, Plane, Solid

SHAFT_START = 10.0
BODY_GRAMS_ESTIMATED = 9.2
SHAFT_GRAMS_ESTIMATED = 0.3


def body(solids: list[Solid]) -> list[Solid]:
    return [solid.split(Plane.XY.offset(SHAFT_START), keep=Keep.BOTTOM) for solid in solids]


def shaft(solids: list[Solid]) -> list[Solid]:
    return [solid.split(Plane.XY.offset(SHAFT_START), keep=Keep.TOP) for solid in solids]
