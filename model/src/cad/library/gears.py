from dataclasses import dataclass

from bd_warehouse.gear import SpurGearPlan
from build123d import Align, Axis, GeomType, Location, Plane, Rotation, extrude

from cad.library.derived import derived
from cad.library.features.planes import line_through, normal_to
from cad.library.fits import Fits
from cad.library.shapes import TEETH, Brep, Printed, SurfaceFaces, register
from cad.library.turns import turn_to
from cad.standards import ToothRoot

PRESSURE_ANGLE = 20.0
ADDENDUM = 1.0
DEDENDUM = 1.25
ROOT_FILLET = 0.0


def pitch_radius(teeth: int, module: float) -> float:
    return module * teeth / 2


def tip_radius(teeth: int, module: float) -> float:
    return pitch_radius(teeth, module) + ADDENDUM * module


def root_radius(teeth: int, module: float) -> float:
    return pitch_radius(teeth, module) - DEDENDUM * module


def gear_plan(teeth: int, module: float, rotation: float = 0.0) -> SpurGearPlan:
    return SpurGearPlan(
        module=module,
        tooth_count=teeth,
        pressure_angle=PRESSURE_ANGLE,
        addendum=ADDENDUM * module,
        dedendum=DEDENDUM * module,
        rotation=rotation,
        align=Align.NONE,
    )


@derived
def gear_solid(teeth: int, width: float, module: float) -> Brep:
    return extrude(gear_plan(teeth, module), amount=width)


def spur_teeth() -> None:
    register(TEETH, Location(), [SurfaceFaces(kind=GeomType.EXTRUSION)])


def crown_teeth() -> None:
    register(TEETH, Location(), [SurfaceFaces(kind=GeomType.BSPLINE)])


def mesh_phase(wheel: Location, wheel_teeth: int, pinion: Location, pinion_teeth: int) -> float:
    pinion_turning = normal_to(
        wheel.z_axis.direction, through=pinion, x_dir=pinion.x_axis.direction
    )
    wheel_pitch = 360 / wheel_teeth
    pinion_pitch = 360 / pinion_teeth
    wheel_off = turn_to(Plane(wheel), line_through(wheel, pinion).direction) / wheel_pitch
    pinion_off = turn_to(pinion_turning, line_through(pinion, wheel).direction) / pinion_pitch
    return (wheel_off + pinion_off - 1 / 2) * wheel_pitch


def crown_root(pitch: Plane, module: float) -> Plane:
    return pitch.offset(DEDENDUM * module)


def crown_phase(crown_axis: Axis, crown_teeth: int, pinion: Location, pinion_teeth: int) -> float:
    tooth_to_the_crown = pinion.x_axis.direction.get_signed_angle(
        crown_axis.direction, pinion.z_axis.direction
    )
    pinion_pitch = 360 / pinion_teeth
    off_the_gap = tooth_to_the_crown - pinion_pitch / 2
    return -off_the_gap * pinion_teeth / crown_teeth


def crown_meshing(pitch: Plane, toward_the_pinion: float, phase: float) -> Location:
    return Location(-pitch) * Rotation(0, 0, -(toward_the_pinion + phase))


def one_tooth_past(turn: float, teeth: int) -> float:
    return turn + 360 / teeth


@dataclass(kw_only=True)
class Gear(Printed):
    teeth: int
    module: float
    width: float

    def rating(self, fits: Fits) -> ToothRoot:
        filament = self.filament
        if filament is None:
            raise ValueError(f"{self.name} is a gear but not printed")
        return ToothRoot(
            teeth=self.teeth,
            module=self.module,
            width=self.width,
            pressure_deg=PRESSURE_ANGLE,
            dedendum=DEDENDUM,
            root_fillet=ROOT_FILLET,
            plastic=filament.plastic,
            connectors=(TEETH,),
        )
