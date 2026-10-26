from build123d import (
    Align,
    Axis,
    BuildPart,
    Cylinder,
    Location,
    Locations,
    Mode,
    Plane,
    Select,
    chamfer,
)
from cad.design.parts import part
from cad.library.features.hardware import counterbored_screws
from cad.library.features.planes import foot_on
from cad.library.provenance import step
from cad.library.shapes import FacesOn, Printed, RoundFaces, built, register
from cad.library.turns import UPSIDE_DOWN

from dispenser import models
from dispenser.master import DispenserMaster

FEET = "feet"
BUZZER_BORE = "buzzer bore"
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


@part
def plate(m: DispenserMaster) -> Printed:
    with BuildPart() as made:
        with step("plate"), Locations(Location(m.plate_bottom)):
            Cylinder(m.plate_radius, m.plate_thickness, align=BOTTOM)
        with step("broken edges"):
            chamfer(made.edges(Select.LAST), m.fits.min_wall / 2)
        with (
            step("screw bosses"),
            Locations(*[foot_on(m.plate_top, of=spot) for spot in m.plate_spots]),
        ):
            Cylinder(m.screw_land, m.screw_sunk, align=BOTTOM)
        with (
            step("buzzer collar"),
            Locations(foot_on(m.plate_top, of=m.buzzer_spot)),
        ):
            Cylinder(models.BUZZER_DIAMETER / 2 + m.fits.min_wall, m.screw_sunk, align=BOTTOM)
        with step("plate screws"):
            heads = [spot * UPSIDE_DOWN for spot in m.plate_spots]
            depth = m.plate_thickness + m.screw_sunk
            counterbored_screws(Plane(heads[0]), heads, m.screw, m.screw_sunk, depth, fits=m.fits)
        with step("buzzer bore"), Locations(m.buzzer_spot):
            Cylinder(
                m.fits.pressed(models.BUZZER_DIAMETER) / 2,
                m.plate_thickness + m.screw_sunk,
                align=BOTTOM,
                mode=Mode.SUBTRACT,
            )
            bore = RoundFaces(
                axis=Axis(m.buzzer_spot), radius=m.fits.pressed(models.BUZZER_DIAMETER) / 2
            )
            register(BUZZER_BORE, m.buzzer_spot, [bore])
        register(FEET, m.plate_bottom, [FacesOn(plane=-m.plate_bottom)])
    return Printed(
        name="plate",
        pose=Location(),
        body=built(made),
        bed="-z",
        material=m.material,
        print_settings=m.print_settings,
    )
