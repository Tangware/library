from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Location,
    Locations,
    Mode,
    Plane,
    Pos,
    extrude,
)
from cad.design.parts import part
from cad.library.features.planes import axis_along, between, corner, crossing, parallel, station
from cad.library.provenance import step
from cad.library.shapes import FacesOn, Printed, RoundFaces, built, register

from pantilt.features import d_bore, shaft_clamp
from pantilt.master import ProductMaster
from pantilt.models import stepper

TILT_CLAMP = "tilt clamp insert"
JAW_GUIDE = "jaw guide"
SPRING_POST = "spring post"
TILT_BORE = "tilt bore"
CAMERA_POCKET = "camera pocket"
CORNER = (Align.MIN, Align.MIN, Align.MIN)
ALONG = (Align.CENTER, Align.CENTER, Align.MIN)
FROM_THE_FRONT = (Align.CENTER, Align.MIN, Align.MIN)
THROUGH_THE_FRONT = (Align.CENTER, Align.MIN, Align.CENTER)


def block(
    on: Plane,
    low: tuple[float, float],
    high: tuple[float, float],
    height: float,
    mode: Mode = Mode.ADD,
) -> None:
    with Locations(Location(on) * Pos(*low)):
        Box(high[0] - low[0], high[1] - low[1], height, align=CORNER, mode=mode)


@part
def cradle(m: ProductMaster) -> Printed:
    camera = m.camera_board
    half = camera.width + m.fits.sliding + m.wall
    left, right = m.phone_middle - half, m.phone_middle + half
    bottom = m.cradle_bottom
    inside = between(bottom, m.ledge)
    hub_outside = m.hub_inside + m.hub_thickness
    with BuildPart() as made:
        hub_plane = Plane.YZ.offset(m.hub_inside)
        on_the_axis = Locations(Pos(X=0, Y=m.tilt_height))
        with step("hub disc"), BuildSketch(hub_plane) as hub, on_the_axis:
            Circle(m.radius)
        with step("hub disc"):
            extrude(hub.sketch, amount=m.hub_thickness)
        with step("back plate"):
            far_end = 2 * m.phone_middle - m.hub_inside
            back = (hub_outside, m.cradle_back)
            block(bottom, (far_end, m.phone_back), back, between(bottom, m.back_plate_top))
        with step("jaw guide"), Locations(m.guide.at):
            guide = m.guide
            Box(guide.width, guide.depth, guide.height, align=ALONG)
        with step("jaw channel"), Locations(m.guide.at * Pos(Y=-m.wall / 2, Z=m.wall)):
            channel = (guide.width - 2 * m.wall, guide.depth - m.wall, guide.height - m.wall)
            Box(*channel, align=ALONG, mode=Mode.SUBTRACT)
            post = station(Plane.XY, through=m.spring_post_at)
            register(SPRING_POST, post, [FacesOn(plane=post)])
            front = Plane.XZ.offset(-m.cradle_back)
            register(JAW_GUIDE, Location(front), [FacesOn(plane=front)])
        with step("camera block"):
            block(bottom, (left, m.cradle_front), (right, m.cradle_back), inside)
        with step("ledge lip"):
            block(m.ledge, (left, m.cradle_front), (right, m.phone_front), m.lip)
        with step("camera pocket"):
            window_wall = Plane.XZ.offset(-(m.cradle_front + m.wall))
            middle = parallel(Plane.YZ, through=m.camera_at * m.camera_board_middle)
            with Locations(corner(bottom.offset(m.wall), middle, window_wall)):
                Box(
                    camera.width + 2 * m.fits.sliding,
                    m.cradle_back - m.cradle_front - m.wall,
                    inside - 2 * m.wall,
                    align=FROM_THE_FRONT,
                    mode=Mode.SUBTRACT,
                )
            register(CAMERA_POCKET, Location(window_wall), [FacesOn(plane=window_wall)])
        with step("lens window"):
            lens = axis_along(Axis.Y.direction, through=m.camera_at * m.lens)
            with Locations(crossing(Plane.XZ.offset(-m.cradle_front), lens)):
                Box(
                    m.camera_module.width + 2 * m.fits.sliding,
                    m.wall,
                    m.camera_module.height + 2 * m.fits.sliding,
                    align=THROUGH_THE_FRONT,
                    mode=Mode.SUBTRACT,
                )
        with step("tilt shaft bore"):
            d_bore(m, m.tilt_motor_at, m.screw_plate + m.fits.sliding, m.hub_thickness - m.wall)
            bore = m.fits.printed(stepper.SHAFT_DIAMETER) / 2
            register(
                TILT_BORE, m.tilt_motor_at, [RoundFaces(axis=Axis(m.tilt_motor_at), radius=bore)]
            )
        with step("tilt clamp"):
            shaft_clamp(m, m.tilt_clamp, m.radius, TILT_CLAMP)
    return Printed(
        name="cradle",
        pose=Location(),
        body=built(made),
        bed="+y",
        material="PAHT-CF black",
        print_settings=m.print_settings,
    )
