from collections import Counter
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, replace
from types import ModuleType

from build123d import Location

from cad.cables.models import Route
from cad.library.derived import Derived, derived
from cad.library.features.hardware import Fastening
from cad.library.mates import Connector, Mate, Reference, copy_keys, named
from cad.library.shapes import Part

type Made = Part | list[Part] | Fastening


@dataclass(frozen=True)
class Job:
    make: Callable[[], Made]
    builder: object
    args: tuple[object, ...]
    kwargs: dict[str, object]
    module: str

    def run(self) -> Fastening:
        match made := self.make():
            case Fastening():
                return made
            case list():
                return Fastening(parts=made, mates=[])
        return Fastening(parts=[made], mates=[])


def job[**P, R: Made](builder: Derived[P, R], *args: P.args, **kwargs: P.kwargs) -> Job:
    return Job(
        make=lambda: builder(*args, **kwargs),
        builder=builder,
        args=args,
        kwargs=kwargs,
        module=builder.__module__,
    )


class Assembly:
    def __init__(
        self,
        name: str,
        *holds: Job | Mate | Assembly,
        why: tuple[ModuleType, ...] = (),
        stress_analysed: bool = True,
        bench: bool = False,
        cables: Callable[[Fastening], Sequence[Route]] | None = None,
    ) -> None:
        self.name = name
        self.holds = holds
        self.why = why
        self.stress_analysed = stress_analysed
        self.bench = bench
        self.cables = cables


def _node(at: str, held: Assembly) -> str:
    return f"{at}/{held.name}".removeprefix("/")


def walked(assembly: Assembly, at: str = "") -> Iterator[tuple[str, Job | Mate]]:
    for held in assembly.holds:
        if isinstance(held, Assembly):
            yield from walked(held, _node(at, held))
        else:
            yield at, held


def jobs(assembly: Assembly) -> list[Job]:
    return [held for _, held in walked(assembly) if isinstance(held, Job)]


def instance_keys(parts: list[Part]) -> dict[int, str]:
    copies = Counter(part.name for part in parts)
    keys = {name: iter(copy_keys(name, count)) for name, count in copies.items()}
    return {id(part): next(keys[part.name]) for part in parts}


def unseated(mate: Mate) -> list[str]:
    faults = []
    for connector in (mate.child, mate.parent):
        try:
            faces = connector.seat.faces
        except ValueError as missing:
            missing.add_note(f"named by the mate {mate.name}")
            raise
        if not faces:
            faults.append(f"{mate.name}: {connector.name} on {named(connector.part)}")
    return faults


def joined(made: list[Fastening]) -> Fastening:
    parts = [part for each in made for part in each.parts]
    keys = instance_keys(parts)
    keyed = {keys[id(part)]: part for part in parts}

    def found(reference: Reference) -> Part:
        if isinstance(reference, Part) and id(reference) in keys:
            return reference
        if isinstance(reference, Part):
            reference = reference.name
        if reference not in keyed:
            raise ValueError(f"no built part is keyed {reference}")
        return keyed[reference]

    def resolved(connector: Connector) -> Connector:
        placing = connector.placing
        at = placing if isinstance(placing, Location | None) else found(placing)
        return Connector(found(connector.part), connector.name, at)

    mates = [
        replace(
            mate,
            child=resolved(mate.child),
            parent=resolved(mate.parent),
            fasteners=tuple(found(fastener) for fastener in mate.fasteners),
            servo=None if mate.servo is None else found(mate.servo),
        )
        for each in made
        for mate in each.mates
    ]
    faults = [fault for mate in mates for fault in unseated(mate)]
    if faults:
        raise ValueError("mates without seat faces: " + "; ".join(faults))
    return Fastening(parts=parts, mates=mates)


def placed(fastening: Fastening, made: list[tuple[str, Fastening]]) -> None:
    for node, each in made:
        for part in each.parts:
            part.group = f"{node}/{part.group}".strip("/")
    holders = {id(mate.child_part): mate.parent_part for mate in fastening.mates if not mate.closes}
    for part in fastening.parts:
        holder = part
        while not holder.group:
            holder = holders[id(holder)]
        part.group = holder.group


@derived
def assembled(assembly: Assembly) -> Fastening:
    made = [
        (node, held.run() if isinstance(held, Job) else Fastening(parts=[], mates=[held]))
        for node, held in walked(assembly)
    ]
    fastening = joined([each for _, each in made])
    placed(fastening, made)
    return fastening
