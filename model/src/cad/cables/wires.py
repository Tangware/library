from collections.abc import Sequence

# Glenair, Circular Connector Backshells and Accessories, Wire Bundle Diameter Calculator (2022)
BUNDLE_FACTORS = (
    (1, 1.0),
    (2, 2.0),
    (3, 2.2),
    (4, 2.4),
    (5, 2.7),
    (6, 2.9),
    (7, 3.0),
    (8, 3.3),
    (9, 3.8),
    (10, 4.0),
    (12, 4.3),
    (14, 4.6),
    (16, 5.0),
    (18, 5.3),
    (20, 5.6),
    (24, 6.0),
    (28, 6.5),
    (32, 6.9),
    (36, 7.4),
    (40, 7.7),
)


def bundle_diameter(wires: Sequence[float]) -> float:
    factor = next(factor for count, factor in BUNDLE_FACTORS if count >= len(wires))
    return factor * (sum(wires) / len(wires))


FIXED_BEND_DIAMETERS = 4.0  # CENELEC HD 516, flexible cables up to 8 mm, free movement
FLEXING_BEND_DIAMETERS = 6.0  # CENELEC HD 516, flexible cables up to 8 mm, repeated flexing


def bend_diameters(moving: bool) -> float:
    return FLEXING_BEND_DIAMETERS if moving else FIXED_BEND_DIAMETERS
