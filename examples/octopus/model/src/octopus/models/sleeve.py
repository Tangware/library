from build123d import Compound, Solid
from cad.library.bought.catalogue import BLACK_PLASTIC, Rgb

from octopus.models import battery_holder

SUPPLIED_BORE = 2.36  # TE RNF-100-3/32: supplied inside diameter 0.093 in, fits both leads
WALL = 0.51  # TE RNF-100 table, 3/32: recovered wall 0.020 in
LENGTH = 2 * battery_holder.STRIP
GRAMS_ESTIMATED = 0.06  # estimate: the tube's volume in polyolefin
COLOUR: Rgb = BLACK_PLASTIC  # BK in the part number


def solid() -> Solid | Compound:
    bore = SUPPLIED_BORE / 2
    return Solid.make_cylinder(bore + WALL, LENGTH).cut(Solid.make_cylinder(bore, LENGTH))
