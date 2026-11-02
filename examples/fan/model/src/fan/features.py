from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Circle,
    Convexity,
    Location,
    Mode,
    PolarLocations,
    Rectangle,
    Select,
    chamfer,
    extrude,
)

from fan.master import FanMaster

GRILLE_RIBS = 4


def grille(
    m: FanMaster, made: BuildPart, face: Location, depth: float, inner: float, outer: float
) -> None:
    pitch = m.grille_slot + m.wall
    rings = int((outer - inner) // pitch)
    for ring in range(rings):
        middle = inner + ring * pitch
        with BuildSketch(face) as slot:
            Circle(middle + m.grille_slot)
            Circle(middle, mode=Mode.SUBTRACT)
            with PolarLocations(0, GRILLE_RIBS):
                Rectangle(outer, m.wall, align=(Align.MIN, Align.CENTER), mode=Mode.SUBTRACT)
        extrude(slot.sketch, amount=depth, mode=Mode.SUBTRACT)
        chamfer(made.edges(Select.NEW).filter_by(Convexity.CONVEX), m.wall_edge_break)
