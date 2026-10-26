import itertools
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field

from build123d import Location, Plane

from cad.cables.bundle import packed, packed_diameter
from cad.cables.wires import bend_diameters
from cad.library.bought.catalogue import Bill, Catalogue
from cad.library.mates import Connector, Reference, joined
from cad.library.shapes import Part, Shaped

EMPTY = ""


@dataclass(frozen=True, kw_only=True)
class Wire:
    name: str
    diameter: float
    colour: str


@dataclass(frozen=True, kw_only=True)
class Splice:
    into: Cable


@dataclass(frozen=True, kw_only=True)
class Plug:
    name: str
    model: Catalogue | Splice | None
    pinout: tuple[str, ...]


@dataclass(frozen=True, kw_only=True)
class Jacketed:
    diameter: float
    rated_bend: float | None = None


@dataclass(frozen=True)
class Discrete:
    pass


@dataclass(frozen=True)
class Ribbon:
    pass


type Construction = Jacketed | Discrete | Ribbon


@dataclass(frozen=True)
class CutToFit:
    pass


@dataclass(frozen=True, kw_only=True)
class Cable:
    name: str
    wires: tuple[Wire, ...]
    plugs: tuple[Plug, ...]
    construction: Construction
    twist_rating: float
    length: float | CutToFit
    bill: Bill

    def __post_init__(self) -> None:
        names = {wire.name for wire in self.wires} | {EMPTY}
        for plug in self.plugs:
            if missing := [name for name in plug.pinout if name not in names]:
                raise ValueError(f"{self.name}: {plug.name} names {', '.join(missing)}, no wire")
            if isinstance(plug.model, Splice):
                joined = {wire.name for wire in plug.model.into.wires}
                if loose := [name for name in plug.pinout if name not in joined]:
                    into = plug.model.into.name
                    raise ValueError(
                        f"{self.name}: {plug.name} joins {', '.join(loose)}, not in {into}"
                    )
            used = Counter(name for name in plug.pinout if name != EMPTY)
            if twice := [name for name, count in used.items() if count > 1]:
                raise ValueError(f"{self.name}: {plug.name} lands {', '.join(twice)} twice")

    def ends(self, wire: str) -> tuple[tuple[int, int], ...]:
        return tuple(
            (plug, position)
            for plug, each in enumerate(self.plugs)
            for position, name in enumerate(each.pinout, start=1)
            if name == wire
        )

    def offsets(self, wires: Sequence[Wire]) -> dict[str, tuple[float, float]]:
        if isinstance(self.construction, Discrete):
            widest = max(wire.diameter for wire in wires)
            return dict(zip((wire.name for wire in wires), packed(len(wires), widest), strict=True))
        width = sum(wire.diameter for wire in self.wires)
        ends = itertools.accumulate(wire.diameter for wire in self.wires)
        flat = {
            wire.name: (end - wire.diameter / 2 - width / 2, 0.0)
            for wire, end in zip(self.wires, ends, strict=True)
        }
        return {wire.name: flat[wire.name] for wire in wires}

    def diameter(self, wires: Sequence[Wire]) -> float:
        match self.construction:
            case Jacketed(diameter=diameter):
                return diameter
            case Discrete():
                return packed_diameter(len(wires), max(wire.diameter for wire in wires))
        return sum(wire.diameter for wire in wires)

    def bend_radius(self, wires: Sequence[Wire], *, moving: bool, edgewise: float) -> float:
        rule = bend_diameters(moving)
        if isinstance(self.construction, Jacketed):
            rated = self.construction.rated_bend
            return rule * self.construction.diameter if rated is None else rated
        thickness = max(wire.diameter for wire in wires)
        if isinstance(self.construction, Discrete):
            return rule * thickness + self.diameter(wires) / 2
        width = sum(wire.diameter for wire in wires)
        return rule * thickness + (thickness + (width - thickness) * edgewise) / 2


@dataclass(frozen=True, kw_only=True)
class ServiceLoop:
    length: float
    plane: Plane | None = None


@dataclass(frozen=True, kw_only=True)
class RoutePoint:
    part: Reference
    at: Location
    face: Plane | None = None

    @property
    def frame(self) -> Location:
        placed = joined(self.part).pose * self.at
        if self.face is None:
            return placed
        return Location(Plane(origin=placed.position, x_dir=self.face.x_dir, z_dir=self.face.z_dir))


type Item = Connector | RoutePoint | ServiceLoop
type Plugged = Connector | RoutePoint


@dataclass(frozen=True, kw_only=True)
class Route:
    cable: Cable
    plugged: tuple[Plugged, ...]
    through: tuple[tuple[Item, ...], ...]

    def __post_init__(self) -> None:
        name, plugs = self.cable.name, len(self.cable.plugs)
        if len(self.plugged) != plugs:
            raise ValueError(f"{name} has {plugs} plugs in {len(self.plugged)} sockets")
        if len(self.through) != plugs - 1:
            raise ValueError(f"{name} has {len(self.through)} paths for {plugs - 1} branches")
        at_a_plug = [
            k in (0, len(path) - 1)
            for path in self.through
            for k, item in enumerate(path)
            if isinstance(item, ServiceLoop)
        ]
        if any(at_a_plug):
            raise ValueError(f"{name} hangs a service loop from a plug, not between two clips")

    @property
    def paths(self) -> list[tuple[int, tuple[Item, ...]]]:
        first, *others = self.plugged
        return [
            (plug, (first, *through, end))
            for plug, (through, end) in enumerate(zip(self.through, others, strict=True), start=1)
        ]


@dataclass(kw_only=True)
class Swept(Shaped):
    on: Part = field(compare=False)
    cable: str
    material: str = "cable"
