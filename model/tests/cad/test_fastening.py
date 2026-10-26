from build123d import Box, Location, Plane, Pos

from cad.library.bought.catalogue import Catalogue
from cad.library.bought.vendor import Bought
from cad.library.features.hardware import Anchor, Hole, screwed, screwed_on
from cad.library.fits import STAINLESS_A2_70
from cad.library.mates import Connector
from cad.library.shapes import Shaped
from cad.library.standard.fasteners import Metric, Screw, Stock

MOTOR = Catalogue(file="made-up motor", grams=100.0, model=lambda: Box(20, 20, 20))
BRACKET_MM = 3.0
THREAD_DEPTH_MM = 6.0
LONGEST_WITHIN_MM = 8.0
STOCK = Stock(
    inserts={}, insert_maker="CNCKitchen", screw_lengths={}, fastener_grade=STAINLESS_A2_70
)


def test_m9_a_screw_into_a_bought_part_thread_ends_within_the_thread() -> None:
    bracket = Shaped(name="bracket", pose=Location(), body=Box(20, 20, BRACKET_MM))
    motor = Bought(name="motor", pose=Location(), item=MOTOR)
    spot = Location((5, 5, 0))
    through = Hole(
        face=Plane.XY, seats=[spot * Pos(Z=BRACKET_MM)], screw=Metric.M3, anchor=Anchor.CLEARANCE
    )
    tapped = Hole(
        face=Plane.XY, seats=[spot * Pos(Z=-THREAD_DEPTH_MM)], screw=Metric.M3, anchor=Anchor.TAPPED
    )

    made = screwed(
        through,
        tapped,
        Connector(bracket, "face"),
        Connector(motor, "face"),
        stock=STOCK,
    )

    (screw,) = made.parts
    assert (isinstance(screw, Screw) and screw.length, made.mates[0].fasteners) == (
        LONGEST_WITHIN_MM,
        (screw,),
    )


def test_m7_a_motor_screwed_onto_a_bracket_is_held_by_the_bracket_and_comes_up_to_it() -> None:
    bracket = Shaped(name="bracket", pose=Location(), body=Box(20, 20, BRACKET_MM))
    motor = Bought(name="motor", pose=Location(), item=MOTOR)
    spot = Location((5, 5, 0))
    through = Hole(
        face=Plane.XY, seats=[spot * Pos(Z=BRACKET_MM)], screw=Metric.M3, anchor=Anchor.CLEARANCE
    )
    tapped = Hole(
        face=Plane.XY, seats=[spot * Pos(Z=-THREAD_DEPTH_MM)], screw=Metric.M3, anchor=Anchor.TAPPED
    )

    made = screwed_on(
        through,
        tapped,
        Connector(bracket, "face"),
        Connector(motor, "face"),
        stock=STOCK,
    )

    on, under_the_head = made.mates
    approach = on.approach
    assert approach is not None
    assert (
        on.child_part,
        on.parent_part,
        under_the_head.parent_part,
        tuple(approach.direction),
    ) == (motor, bracket, bracket, (0, 0, 1))
