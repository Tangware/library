from math import acos, cos, pi, radians, sin, sqrt, tan

from build123d import (
    Align,
    BasePartObject,
    BuildLine,
    BuildPart,
    BuildSketch,
    Circle,
    Face,
    IntersectingLine,
    Line,
    Mode,
    Plane,
    PolarLocations,
    RotationLike,
    Spline,
    add,
    extrude,
    loft,
    make_face,
    mirror,
)

from cad.library.shapes import built

SECTIONS = 7
FLANK_POINTS = 8
SECTION_SOLVE_STEPS = 8


def _involute(angle: float) -> float:
    return tan(angle) - angle


def undercut_free_radius(
    module: float,
    tooth_count: int,
    pinion_tooth_count: int,
    pressure_angle: float,
    addendum: float | None = None,
) -> float:
    pinion_pitch_radius = module * pinion_tooth_count / 2
    pinion_base_radius = pinion_pitch_radius * cos(radians(pressure_angle))
    reach = addendum if addendum is not None else module
    rolling = pinion_base_radius**2 / (pinion_pitch_radius - reach)
    working_angle = acos(pinion_base_radius / rolling)
    off_the_axis = rolling * sin(working_angle) * cos(working_angle)
    return sqrt((rolling * tooth_count / pinion_tooth_count) ** 2 + off_the_axis**2)


def undercut_free_teeth(
    inner_radius: float, module: float, pinion_tooth_count: int, pressure_angle: float
) -> int:
    teeth = pinion_tooth_count
    while (
        undercut_free_radius(module, teeth + 1, pinion_tooth_count, pressure_angle) <= inner_radius
    ):
        teeth += 1
    return teeth


class CrownGear(BasePartObject):
    def __init__(
        self,
        module: float,
        tooth_count: int,
        pressure_angle: float,
        thickness: float,
        pinion_tooth_count: int,
        addendum: float | None = None,
        dedendum: float | None = None,
        base_height: float | None = None,
        inner_radius: float | None = None,
        rotation: RotationLike = (0, 0, 0),
        align: Align | tuple[Align, Align, Align] | None = Align.CENTER,
        mode: Mode = Mode.ADD,
    ):
        self.module = module
        self.tooth_count = tooth_count
        self.pinion_tooth_count = pinion_tooth_count
        self.ratio = tooth_count / pinion_tooth_count
        self.pressure_angle = radians(pressure_angle)
        self.addendum = addendum if addendum is not None else module
        self.dedendum = dedendum if dedendum is not None else 1.25 * module
        self.base_height = base_height if base_height is not None else 2 * module
        self.pinion_pitch_radius = module * pinion_tooth_count / 2
        self.pinion_base_radius = self.pinion_pitch_radius * cos(self.pressure_angle)
        self.pinion_addendum_radius = self.pinion_pitch_radius + module
        self.pitch_radius = module * tooth_count / 2
        self.inner_radius = (
            inner_radius
            if inner_radius is not None
            else undercut_free_radius(
                module, tooth_count, pinion_tooth_count, pressure_angle, self.addendum
            )
        )
        self.outer_radius = self.inner_radius + thickness

        with BuildSketch(Plane.XY.offset(-self.dedendum)) as ring:
            Circle(self.outer_radius)
            Circle(self.inner_radius, mode=Mode.SUBTRACT)
        flanks = loft([self._tooth_section(section) for section in self._sections()])
        tooth = flanks & extrude(ring.sketch, amount=self.dedendum + self.addendum)
        with BuildPart() as crown:
            extrude(ring.sketch, amount=-self.base_height)
            with PolarLocations(0, tooth_count):
                add(tooth)
        super().__init__(built(crown).solid(), rotation, align, mode)

    def _sections(self) -> list[float]:
        first = self.inner_radius * cos(pi / self.tooth_count)
        last = self.outer_radius / cos(pi / self.tooth_count)
        return [first + (last - first) * i / (SECTIONS - 1) for i in range(SECTIONS)]

    def _flank(self, across: float, height: float) -> tuple[float, float]:
        rolling = across / self.ratio
        working_angle = acos(self.pinion_base_radius / rolling)
        half_space = (
            pi / (2 * self.pinion_tooth_count)
            - _involute(self.pressure_angle)
            + _involute(working_angle)
        )
        along = (height - (self.pinion_pitch_radius - rolling)) / sin(working_angle)
        aside = along * cos(working_angle)
        turn = (along / self.pinion_base_radius - half_space) / self.ratio
        return (
            across * cos(turn) + aside * sin(turn),
            aside * cos(turn) - across * sin(turn),
        )

    def _flank_in_section(self, section: float, height: float) -> float:
        across = section
        for _ in range(SECTION_SOLVE_STEPS):
            across += section - self._flank(across, height)[0]
        return self._flank(across, height)[1]

    def _lowest_contact(self, section: float) -> float:
        rolling = section / self.ratio
        working_angle = acos(self.pinion_base_radius / rolling)
        tip_reach = sqrt(self.pinion_addendum_radius**2 - self.pinion_base_radius**2)
        along = rolling * sin(working_angle) - tip_reach
        return max(self.pinion_pitch_radius - rolling + along * sin(working_angle), -self.dedendum)

    def _tooth_section(self, section: float) -> Face:
        low = self._lowest_contact(section)
        heights = [
            low + (self.addendum - low) * i / (FLANK_POINTS - 1) for i in range(FLANK_POINTS)
        ]
        with BuildSketch(Plane.YZ.offset(section)) as outline:
            with BuildLine():
                root = Line(
                    (-pi * self.module, -self.dedendum),
                    (pi * self.module, -self.dedendum),
                    mode=Mode.PRIVATE,
                )
                flank = Spline(*[(self._flank_in_section(section, z), z) for z in heights])
                foot = IntersectingLine(flank @ 0, -(flank % 0), root)
                other_flank = mirror(flank, about=Plane.YZ).edge()
                other_foot = mirror(foot, about=Plane.YZ).edge()
                Line(flank @ 1, other_flank @ 1)
                Line(foot @ 1, other_foot @ 1)
            make_face()
        section_face: Face = outline.sketch.face()
        return section_face
