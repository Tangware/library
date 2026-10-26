import sys
from dataclasses import dataclass
from importlib import import_module  # noqa: TID251
from pathlib import Path
from pkgutil import iter_modules
from types import ModuleType

from cad.assembly.tree import Assembly
from cad.design.catalogue import Item
from cad.design.master import Master

MODEL = "model"
SOURCES = "src"


@dataclass(frozen=True)
class Design:
    root: Path
    package: str
    name: str
    master: Master
    assembly: Assembly
    catalogue: tuple[Item, ...]

    @property
    def model(self) -> Path:
        return self.root / MODEL

    @property
    def sources(self) -> Path:
        return self.model / SOURCES / self.package

    def item(self, name: str) -> Item:
        found = [item for item in self.catalogue if item.name == name]
        if len(found) != 1:
            raise ValueError(f"the catalogue lists {name} {len(found)} times")
        return found[0]

    def stock(self, material: str) -> Item | None:
        found = [item for item in self.catalogue if item.material == material]
        if len(found) > 1:
            raise ValueError(f"the catalogue lists {len(found)} items of the material {material}")
        return found[0] if found else None

    def listed(self, name: str) -> bool:
        return any(item.name == name for item in self.catalogue)


def _one[T](found: list[T], what: str, where: str) -> T:
    if len(found) != 1:
        raise ValueError(f"{where} holds {len(found)} {what}, not one")
    return found[0]


def _modules(package: ModuleType) -> list[ModuleType]:
    return [
        import_module(f"{package.__name__}.{info.name}") for info in iter_modules(package.__path__)
    ]


def _held(assembly: Assembly) -> list[Assembly]:
    inner = [held for held in assembly.holds if isinstance(held, Assembly)]
    return [*inner, *(deeper for each in inner for deeper in _held(each))]


def _top(modules: list[ModuleType]) -> Assembly:
    found = [
        value
        for module in modules
        for value in vars(module).values()
        if isinstance(value, Assembly)
    ]
    inside = {id(each) for assembly in found for each in _held(assembly)}
    return _one([each for each in found if id(each) not in inside], "top assemblies", "assemblies/")


def package_name(root: Path) -> str:
    sources = root / MODEL / SOURCES
    return _one(
        [p.name for p in sources.iterdir() if (p / "__init__.py").is_file()],
        "packages",
        str(sources),
    )


def load(root: Path) -> Design:
    root = root.resolve()
    package = package_name(root)
    sources = str(root / MODEL / SOURCES)
    if sources not in sys.path:
        sys.path.insert(0, sources)
    top = import_module(package)
    master = import_module(f"{package}.master")
    masters = [value for value in vars(master).values() if isinstance(value, Master)]
    catalogue = import_module(f"{package}.catalogue")
    return Design(
        root=root,
        package=package,
        name=str(top.NAME),
        master=_one(masters, "masters", f"{package}.master"),
        assembly=_top(_modules(import_module(f"{package}.assemblies"))),
        catalogue=tuple(catalogue.CATALOGUE),
    )
