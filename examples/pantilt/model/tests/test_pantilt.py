from collections.abc import Callable, Iterator

import pytest
from build123d import Axis, Box, CenterOf, Location, Plane, Pos, Rotation
from cad.assembly.tree import assembled, instance_keys
from cad.design.built import manifest
from cad.design.catalogue import Kind as Bill
from cad.library.bought.vendor import Bought
from cad.library.extension_spring import ExtensionSpring
from cad.library.features.hardware import Fastening
from cad.library.features.planes import line_between
from cad.library.mates import Kind, Mate
from cad.library.shapes import Brep, Part, Printed

from pantilt.assemblies.pantilt import PRODUCT
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

MADE = (base, lid, arm, cap, cradle, jaw)
STANDARD_GRAVITY = 9.80665
HOLDING_SHARE = 0.5
TOUCHING_MM3 = 1.0
G_PER_KG = 1000.0
CRADLE = "pantilt/cradle"


@pytest.fixture(scope="module")
def world() -> Fastening:
    return assembled(PRODUCT)


@pytest.fixture(scope="module")
def kilograms(world: Fastening) -> dict[int, float]:
    built = manifest()
    grams = {part["id"]: part["mass_g"] for part in built["parts"]}
    named: dict[str, float] = {}
    for assembly in built["assemblies"]:
        named |= {each["name"]: grams[each["part"]] for each in assembly["instances"]}
        named |= {each["name"]: each["mass_g"] for each in assembly["hardware"]}
    keys = instance_keys(world.parts)
    return {id(part): named[keys[id(part)]] / G_PER_KG for part in world.parts}


def about(axis: Axis, angle: float) -> Location:
    frame = Location(Plane(origin=axis.position, z_dir=axis.direction))
    return frame * Rotation(0, 0, angle) * frame.inverse()


def mate(world: Fastening, name: str) -> Mate:
    (found,) = [each for each in world.mates if each.name == name]
    return found


def overlap(first: Brep, second: Brep) -> float:
    common = first & second
    return 0.0 if common is None else common.volume


def holder(world: Fastening, part: Part) -> Mate | None:
    found = [each for each in world.mates if each.child_part is part and not each.closes]
    return found[0] if found else None


def motion(joint: Mate, value: float) -> Location:
    if joint.kind is Kind.PRISMATIC:
        return Pos(*(joint.axis.direction * value))
    return about(joint.axis, value)


def shift(world: Fastening, part: Part, joints: dict[str, float]) -> Location:
    chain = []
    while (held := holder(world, part)) is not None:
        chain.append(held)
        part = held.parent_part
    moved = Location()
    for joint in reversed(chain):
        if joint.name in joints:
            moved = moved * motion(joint, joints[joint.name])
    return moved


def seated_bought(world: Fastening, first: Part, second: Part) -> bool:
    bought = isinstance(first, Bought) and isinstance(second, Bought)
    pair = {id(first), id(second)}
    return bought and any(
        {id(each.child_part), id(each.parent_part)} == pair for each in world.mates
    )


def clashes(world: Fastening, joints: dict[str, float]) -> Iterator[str]:
    placed = [part for part in world.parts if not isinstance(part, ExtensionSpring)]
    moved = {id(part): shift(world, part, joints) for part in placed}
    solids = {id(part): moved[id(part)] * part.solid() for part in placed}
    boxes = {id(part): solids[id(part)].bounding_box() for part in placed}
    for n, first in enumerate(placed):
        for second in placed[n + 1 :]:
            if moved[id(first)] == moved[id(second)] or seated_bought(world, first, second):
                continue
            if boxes[id(first)].disjoint(boxes[id(second)]):
                continue
            if overlap(solids[id(first)], solids[id(second)]) > TOUCHING_MM3:
                yield f"{first.name} hits {second.name}"


def centre_and_kilograms(
    world: Fastening, kilograms: dict[int, float], pan: float, tilt: float
) -> tuple[tuple[float, float], float]:
    phone = MASTER.phone.block
    phone_at = phone.at * Pos(Z=phone.height / 2)
    tilted = about(mate(world, PAN).axis, pan) * about(mate(world, TILT).axis, tilt)
    joints = {PAN: pan, TILT: tilt}
    points = [((tilted * phone_at).position, MASTER.heaviest_phone_kg)]
    points += [
        (
            (shift(world, part, joints) * Pos(part.solid().center(CenterOf.MASS))).position,
            kilograms[id(part)],
        )
        for part in world.parts
    ]
    total = sum(kg for _, kg in points)
    x = sum(at.X * kg for at, kg in points) / total
    y = sum(at.Y * kg for at, kg in points) / total
    return (x, y), total


@pytest.mark.check(
    does_not_catch="Strength, fit and finish.", subjects=tuple(b.build.__name__ for b in MADE)
)
@pytest.mark.parametrize("builder", MADE)
def test_m3_each_part_builds_from_the_master_alone(
    builder: Callable[[ProductMaster], Printed],
) -> None:
    assert builder(MASTER).solid().is_valid


@pytest.mark.check(
    does_not_catch="The spring's grip on the phone, the spring itself as it stretches, and "
    "phones with bumps or cases.",
    subjects=("jaw", "cradle"),
)
def test_r1_the_jaw_slides_from_the_widest_phone_to_the_narrowest_without_a_clash(
    world: Fastening,
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
def test_r1_the_spring_stays_taut_and_within_its_rating_over_the_jaw_travel(
    world: Fastening,
) -> None:
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
def test_r2_it_turns_a_quarter_each_way_without_a_clash(world: Fastening, end: str) -> None:
    assert list(clashes(world, {PAN: getattr(MASTER.pan_range, end)})) == []


@pytest.mark.check(
    does_not_catch="The phone itself against the arm, and parts within the mesh tolerance.",
    subjects=("cradle", "arm"),
)
@pytest.mark.parametrize("end", ["low", "high"])
def test_r3_it_tilts_through_its_range_without_a_clash(world: Fastening, end: str) -> None:
    assert list(clashes(world, {TILT: getattr(MASTER.tilt_range, end)})) == []


@pytest.mark.check(
    does_not_catch="Noise from the drivers' chopping, resonance, and the firmware's ramps.",
    subjects=("arm", "cradle"),
)
def test_r4_each_axis_turns_on_its_motor_shaft_with_no_gear_between(world: Fastening) -> None:
    for joint in (PAN, TILT):
        turning = mate(world, joint)
        carried = [held for held in world.mates if held.parent_part is turning.child_part]
        assert turning.kind is Kind.REVOLUTE
        assert turning.parent_part.catalogue == STATOR
        assert turning.child_part.catalogue == ROTOR
        assert carried
        assert all(held.kind is Kind.RIGID for held in carried)
    assert not [held for held in world.mates if held.kind is Kind.GEAR]


@pytest.mark.check(
    does_not_catch="Knocks, a tug on the cable, a slippery desk, and the mass of a phone case.",
    subjects=("base",),
)
def test_r5_it_stands_with_the_heaviest_phone_at_every_pose(
    world: Fastening, kilograms: dict[int, float]
) -> None:
    for pose in MASTER.poses:
        centre, _ = centre_and_kilograms(
            world, kilograms, pose.joints.get(PAN, 0.0), pose.joints.get(TILT, 0.0)
        )
        x, y = centre
        assert line_between(Pos(), Pos(x, y)).length < MASTER.radius


@pytest.mark.check(
    does_not_catch="Holding torque lost to microstepping, heat or a low supply; the jaw's grip.",
    subjects=("cradle",),
)
def test_r5_the_tilt_motor_holds_the_heaviest_phone_at_every_tilt(
    world: Fastening, kilograms: dict[int, float]
) -> None:
    axis = mate(world, TILT).axis
    held = [part for part in world.parts if part.group.startswith(CRADLE)]
    phone = MASTER.phone.block
    for tilt in (MASTER.tilt_range.low, 0.0, MASTER.tilt_range.high):
        turned = about(axis, tilt)
        loads = [((turned * phone.at * Pos(Z=phone.height / 2)).position, MASTER.heaviest_phone_kg)]
        loads += [
            ((turned * Pos(part.solid().center(CenterOf.MASS))).position, kilograms[id(part)])
            for part in held
        ]
        torque = sum(kg * STANDARD_GRAVITY * abs(at.Y - axis.position.Y) for at, kg in loads)
        assert torque < HOLDING_SHARE * stepper.HOLDING_TORQUE_NM * 1000


@pytest.mark.check(
    does_not_catch="Whether face detection runs fast enough on the board.",
    subjects=("cradle",),
)
def test_r6_the_camera_rides_the_cradle_and_sees_past_it(world: Fastening) -> None:
    (board,) = [part for part in world.parts if part.catalogue == CAMERA_BOARD]
    lens = (board.pose * MASTER.lens).position
    module = MASTER.camera_module
    reach = MASTER.plug_reach
    ahead = Pos(lens.X, lens.Y - reach / 2 - MASTER.fits.sliding, lens.Z)
    sight = Box(module.width, reach, module.height).moved(ahead)
    blocked = sum(overlap(part.solid(), sight) for part in world.parts if part is not board)

    held = holder(world, board)
    assert held is not None
    assert held.parent_part.name == "cradle"
    assert blocked < TOUCHING_MM3


@pytest.mark.check(
    does_not_catch="The plug's strain relief and a cable pulled sideways.",
    subjects=("base",),
)
def test_r7_the_usb_c_socket_sits_on_a_part_that_never_moves(world: Fastening) -> None:
    (part,) = [each for each in world.parts if each.catalogue == USB_C_BOARD]
    chain = []
    while (held := holder(world, part)) is not None:
        chain.append(held.kind)
        part = held.parent_part

    assert Kind.REVOLUTE not in chain


@pytest.mark.check(
    does_not_catch="Prices that change, estimates in the bill, the printing process (only the "
    "material is costed), tooling and assembly labour.",
    subjects=(),
)
def test_r8_the_landed_cost_is_under_the_target() -> None:
    lines = [line for line in manifest()["bom"] if line["kind"] in (Bill.MADE, Bill.BOUGHT)]
    parts = sum(float(line["unit_price"] or 0.0) * int(line["qty"] or 0) for line in lines)

    assert parts * (1 + MASTER.landing_share) < MASTER.landed_cost_target_usd


@pytest.mark.check(
    does_not_catch="A light, a sticker or a printed mark added later; how the window reads.",
    subjects=("cradle",),
)
def test_s1_the_front_shows_one_window(world: Fastening) -> None:
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
def test_s2_both_axes_show_as_cylinders_of_one_diameter_at_right_angles(world: Fastening) -> None:
    pan, tilt = mate(world, PAN).axis, mate(world, TILT).axis
    footprint = base(MASTER).solid().bounding_box()
    drum = cap(MASTER).solid().bounding_box()

    assert abs(pan.direction.dot(tilt.direction)) < 1e-9
    assert pytest.approx(drum.size.Y) == footprint.size.X


@pytest.mark.check(
    does_not_catch="Colour matching between print batches and the finish itself.",
    subjects=tuple(b.build.__name__ for b in MADE),
)
def test_s3_every_made_part_is_one_material(world: Fastening) -> None:
    assert len({part.material for part in world.parts if isinstance(part, Printed)}) == 1


@pytest.mark.check(
    does_not_catch="How big it looks next to a real phone.",
    subjects=("base",),
)
def test_s4_the_base_is_no_wider_than_the_widest_phone(world: Fastening) -> None:
    footprint = base(MASTER).solid().bounding_box()

    assert max(footprint.size.X, footprint.size.Y) <= MASTER.widest_phone
