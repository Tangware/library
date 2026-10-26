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
    chamfer,
)
from cad.design.parts import part
from cad.library.features.cuts import extrude_to
from cad.library.features.hardware import counterbored_screws, insert_holes
from cad.library.features.planes import between
from cad.library.provenance import step
from cad.library.shapes import (
    FacesOn,
    Printed,
    RoundFaces,
    built,
    faces_on,
    meeting,
    register,
    round_faces,
)
from cad.library.turns import ALONG_X, FACING_BACK

from pantilt.features import d_bore, shaft_clamp
from pantilt.master import ProductMaster
from pantilt.models import stepper

PAN_CLAMP = "pan clamp insert"
CAP_INSERTS = "cap inserts"
BEHIND = (Align.CENTER, Align.CENTER, Align.MAX)
PAN_BORE = "pan bore"
MOTOR_SEAT = "motor seat"
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)
FROM_THE_AXIS = (Align.MIN, Align.CENTER, Align.MIN)


@part
def arm(m: ProductMaster) -> Printed:
    height = between(m.arm_bottom, m.arm_top)
    rise = between(m.arm_top, m.tilt_level)
    column = Plane(m.tilt_motor_at).offset(m.screw_plate)
    with BuildPart() as made:
        with step("foot disc"), Locations(Location(m.arm_bottom)):
            Cylinder(m.radius, height, align=BOTTOM)
        with step("beam"), Locations(Location(m.arm_bottom)):
            Box(m.tilt_flange, stepper.FRAME, height, align=FROM_THE_AXIS)
        with step("column"), BuildSketch(column) as side:
            Circle(m.radius)
            with Locations(Pos(Y=rise / 2)):
                Rectangle(stepper.FRAME, rise)
        with step("column"):
            extrude_to(column, Plane(m.tilt_motor_at), sketch=side)
        with step("cable chamber"), Locations(Location(m.arm_bottom)):
            chamber = between(m.arm_bottom, m.chamber_top)
            Cylinder(m.inside_radius, chamber, align=BOTTOM, mode=Mode.SUBTRACT)
            Cylinder(m.pan_hub_radius, chamber, align=BOTTOM)
        with (
            step("cable hole"),
            Locations(
                m.cable_points["under the arm's cable hole"]
                * Pos(Z=between(m.chamber_middle, m.chamber_top))
            ),
        ):
            Cylinder(m.flat_cable_width / 2, m.wall, align=BOTTOM, mode=Mode.SUBTRACT)
        with step("pan shaft bore"):
            d_bore(
                m,
                m.pan_motor_at,
                m.screw_plate,
                stepper.SHAFT_LENGTH - m.screw_plate + m.fits.sliding,
            )
            register(
                PAN_BORE,
                m.pan_motor_at,
                [
                    RoundFaces(
                        axis=Axis(m.pan_motor_at), radius=m.fits.printed(stepper.SHAFT_DIAMETER) / 2
                    )
                ],
            )
        with step("pan clamp"):
            shaft_clamp(m, m.pan_clamp, m.radius, PAN_CLAMP)
        with step("tilt pilot bore"), Locations(m.tilt_motor_at):
            Cylinder(
                m.fits.printed(stepper.PILOT_DIAMETER) / 2,
                m.screw_plate,
                align=BOTTOM,
                mode=Mode.SUBTRACT,
            )
        with step("drum"), Locations(m.tilt_motor_at):
            Cylinder(m.radius, m.drum_rim - m.tilt_flange, align=BEHIND)
        with step("motor pocket"), Locations(m.tilt_motor_at):
            side = m.fits.printed(stepper.FRAME)
            Box(side, side, m.drum_rim - m.tilt_flange, align=BEHIND, mode=Mode.SUBTRACT)
        with step("cap inserts"):
            rim = Plane(Location((m.drum_rim, 0, m.tilt_height)) * ALONG_X)
            insert_holes(rim, m.cap_screws, m.screw, CAP_INSERTS, fits=m.fits, stock=m.stock)
        with step("motor screws"):
            counterbored_screws(
                Plane(m.tilt_motor_at),
                m.tilt_motor_screws,
                m.screw,
                m.screw_plate - m.wall,
                m.screw_plate,
                fits=m.fits,
            )
            register(MOTOR_SEAT, m.tilt_motor_at, [FacesOn(plane=Plane(m.tilt_motor_at))])
        with step("lead hole"), Locations(m.drum_lead_hole * FACING_BACK):
            reach = m.radius - stepper.FRAME / 2
            Cylinder(m.cable_way / 2, reach, align=BOTTOM, mode=Mode.SUBTRACT)
        with step("edge break"):
            outside = round_faces(built(made), m.radius)
            chamfer(meeting(faces_on(built(made), m.arm_bottom), outside), m.fits.min_wall)
    return Printed(
        name="arm",
        pose=Location(),
        body=built(made),
        bed="-z",
        material="PAHT-CF black",
        print_settings=m.print_settings,
    )
