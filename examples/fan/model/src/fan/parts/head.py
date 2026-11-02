from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Convexity,
    Cylinder,
    Location,
    Locations,
    Mode,
    Plane,
    Pos,
    Rectangle,
    Select,
    chamfer,
    extrude,
    fillet,
)
from cad.design.parts import part
from cad.library.features.hardware import INSERTS, insert_holes
from cad.library.features.planes import between
from cad.library.shapes import FacesOn, Printed, built, edges_on, register
from cad.library.turns import UPSIDE_DOWN

from fan.features import grille
from fan.master import SHAFT_RADIUS, FanMaster
from fan.models import FAN_HUB, FLAT_LENGTH, SHAFT_FLATS

FAN_SEAT = "fan seat"
SHAFT_BORE = "shaft bore"
BOTTOM = (Align.CENTER, Align.CENTER, Align.MIN)


@part
def head(m: FanMaster) -> Printed:
    middle = m.fan_middle
    front = m.facing_back(middle, m.head_front)
    pocket = m.facing_back(middle, m.fan_front)
    neck = between(m.neck_bottom, m.head_bottom)
    hub_radius = SHAFT_RADIUS + 2 * m.wall
    hub_bottom = m.shaft_top.offset(-FLAT_LENGTH)
    with BuildPart() as made:
        with Locations(Location(m.head_bottom) * Pos(Y=m.head_front)):
            Box(
                m.head_width,
                m.fan_back - m.head_front,
                m.head_height,
                align=(Align.CENTER, Align.MIN, Align.MIN),
            )
        fillet(made.edges(Select.LAST).filter_by(Axis.Y), m.wall)
        chamfer(edges_on(built(made), Plane(front)), m.fits.min_wall)
        back = Plane(m.facing_back(middle, m.fan_back))
        chamfer(edges_on(built(made), back), m.wall_edge_break)
        with Locations(pocket):
            Box(
                m.fan_side + 2 * m.fits.sliding,
                m.fan_side + 2 * m.fits.sliding,
                m.fan_depth + m.wall,
                align=BOTTOM,
                mode=Mode.SUBTRACT,
            )
            seat = Plane(m.facing_back(Pos(), m.fan_front))
            register(FAN_SEAT, seat, [FacesOn(plane=seat)])
        with Locations(pocket * UPSIDE_DOWN):
            Box(m.fan_side, m.fan_side, m.lead_reach, align=BOTTOM, mode=Mode.SUBTRACT)
        pads = [m.facing_back(at, m.fan_front) for at in m.fan_screws]
        with Locations(*pads):
            Cylinder(m.screw_land, m.lead_reach, align=(Align.CENTER, Align.CENTER, Align.MAX))
        grille(m, made, front, m.insert_depth - m.lead_reach, FAN_HUB, m.fan_side / 2 - m.wall)
        spots = [m.facing_back(at, m.fan_front) for at in m.fan_screws]
        insert_holes(Plane(spots[0]), spots, m.screw, INSERTS, fits=m.fits, stock=m.stock)
        with Locations(Location(m.neck_bottom)):
            Cylinder(
                m.neck_radius,
                neck + m.wall,
                align=BOTTOM,
            )
        chamfer(made.edges(Select.LAST).filter_by(Convexity.CONVEX), m.wall_edge_break)
        with Locations(Location(hub_bottom)):
            Cylinder(hub_radius, between(hub_bottom, m.neck_bottom), align=BOTTOM)
        with BuildSketch(Location(hub_bottom)) as d_bore:
            Circle(m.fits.pressed(2 * SHAFT_RADIUS) / 2)
            Rectangle(2 * SHAFT_RADIUS + m.wall, m.fits.pressed(SHAFT_FLATS), mode=Mode.INTERSECT)
        extrude(
            d_bore.sketch,
            amount=between(hub_bottom, m.shaft_top) + m.fits.sliding,
            mode=Mode.SUBTRACT,
        )
        register(SHAFT_BORE, hub_bottom, [FacesOn(plane=hub_bottom)])
        with Locations(Location(m.neck_bottom) * m.lead_way):
            Cylinder(
                m.lead_bore / 2,
                neck + m.wall + m.fits.sliding + m.lead_bore,
                align=BOTTOM,
                mode=Mode.SUBTRACT,
            )
    return Printed(
        name="head",
        pose=Location(),
        body=built(made),
        bed="-y",
        exterior=True,
        material=m.material,
        print_settings=m.print_settings,
    )
