from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, StrEnum
from functools import cache
from typing import Final, Literal

from bd_warehouse.fastener import (
    HeatSetNut,
    HexHeadScrew,
    HexNut,
    PanHeadScrew,
    PlainWasher,
    SocketHeadCapScrew,
    evaluate_parameter_dict,
    isolate_fastener_type,
    read_drill_sizes,
)
from bd_warehouse.fastener import Nut as FastenerNut
from bd_warehouse.fastener import Screw as FastenerScrew
from bd_warehouse.fastener import ShoulderScrew as FastenerShoulderScrew
from build123d import (
    TOLERANCE,
    Align,
    CounterBoreHole,
    Cylinder,
    Hole,
    Location,
    Plane,
)

from cad.library.derived import derived
from cad.library.fits import (
    BRASS,
    NUT_PROOF_MPA,
    PIN_DOUBLE_SHEAR_N,
    Fits,
    Metal,
)
from cad.library.models import din985_lock_nut
from cad.library.shapes import (
    BORE,
    FACES,
    OUTSIDE,
    Brep,
    Part,
    Seat,
    flat_faces,
    round_faces,
    round_faces_below,
    seat_of,
)
from cad.standards import Direction, NutProof, RatedForce, ScrewStrength


class Metric(StrEnum):
    M1_6 = "M1.6-0.35"
    M2 = "M2-0.4"
    M2_5 = "M2.5-0.45"
    M3 = "M3-0.5"
    M4 = "M4-0.7"
    M5 = "M5-0.8"
    M6 = "M6-1"

    @property
    def size(self) -> str:
        return self.value.partition("-")[0]

    @property
    def diameter(self) -> float:
        return float(self.size.removeprefix("M"))

    @property
    def pitch(self) -> float:
        return float(self.value.partition("-")[2])


SOCKET_HEAD: Final = "iso4762"
PAN_HEAD: Final = "iso1580"
HEX_NUT: Final = "iso4032"
THIN_NUT: Final = "iso4035"
HEX_BOLT: Final = "din931"
SHOULDER_SCREW: Final = "iso7379"
PLAIN_WASHER: Final = "iso7091"
TAP_MATERIAL = "Soft"
UNDER_HEAD = "under head"
THREAD = "thread"
BEARING_FACE = "bearing face"
SHOULDER = "shoulder"
THREADS_PAST_THE_NUT = 2
SPRING_PIN = "ISO 8752 spring pin"
DOWEL = "ISO 8734 dowel pin"
STAINLESS = "stainless"


type Table = type[
    SocketHeadCapScrew
    | PanHeadScrew
    | HexHeadScrew
    | FastenerShoulderScrew
    | HexNut
    | PlainWasher
    | HeatSetNut
]


@cache
def _text(kind: Table, standard: str, size: str) -> dict[str, str]:
    found: dict[str, str] = isolate_fastener_type(standard, kind.fastener_data)[size]
    return found


@cache
def _data(kind: Table, standard: str, size: str) -> dict[str, float]:
    found: dict[str, float] = evaluate_parameter_dict(_text(kind, standard, size))
    return found


def screw_connectors(shape: Brep) -> dict[str, Seat]:
    return {
        UNDER_HEAD: seat_of(flat_faces(shape, 0.0), Location()),
        THREAD: seat_of(round_faces_below(shape, 0.0), Location()),
    }


def nut_connectors(shape: Brep, size: Metric) -> dict[str, Seat]:
    thread = round_faces(shape, size.diameter / 2)
    return {
        BEARING_FACE: seat_of(flat_faces(shape, 0.0), Location()),
        THREAD: seat_of(thread, Location()),
    }


def clearance(screw: Metric, *, fits: Fits) -> float:
    return float(FastenerScrew.clearance_hole_data[screw.size][fits.clearance_fit])


def clearance_range(screw: Metric) -> tuple[float, float]:
    fits = FastenerScrew.clearance_hole_data[screw.size]
    return fits["Close"], fits["Loose"]


def passing_range(screw: Metric) -> tuple[float, float]:
    return screw.diameter, FastenerScrew.clearance_hole_data[screw.size]["Loose"]


def tapped(screw: Metric) -> float:
    return float(FastenerScrew.tap_hole_data[screw][TAP_MATERIAL])


def pilot(screw: Metric, *, fits: Fits) -> float:
    return fits.printed(fits.plastic_pilot * screw.diameter)


def thread_depth(screw: Metric, *, fits: Fits) -> float:
    return fits.plastic_thread * screw.diameter


def head_diameter(screw: Metric) -> float:
    return float(_data(SocketHeadCapScrew, SOCKET_HEAD, screw)["dk"])


def head_height(screw: Metric) -> float:
    return float(_data(SocketHeadCapScrew, SOCKET_HEAD, screw)["k"])


def counterbore_radius(screw: Metric, *, fits: Fits) -> float:
    counterbore = clearance(screw, fits=fits) - screw.diameter + head_diameter(screw)
    return counterbore / 2


def nut_across_flats(screw: Metric) -> float:
    return float(_data(HexNut, HEX_NUT, screw)["s"])


def socket_across_flats(screw: Metric) -> float:
    return float(_data(SocketHeadCapScrew, SOCKET_HEAD, screw)["s"])


def shoulder_socket_across_flats(screw: Metric) -> float:
    return float(_data(FastenerShoulderScrew, SHOULDER_SCREW, screw)["s"])


def nut_height(screw: Metric) -> float:
    return float(_data(HexNut, HEX_NUT, screw)["m"])


def shoulder_diameter(screw: Metric) -> float:
    return float(_data(FastenerShoulderScrew, SHOULDER_SCREW, screw)["ds"])


def shoulder_head_height(screw: Metric) -> float:
    return float(_data(FastenerShoulderScrew, SHOULDER_SCREW, screw)["k"])


def shoulder_thread(screw: Metric) -> float:
    return float(_data(FastenerShoulderScrew, SHOULDER_SCREW, screw)["b"])


def washer_thickness(screw: Metric) -> float:
    return float(_data(PlainWasher, PLAIN_WASHER, screw.size)["h"])


def washer_bore(screw: Metric) -> float:
    return float(_data(PlainWasher, PLAIN_WASHER, screw.size)["d1"])


def past_the_nut(screw: Metric) -> float:
    return THREADS_PAST_THE_NUT * screw.pitch


def shortest_at_least(lengths: Sequence[float], needed: float) -> float:
    return float(min(length for length in lengths if length >= needed - TOLERANCE))


def longest_at_most(lengths: Sequence[float], room: float) -> float:
    return float(max(length for length in lengths if length <= room + TOLERANCE))


class Ends(Enum):
    PAST = "past"
    WITHIN = "within"


@dataclass(frozen=True, kw_only=True)
class Stock:
    inserts: dict[Metric, str]
    insert_maker: str
    screw_lengths: dict[tuple[Metric, str], tuple[float, ...]]
    fastener_grade: Metal


STOCK_UNITS = {"inserts": "-", "insert_maker": "-", "screw_lengths": "mm", "fastener_grade": "-"}


STANDARDS: dict[str, type[SocketHeadCapScrew | HexHeadScrew | FastenerShoulderScrew]] = {
    SOCKET_HEAD: SocketHeadCapScrew,
    HEX_BOLT: HexHeadScrew,
    SHOULDER_SCREW: FastenerShoulderScrew,
}


def made_lengths(size: Metric, standard: str = SOCKET_HEAD) -> list[float]:
    data = _data(STANDARDS[standard], standard, size)
    return [
        float(length)
        for length in FastenerScrew.nominal_length_range[standard]
        if data["short"] <= length <= data["long"]
    ]


def screw_length(
    size: Metric, reach: float, ends: Ends, standard: str = SOCKET_HEAD, *, stock: Stock
) -> float:
    made = made_lengths(size, standard)
    stocked = (size, standard) in stock.screw_lengths
    lengths = [
        length for length in made if not stocked or length in stock.screw_lengths[size, standard]
    ]
    match ends:
        case Ends.PAST:
            return shortest_at_least(lengths, reach)
        case Ends.WITHIN:
            return float(max(length for length in lengths if length <= reach + TOLERANCE))


def clearance_hole(screw: Metric, depth: float | None = None, *, fits: Fits) -> Hole:
    return Hole(fits.printed(clearance(screw, fits=fits)) / 2, depth)


def pilot_hole(screw: Metric, depth: float, *, fits: Fits) -> Hole:
    return Hole(pilot(screw, fits=fits) / 2, depth)


def counterbored_hole(
    screw: Metric, seat: float, depth: float | None = None, *, fits: Fits
) -> CounterBoreHole:
    return CounterBoreHole(
        fits.printed(clearance(screw, fits=fits)) / 2,
        counterbore_radius(screw, fits=fits),
        seat,
        depth,
    )


@derived
def _screw(size: Metric, length: float) -> Brep:
    return SocketHeadCapScrew(size, length, SOCKET_HEAD, simple=True)


def _screw_strength(size: Metric, metal: Metal) -> ScrewStrength:
    return ScrewStrength(diameter=size.diameter, pitch=size.pitch, yield_mpa=metal.yield_mpa)


@dataclass(kw_only=True)
class Screw(Part):
    size: Metric
    length: float
    grade: Metal
    material: str = STAINLESS

    @property
    def label(self) -> str:
        return f"{self.size.size} x {self.length:g} socket head cap screw"

    @property
    def metal(self) -> Metal:
        return self.grade

    @property
    def head_diameter(self) -> float:
        return head_diameter(self.size)

    def rating(self, fits: Fits) -> ScrewStrength:
        return _screw_strength(self.size, self.metal)

    def shape(self) -> Brep:
        return _screw(self.size, self.length)

    def published(self) -> dict[str, Seat]:
        return screw_connectors(self.unposed())


@derived
def _pan_head(size: Metric, length: float) -> Brep:
    return PanHeadScrew(size, length, PAN_HEAD, simple=True)


@dataclass(frozen=True)
class PanHead:
    radius: float
    height: float


def pan_head(screw: Metric) -> PanHead:
    head = _data(PanHeadScrew, PAN_HEAD, screw.value)
    return PanHead(radius=head["dk"] / 2, height=head["k"])


@dataclass(kw_only=True)
class PanScrew(Part):
    size: Metric
    length: float
    tapping: bool = False
    grade: Metal
    material: str = "steel"

    @property
    def label(self) -> str:
        kind = "self-tapping screw" if self.tapping else "pan head screw"
        return f"{self.size.size} x {self.length:g} {kind}"

    @property
    def metal(self) -> Metal:
        return self.grade

    @property
    def head_diameter(self) -> float:
        return 2 * pan_head(self.size).radius

    def rating(self, fits: Fits) -> ScrewStrength:
        return _screw_strength(self.size, self.metal)

    def shape(self) -> Brep:
        return _pan_head(self.size, self.length)

    def published(self) -> dict[str, Seat]:
        return screw_connectors(self.unposed())


@derived
def _nut(size: Metric, standard: Literal["iso4032", "iso4035"]) -> Brep:
    return HexNut(size, standard, simple=True)


@dataclass(kw_only=True)
class Nut(Part):
    size: Metric
    grade: Metal
    material: str = STAINLESS

    @property
    def label(self) -> str:
        return f"{self.size.size} hex nut"

    @property
    def metal(self) -> Metal:
        return self.grade

    def rating(self, fits: Fits) -> NutProof:
        return NutProof(diameter=self.size.diameter, pitch=self.size.pitch, proof_mpa=NUT_PROOF_MPA)

    def shape(self) -> Brep:
        return _nut(self.size, HEX_NUT)

    def published(self) -> dict[str, Seat]:
        return nut_connectors(self.unposed(), self.size)


@dataclass(kw_only=True)
class JamNut(Nut):
    @property
    def label(self) -> str:
        return f"{self.size.size} ISO 4035 thin hex nut"

    def shape(self) -> Brep:
        return _nut(self.size, THIN_NUT)


def lock_nut_height(screw: Metric) -> float:
    return din985_lock_nut.SIZES[screw.size].height


def lock_nut_across_flats(screw: Metric) -> float:
    return din985_lock_nut.SIZES[screw.size].across_flats


@derived
def _lock_nut(size: Metric) -> Brep:
    return din985_lock_nut.lock_nut(size.size, size.diameter)


@dataclass(kw_only=True)
class LockNut(Part):
    size: Metric
    grade: Metal
    material: str = "steel"

    @property
    def label(self) -> str:
        return f"{self.size.size} DIN 985 nylon-insert lock nut"

    @property
    def metal(self) -> Metal:
        return self.grade

    def rating(self, fits: Fits) -> NutProof:
        return NutProof(diameter=self.size.diameter, pitch=self.size.pitch, proof_mpa=NUT_PROOF_MPA)

    def shape(self) -> Brep:
        return _lock_nut(self.size)

    def published(self) -> dict[str, Seat]:
        return nut_connectors(self.unposed(), self.size)


def hex_bolt_head(screw: Metric) -> float:
    return float(_data(HexHeadScrew, HEX_BOLT, screw)["k"])


def hex_bolt_across_flats(screw: Metric) -> float:
    return float(_data(HexHeadScrew, HEX_BOLT, screw)["s"])


@derived
def _hex_bolt(size: Metric, length: float) -> Brep:
    return HexHeadScrew(size, length, HEX_BOLT, simple=True)


@dataclass(kw_only=True)
class HexBolt(Part):
    size: Metric
    length: float
    grade: Metal
    material: str = "steel"

    @property
    def label(self) -> str:
        return f"{self.size.size} x {self.length:g} DIN 931 {self.grade.name} hex bolt"

    @property
    def metal(self) -> Metal:
        return self.grade

    @property
    def head_diameter(self) -> float:
        return hex_bolt_across_flats(self.size)

    def rating(self, fits: Fits) -> ScrewStrength:
        return _screw_strength(self.size, self.metal)

    def shape(self) -> Brep:
        return _hex_bolt(self.size, self.length)

    def published(self) -> dict[str, Seat]:
        return screw_connectors(self.unposed())


@derived
def _shoulder_screw(size: Metric, length: float) -> Brep:
    return FastenerShoulderScrew(size, length, SHOULDER_SCREW, simple=True)


@dataclass(kw_only=True)
class ShoulderScrew(Part):
    size: Metric
    length: float
    grade: Metal
    material: str = "steel"

    @property
    def label(self) -> str:
        return f"{self.size.size} Ø{self.diameter:g} x {self.length:g} ISO 7379 shoulder screw"

    @property
    def metal(self) -> Metal:
        return self.grade

    @property
    def diameter(self) -> float:
        return shoulder_diameter(self.size)

    def shape(self) -> Brep:
        return _shoulder_screw(self.size, self.length)

    def published(self) -> dict[str, Seat]:
        shoulder = seat_of(round_faces(self.unposed(), self.diameter / 2), Location())
        return {**screw_connectors(self.unposed()), SHOULDER: shoulder}


@derived
def _washer(size: Metric) -> Brep:
    return PlainWasher(size.size, PLAIN_WASHER)


SCREWS = (Screw, PanScrew, HexBolt)


@dataclass(kw_only=True)
class Washer(Part):
    size: Metric
    grade: Metal
    material: str = "steel"

    @property
    def label(self) -> str:
        return f"{self.size.size} ISO 7091 washer"

    @property
    def metal(self) -> Metal:
        return self.grade

    def shape(self) -> Brep:
        return _washer(self.size)

    def published(self) -> dict[str, Seat]:
        shape = self.unposed()
        bore = round_faces(shape, washer_bore(self.size) / 2)
        return {
            BORE: seat_of(bore, Location()),
            FACES: seat_of(shape.faces().filter_by(Plane.XY), Location()),
        }


@dataclass(kw_only=True)
class Pin(Part):
    diameter: float
    length: float
    standard: str = SPRING_PIN
    material: str = "steel"

    @property
    def label(self) -> str:
        return f"{self.standard} Ø{self.diameter:g} x {self.length:g}"

    @property
    def rated_double_shear_n(self) -> float:
        return PIN_DOUBLE_SHEAR_N[self.diameter]

    def rating(self, fits: Fits) -> RatedForce:
        return RatedForce(
            check="pin double shear", rated_n=self.rated_double_shear_n, direction=Direction.ACROSS
        )

    def shape(self) -> Brep:
        return Cylinder(
            self.diameter / 2, self.length, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )

    def published(self) -> dict[str, Seat]:
        return {OUTSIDE: seat_of(round_faces(self.unposed(), self.diameter / 2), Location())}


@derived
def _heat_set_nut(designation: str, maker: str) -> Brep:
    insert: type[FastenerNut] = HeatSetNut
    return insert(designation, maker)


@dataclass(frozen=True)
class InsertSize:
    outside: float
    length: float
    hole: float


def insert_size(screw: Metric, *, fits: Fits, stock: Stock) -> InsertSize:
    designation = stock.inserts[screw]
    data = _data(HeatSetNut, stock.insert_maker, designation)
    drill = read_drill_sizes()[_text(HeatSetNut, stock.insert_maker, designation)["drill"].strip()]
    return InsertSize(outside=data["s"], length=data["m"], hole=fits.printed(drill))


@dataclass(kw_only=True)
class ThreadedInsert(Part):
    designation: str
    maker: str
    material: str = "steel"

    @property
    def size(self) -> Metric:
        return Metric(self.designation.rpartition("-")[0])

    @property
    def label(self) -> str:
        number, _, _ = _text(HeatSetNut, self.maker, self.designation)["part"].partition(" (")
        return f"{self.maker} {self.size.size} x {self.length:g} heat-set insert {number}"

    @property
    def metal(self) -> Metal:
        return BRASS

    @property
    def outside(self) -> float:
        return float(_data(HeatSetNut, self.maker, self.designation)["s"])

    @property
    def length(self) -> float:
        return float(_data(HeatSetNut, self.maker, self.designation)["m"])

    def pull_out_n(self, fits: Fits) -> float:
        if self.size.diameter not in fits.insert_pull_out_n:
            missing = f"no insert pull-out force for {self.size.size}"
            raise ValueError(f"{self.group}/{self.name}: {missing}")
        return fits.insert_pull_out_n[self.size.diameter]

    def rating(self, fits: Fits) -> RatedForce:
        return RatedForce(
            check="insert pull-out", rated_n=self.pull_out_n(fits), direction=Direction.ALONG
        )

    def shape(self) -> Brep:
        return _heat_set_nut(self.designation, self.maker)

    def published(self) -> dict[str, Seat]:
        shape = self.unposed()
        thread = round_faces(shape, self.size.diameter / 2)
        outside = [face for face in shape.faces() if face not in thread]
        return {OUTSIDE: seat_of(outside, Location()), THREAD: seat_of(thread, Location())}


def insert_hole(screw: Metric, *, fits: Fits, stock: Stock) -> Hole:
    insert = insert_size(screw, fits=fits, stock=stock)
    return Hole(insert.hole / 2, insert.length)
