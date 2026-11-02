from build123d import Align, Box, Solid

LENGTH = 71.0
WIDTH = 65.0
HEIGHT = 20.0
GRAMS_ESTIMATED = 25.0


def solid() -> Solid:
    return Solid(Box(LENGTH, WIDTH, HEIGHT, align=(Align.CENTER, Align.CENTER, Align.MIN)).wrapped)
