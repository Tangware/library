from build123d import Align, Box, BuildPart, Location, Locations, Plane, Pos
from cad.design.parts import part
from cad.library.features.planes import between, reach
from cad.library.provenance import step
from cad.library.shapes import FacesOn, Printed, built, register

from pantilt.master import ProductMaster

CORNER = (Align.MIN, Align.MIN, Align.MIN)
HANGING = (Align.CENTER, Align.CENTER, Align.MAX)
STEM = "stem"
SPRING_LUG = "spring lug"


@part
def jaw(m: ProductMaster) -> Printed:
    left = m.phone_middle - m.jaw_length / 2
    front = (-Plane.XZ).offset(m.cradle_front)
    depth = between(front, reach([m.guide], toward=-Plane.XZ))
    with BuildPart() as made:
        with step("bar"), Locations(Pos(left, m.cradle_front, m.phone_top)):
            Box(m.jaw_length, depth, m.jaw_thickness, align=CORNER)
            underside = Plane.XY.offset(m.phone_top)
            register(SPRING_LUG, underside, [FacesOn(plane=underside)])
        with step("lip"), Locations(Pos(left, m.cradle_front, m.phone_top - m.lip)):
            Box(m.jaw_length, m.wall, m.lip, align=CORNER)
        with step("stem"), Locations(m.stem_at):
            Box(m.stem_side, m.stem_side, m.stem_length, align=HANGING)
            front = Plane.XZ.offset(-(m.guide_middle - m.stem_side / 2))
            register(STEM, Location(front), [FacesOn(plane=front)])
    return Printed(
        name="jaw",
        pose=Location(),
        body=built(made),
        bed="-y",
        material="PAHT-CF black",
        print_settings=m.print_settings,
    )
