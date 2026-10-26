from build123d import Align, Box, BuildPart, Cylinder, Location, Locations, Mode
from cad.design.parts import part
from cad.library.features.hardware import counterbored_screws
from cad.library.provenance import step
from cad.library.shapes import FacesOn, Printed, built, register

from pantilt.master import ProductMaster
from pantilt.models import stepper

MOTOR_SEAT = "motor seat"
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


@part
def lid(m: ProductMaster) -> Printed:
    with BuildPart() as made:
        with step("disc"), Locations(Location(m.pan_flange)):
            Cylinder(m.inside_radius - m.fits.sliding, m.screw_plate, align=BOTTOM)
            register(MOTOR_SEAT, m.pan_flange, [FacesOn(plane=m.pan_flange)])
        with step("pilot bore"), Locations(Location(m.pan_flange)):
            Cylinder(
                m.fits.printed(stepper.PILOT_DIAMETER) / 2,
                m.screw_plate,
                align=BOTTOM,
                mode=Mode.SUBTRACT,
            )
        with step("screws"):
            counterbored_screws(
                m.pan_flange,
                [*m.pan_motor_screws, *m.lid_screws],
                m.screw,
                m.screw_plate - m.wall,
                m.screw_plate,
                fits=m.fits,
            )
        with step("cable hole"), Locations(m.lid_hole):
            Box(m.flat_cable_width, m.cable_way, m.screw_plate, align=BOTTOM, mode=Mode.SUBTRACT)
    return Printed(
        name="lid",
        pose=Location(),
        body=built(made),
        bed="-z",
        material="PAHT-CF black",
        print_settings=m.print_settings,
    )
