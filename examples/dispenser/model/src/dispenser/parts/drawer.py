from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Cylinder,
    Location,
    Locations,
    Mode,
    Plane,
    Pos,
    Rectangle,
    Select,
    extrude,
    fillet,
)
from cad.design.parts import part
from cad.library.provenance import step
from cad.library.shapes import FacesOn, Printed, built, register

from dispenser import models
from dispenser.master import DispenserMaster

RUNNER = "runner"
ACTUATOR_POCKET = "actuator pocket"
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)
BACK = (Align.CENTER, Align.MAX, Align.MIN)


@part
def drawer(m: DispenserMaster) -> Printed:
    floor = m.drawer_bottom.offset(m.pull_height)
    tray = floor.offset(m.wall)
    with BuildPart() as made:
        with step("block"), Locations(Location(m.drawer_bottom) * Pos(Y=m.drawer_back)):
            Box(m.drawer_width, m.radius + m.drawer_back, m.drawer_height, align=BACK)
        with step("front follows the drum"), Locations(Location(m.drawer_bottom)):
            Cylinder(m.radius, m.drawer_height, align=BOTTOM, mode=Mode.INTERSECT)
        with step("rounded front corners"):
            fillet(made.edges(Select.LAST).filter_by(Axis.Z), m.wall)
        with step("tray"):
            with BuildSketch(Location(tray) * Pos(Y=m.tray_back)) as inside:
                Rectangle(m.pull_width, m.radius, align=(Align.CENTER, Align.MAX))
                with Locations(Pos(Y=-m.tray_back)):
                    Circle(m.radius - m.wall, mode=Mode.INTERSECT)
            extrude(inside.sketch, amount=m.tray_depth, mode=Mode.SUBTRACT)
        with (
            step("pull"),
            Locations(Location(m.drawer_bottom) * Pos(Y=m.drawer_front + m.pull_reach)),
        ):
            Box(m.pull_width, m.pull_reach, m.pull_height, align=BACK, mode=Mode.SUBTRACT)
        with step("actuator pocket"), Locations(m.actuator_at):
            pocket = m.fits.sliding
            Box(
                models.REED_LENGTH + 2 * pocket,
                models.REED_WIDTH + 2 * pocket,
                models.REED_HEIGHT,
                align=BOTTOM,
                mode=Mode.SUBTRACT,
            )
            register(ACTUATOR_POCKET, m.actuator_at, [FacesOn(plane=Plane(m.actuator_at))])
        register(RUNNER, m.drawer_bottom, [FacesOn(plane=m.drawer_bottom)])
    return Printed(
        name="drawer",
        pose=Location(),
        body=built(made),
        bed="-z",
        material=m.material,
        print_settings=m.print_settings,
    )
