from dataclasses import dataclass

from bd_warehouse.fastener import polygon_diagonal
from build123d import (
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Hole,
    Location,
    Locations,
    Mode,
    Plane,
    RegularPolygon,
    extrude,
)

from cad.library.bought.catalogue import Bill, Catalogue
from cad.library.fits import Fits, Metal
from cad.library.shapes import (
    BORE,
    ENDS,
    FACES,
    OUTSIDE,
    Brep,
    Part,
    Seat,
    Shaped,
    built,
    round_faces,
    seat_of,
)
from cad.library.standard.fasteners import THREAD, Metric
from cad.standards import EulerStrut, HexSection, RoundSection, ThreadSection

FLATS = "flats"


@dataclass(frozen=True)
class TubeSize:
    outside: float
    wall: float

    @property
    def bore(self) -> float:
        return self.outside - 2 * self.wall


@dataclass(frozen=True)
class HexSize:
    across_flats: float

    @property
    def corner_radius(self) -> float:
        return polygon_diagonal(self.across_flats, 6) / 2

    def prism(self, start: float, end: float) -> Brep:
        with BuildPart() as bar:
            with BuildSketch(Plane.XY.offset(start)):
                RegularPolygon(self.across_flats / 2, 6, major_radius=False)
            extrude(amount=end - start)
        return built(bar)


G_PER_MM2 = 1e-6


@dataclass(frozen=True)
class SheetStock:
    bill: Bill
    thickness: float
    grams_per_m2: float


@dataclass(kw_only=True)
class StockTube(Part):
    size: TubeSize
    length: float
    wall_holes: tuple[Location, ...] = ()
    wall_hole: float = 0.0
    grade: Metal
    material: str = "aluminium"

    @property
    def label(self) -> str:
        z = self.size
        cut = f"aluminium tube Ø{z.outside:g} x {z.wall:g}, cut to {self.length:.0f} mm"
        if not self.wall_holes:
            return cut
        return f"{cut}, {len(self.wall_holes)} holes through one wall Ø{self.wall_hole:g}"

    @property
    def metal(self) -> Metal:
        return self.grade

    def rating(self, fits: Fits) -> EulerStrut:
        section = RoundSection(outside=self.size.outside, bore=self.size.bore)
        return EulerStrut(
            length=self.length,
            modulus_mpa=self.metal.modulus_mpa,
            section=section,
            connectors=(ENDS, OUTSIDE, BORE),
        )

    def shape(self) -> Brep:
        with BuildPart() as tube:
            with BuildSketch():
                Circle(self.size.outside / 2)
                Circle(self.size.bore / 2, mode=Mode.SUBTRACT)
            extrude(amount=self.length)
            if self.wall_holes:
                with Locations(*self.wall_holes):
                    Hole(self.wall_hole / 2, self.size.wall)
        return built(tube)

    def published(self) -> dict[str, Seat]:
        shape = self.unposed()
        return {
            ENDS: seat_of(shape.faces().filter_by(Plane.XY), Location()),
            OUTSIDE: seat_of(round_faces(shape, self.size.outside / 2), Location()),
            BORE: seat_of(round_faces(shape, self.size.bore / 2), Location()),
        }


@dataclass(kw_only=True)
class HexBar(Part):
    size: HexSize
    length: float
    grade: Metal
    material: str = "aluminium"

    @property
    def label(self) -> str:
        across = self.size.across_flats
        return f"{self.grade.name} aluminium hex AF{across:g}, cut to {self.length:.0f}"

    @property
    def metal(self) -> Metal:
        return self.grade

    def rating(self, fits: Fits) -> EulerStrut:
        section = HexSection(across_flats=self.size.across_flats)
        return EulerStrut(
            length=self.length,
            modulus_mpa=self.metal.modulus_mpa,
            section=section,
            connectors=(FLATS,),
        )

    def shape(self) -> Brep:
        return self.size.prism(0.0, self.length)

    def published(self) -> dict[str, Seat]:
        shape = self.unposed()
        return {FLATS: seat_of(shape.faces().filter_by(Axis.Z, reverse=True), Location())}


@dataclass(kw_only=True)
class ThreadedRod(Shaped):
    size: Metric
    length: float
    grade: Metal
    material: str = "steel"

    @property
    def label(self) -> str:
        name = f"{self.size.size} {self.grade.name}"
        return f"DIN 976-1 {name} threaded rod, cut to {self.length:.0f}"

    def rating(self, fits: Fits) -> EulerStrut:
        section = ThreadSection(diameter=self.size.diameter, pitch=self.size.pitch)
        return EulerStrut(
            length=self.length,
            modulus_mpa=self.metal.modulus_mpa,
            section=section,
            connectors=(THREAD,),
        )

    def published(self) -> dict[str, Seat]:
        return {THREAD: seat_of(round_faces(self.body, self.size.diameter / 2), Location())}

    @property
    def metal(self) -> Metal:
        return self.grade


@dataclass(kw_only=True)
class StockSheet(Shaped):
    stock: SheetStock
    material: str = "bought"

    @property
    def label(self) -> str:
        return f"{self.stock.bill.number} {self.stock.thickness:g} mm, cut to the template"

    def published(self) -> dict[str, Seat]:
        return {FACES: seat_of(self.body.faces(), Location())}

    @property
    def grams(self) -> float:
        return self.body.volume / self.stock.thickness * self.stock.grams_per_m2 * G_PER_MM2

    @property
    def catalogue(self) -> Catalogue:
        return Catalogue(
            file=self.name,
            grams=self.grams,
            model=self.shape,
            bill=self.stock.bill,
        )
