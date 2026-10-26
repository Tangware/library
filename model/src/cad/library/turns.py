from build123d import Axis, Plane, Rotation, VectorLike

UPSIDE_DOWN = Rotation(180, 0, 0)
FACING_FRONT = Rotation(90, 0, 0)
FACING_BACK = Rotation(-90, 0, 0)
ALONG_X = Rotation(0, 90, 0)
END_FOR_END = Rotation(0, 180, 0)
CLOCKWISE_QUARTER = Rotation(0, 0, -90)
ANTICLOCKWISE_QUARTER = Rotation(0, 0, 90)
HALF_TURN = Rotation(0, 0, 180)
AGAINST_X = Rotation(0, -90, 0)


def turn_to(plane: Plane, toward: VectorLike) -> float:
    facing = Plane(Axis(plane.location), toward)
    return plane.x_dir.get_signed_angle(facing.x_dir, plane.z_dir)
