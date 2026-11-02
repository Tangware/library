BEZEL_LENGTH = 21.0
BEZEL_WIDTH = 9.6
ABOVE_THE_PANEL = 6.2
CUTOUT_WIDTH = 6.8
CUTOUT_LENGTHS = ((0.75, 1.25, 19.2), (1.25, 2.0, 19.4), (2.0, 3.0, 19.6))
GRAMS_ESTIMATED = 2.0


def cutout_length(panel: float) -> float:
    (length,) = [
        length for thinnest, thickest, length in CUTOUT_LENGTHS if thinnest < panel <= thickest
    ]
    return length
