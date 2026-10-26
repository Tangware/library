from build123d import Align, BuildSketch, Circle, Location, Locations, Mode, Rectangle, Rot, Sketch

from dispenser.master import DispenserMaster

CORNER = (Align.MIN, Align.MIN)


def front_sector(m: DispenserMaster, on: Location) -> Sketch:
    half = m.sector / 2
    reach = 2 * m.pocket_reach
    with BuildSketch(on) as sector:
        Circle(m.pocket_reach)
        Circle(m.pocket_start, mode=Mode.SUBTRACT)
        for turn in (-90 - half, -180 + half):
            with Locations(Rot(Z=turn)):
                Rectangle(reach, reach, align=CORNER, mode=Mode.INTERSECT)
    return sector.sketch
