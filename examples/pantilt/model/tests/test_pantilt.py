from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from build123d import Axis, Box, CenterOf, Location, Plane, Pos, Rotation
from cad.analysis.sweep import overlapping
from cad.assembly.mass import weight
from cad.design.bom import bom
from cad.design.build import built
from cad.design.catalogue import Kind as Bill
from cad.design.package import load
from cad.design.world import World
from cad.library.extension_spring import ExtensionSpring
from cad.library.mates import Kind, Mate
from cad.library.shapes import Part, Printed

from pantilt.master import (
    CAMERA_BOARD,
    JAW,
    MASTER,
    PAN,
    ROTOR,
    STATOR,
    TILT,
    USB_C_BOARD,
    ProductMaster,
)
from pantilt.models import stepper
from pantilt.parts.arm import arm
from pantilt.parts.base import base
from pantilt.parts.cap import cap
from pantilt.parts.cradle import cradle
from pantilt.parts.jaw import jaw
from pantilt.parts.lid import lid

REPO = Path(__file__).parents[2]
MADE = (base, lid, arm, cap, cradle, jaw)
STANDARD_GRAVITY = 9.80665
HOLDING_SHARE = 0.5
TOUCHING_MM3 = 1.0
CRADLE = "pantilt/cradle"


@pytest.fixture(scope="module")
def world() -> World:
    return World(built=built(load(REPO)))


def about(axis: Axis, angle: float) -> Location:
    frame = Location(Plane(origin=axis.position, z_dir=axis.direction))
    return frame * Rotation(0, 0, angle) * frame.inverse()


def mate(world: World, name: str) -> Mate:
    (found,) = [each for each in world.built.mates if each.name == name]
    return found


def motion(joint: Mate, value: float) -> Location:
    if joint.kind is Kind.PRISMATIC:
        return Pos(*(joint.axis.direction * value))
    return about(joint.axis, value)


def shift(world: World, part: Part, joints: dict[str, float]) -> Location:
    chain = []
    while (holder := world.built.holder(part)) is not None:
        chain.append(holder)
        part = holder.parent_part
    moved = Location()
    for joint in reversed(chain):
        if joint.name in joints:
            moved = moved * motion(joint, joints[joint.name])
    return moved


def clashes(world: World, joints: dict[str, float]) -> Iterator[str]:
    placed = world.built.placed
    moved = {each.key: shift(world, each.part, joints) for each in placed}
    bodies = {
        each.key: world.moved_body(each, lambda part: shift(world, part, joints)) for each in placed
    }
    for n, first in enumerate(placed):
        for second in placed[n + 1 :]:
            rigid_together = moved[first.key] == moved[second.key]
            springs = isinstance(first.part, ExtensionSpring) or isinstance(
                second.part, ExtensionSpring
            )
            if (rigid_together and not springs) or world.seated_bought(first, second):
                continue
            if overlapping(bodies[first.key], bodies[second.key]):
                yield f"{first.key} hits {second.key}"


def centre_and_kilograms(
    world: World, pan: float, tilt: float
) -> tuple[tuple[float, float], float]:
    phone = MASTER.phone.block
    phone_at = phone.at * Pos(Z=phone.height / 2)
    tilted = about(mate(world, PAN).axis, pan) * about(mate(world, TILT).axis, tilt)
    joints = {PAN: pan, TILT: tilt}
    points = [((tilted * phone_at).position, MASTER.heaviest_phone_kg)]
    points += [
        (
            (
                shift(world, each.part, joints) * Pos(each.part.solid().center(CenterOf.MASS))
            ).position,
            weight(each.part),
        )
        for each in world.built.placed
    ]
    total = sum(kg for _, kg in points)
    x = sum(at.X * kg for at, kg in points) / total
    y = sum(at.Y * kg for at, kg in points) / total
    return (x, y), total


@pytest.mark.check(
    does_not_catch="Strength, fit and finish.", subjects=tuple(b.__name__ for b in MADE)
)
@pytest.mark.parametrize("builder", MADE)
def test_m3_each_part_builds_from_the_master_alone(
    builder: Callable[[ProductMaster], Printed],
) -> None:
    assert builder(MASTER).solid().is_valid


@pytest.mark.check(
    does_not_catch="The spring's grip on the phone and phones with bumps or cases.",
    subjects=("jaw", "cradle"),
)
def test_r1_the_jaw_slides_from_the_widest_phone_to_the_narrowest_without_a_clash(
    world: World,
) -> None:
    jaw_slide = mate(world, JAW)
    underside = shift(world, jaw_slide.child_part, {JAW: MASTER.jaw_range.low}) * Pos(
        Z=MASTER.phone_top
    )

    assert MASTER.ledge.origin.Z + MASTER.narrowest_phone >= underside.position.Z
    assert list(clashes(world, {JAW: MASTER.jaw_range.low})) == []
    assert list(clashes(world, {JAW: MASTER.jaw_range.high})) == []


@pytest.mark.check(
    does_not_catch="Fatigue of the spring and the hooks' own strength.",
    subjects=("jaw", "cradle"),
)
def test_r1_the_spring_stays_taut_and_within_its_rating_over_the_jaw_travel(world: World) -> None:
    spring = MASTER.spring
    for travel in (MASTER.jaw_range.low, MASTER.jaw_range.high):
        lug = Pos(Z=travel) * MASTER.spring_lug_at
        stretch = lug.position.Z - MASTER.spring_post_at.position.Z - spring.free_length
        assert 0.0 < stretch <= spring.rated_stretch


@pytest.mark.check(
    does_not_catch="Cables crossing the joint, and parts within the mesh tolerance.",
    subjects=("arm", "base", "lid"),
)
@pytest.mark.parametrize("end", ["low", "high"])
def test_r2_it_turns_a_quarter_each_way_without_a_clash(world: World, end: str) -> None:
    assert list(clashes(world, {PAN: getattr(MASTER.pan_range, end)})) == []


@pytest.mark.check(
    does_not_catch="The phone itself against the arm, and parts within the mesh tolerance.",
    subjects=("cradle", "arm"),
)
@pytest.mark.parametrize("end", ["low", "high"])
def test_r3_it_tilts_through_its_range_without_a_clash(world: World, end: str) -> None:
    assert list(clashes(world, {TILT: getattr(MASTER.tilt_range, end)})) == []


@pytest.mark.check(
    does_not_catch="Noise from the drivers' chopping, resonance, and the firmware's ramps.",
    subjects=("arm", "cradle"),
)
def test_r4_each_axis_turns_on_its_motor_shaft_with_no_gear_between(world: World) -> None:
    for joint in (PAN, TILT):
        turning = mate(world, joint)
        carried = [held for held in world.built.mates if held.parent_part is turning.child_part]
        assert turning.kind is Kind.REVOLUTE
        assert turning.parent_part.catalogue == STATOR
        assert turning.child_part.catalogue == ROTOR
        assert carried
        assert all(held.kind is Kind.RIGID for held in carried)
    assert not [held for held in world.built.mates if held.kind is Kind.GEAR]


@pytest.mark.check(
    does_not_catch="Knocks, a tug on the cable, a slippery desk, and the mass of a phone case.",
    subjects=("base",),
)
def test_r5_it_stands_with_the_heaviest_phone_at_every_pose(world: World) -> None:
    for pose in MASTER.poses:
        centre, _ = centre_and_kilograms(
            world, pose.joints.get(PAN, 0.0), pose.joints.get(TILT, 0.0)
        )
        x, y = centre
        assert (x * x + y * y) ** 0.5 < MASTER.radius


@pytest.mark.check(
    does_not_catch="Holding torque lost to microstepping, heat or a low supply; the jaw's grip.",
    subjects=("cradle",),
)
def test_r5_the_tilt_motor_holds_the_heaviest_phone_at_every_tilt(world: World) -> None:
    axis = mate(world, TILT).axis
    held = [each for each in world.built.placed if each.assembly.startswith(CRADLE)]
    phone = MASTER.phone.block
    for tilt in (MASTER.tilt_range.low, 0.0, MASTER.tilt_range.high):
        turned = about(axis, tilt)
        loads = [((turned * phone.at * Pos(Z=phone.height / 2)).position, MASTER.heaviest_phone_kg)]
        loads += [
            ((turned * Pos(each.part.solid().center(CenterOf.MASS))).position, weight(each.part))
            for each in held
        ]
        torque = sum(kg * STANDARD_GRAVITY * abs(at.Y - axis.position.Y) for at, kg in loads)
        assert torque < HOLDING_SHARE * stepper.HOLDING_TORQUE_NM * 1000


@pytest.mark.check(
    does_not_catch="Whether face detection runs fast enough on the board.",
    subjects=("cradle",),
)
def test_r6_the_camera_rides_the_cradle_and_sees_past_it(world: World) -> None:
    (board,) = [each for each in world.built.placed if each.part.catalogue == CAMERA_BOARD]
    lens = (board.part.pose * MASTER.lens).position
    module = MASTER.camera_module
    reach = MASTER.plug_reach
    ahead = Pos(lens.X, lens.Y - reach / 2 - MASTER.fits.sliding, lens.Z)
    sight = Box(module.width, reach, module.height).moved(ahead)
    blocked = sum(
        (each.part.solid() & sight).volume for each in world.built.placed if each is not board
    )

    assert world.built.holder(board.part).parent_part.name == "cradle"
    assert blocked < TOUCHING_MM3


@pytest.mark.check(
    does_not_catch="The plug's strain relief and a cable pulled sideways.",
    subjects=("base",),
)
def test_r7_the_usb_c_socket_sits_on_a_part_that_never_moves(world: World) -> None:
    (port,) = [each for each in world.built.placed if each.part.catalogue == USB_C_BOARD]
    part = port.part
    chain = []
    while (holder := world.built.holder(part)) is not None:
        chain.append(holder.kind)
        part = holder.parent_part

    assert Kind.REVOLUTE not in chain


@pytest.mark.check(
    does_not_catch="Prices that change, estimates in the bill, the printing process (only the "
    "material is costed), tooling and assembly labour.",
    subjects=(),
)
def test_r8_the_landed_cost_is_under_the_target(world: World) -> None:
    lines = [line for line in bom(world) if line["kind"] in (Bill.MADE, Bill.BOUGHT)]
    parts = sum(float(line["unit_price"] or 0.0) * int(line["qty"] or 0) for line in lines)

    assert parts * (1 + MASTER.landing_share) < MASTER.landed_cost_target_usd


@pytest.mark.check(
    does_not_catch="A light, a sticker or a printed mark added later; how the window reads.",
    subjects=("cradle",),
)
def test_s1_the_front_shows_one_window(world: World) -> None:
    front = Plane.XZ.offset(-MASTER.cradle_front)
    faces = cradle(MASTER).solid().faces().filter_by(front)
    openings = sum(
        len(face.inner_wires())
        for face in faces
        if abs(face.center().Y - MASTER.cradle_front) < 1e-6
    )

    assert openings == 1


@pytest.mark.check(
    does_not_catch="How the cylinders read in real light; seams and print lines.",
    subjects=("base", "arm", "cap", "cradle"),
)
def test_s2_both_axes_show_as_cylinders_of_one_diameter_at_right_angles(world: World) -> None:
    pan, tilt = mate(world, PAN).axis, mate(world, TILT).axis
    footprint = base(MASTER).solid().bounding_box()
    drum = cap(MASTER).solid().bounding_box()

    assert abs(pan.direction.dot(tilt.direction)) < 1e-9
    assert pytest.approx(drum.size.Y) == footprint.size.X


@pytest.mark.check(
    does_not_catch="Colour matching between print batches and the finish itself.",
    subjects=tuple(b.__name__ for b in MADE),
)
def test_s3_every_made_part_is_one_material(world: World) -> None:
    assert len({each.part.material for each in world.built.placed if each.designed}) == 1


@pytest.mark.check(
    does_not_catch="How big it looks next to a real phone.",
    subjects=("base",),
)
def test_s4_the_base_is_no_wider_than_the_widest_phone(world: World) -> None:
    footprint = base(MASTER).solid().bounding_box()

    assert max(footprint.size.X, footprint.size.Y) <= MASTER.widest_phone
