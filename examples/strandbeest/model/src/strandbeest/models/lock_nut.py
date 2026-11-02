from build123d import BuildPart, BuildSketch, Circle, Mode, RegularPolygon, Solid, extrude

ACROSS_FLATS = 5.5
HEIGHT = 4.0
THREAD = 3.0
SIDES = 6
GRAMS_ESTIMATED = 0.5


def solid() -> Solid:
    with BuildPart() as body:
        with BuildSketch():
            RegularPolygon(ACROSS_FLATS / 2, SIDES, major_radius=False)
            Circle(THREAD / 2, mode=Mode.SUBTRACT)
        extrude(amount=HEIGHT)
    return body.part
