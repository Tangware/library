from collections.abc import Mapping
from dataclasses import dataclass, field

from cad.library.cache import Skeleton
from cad.library.shapes import Block


@dataclass(frozen=True)
class Given:
    unit: str | Mapping[str, str]
    why: str
    source: str


def given[T](value: T, unit: str | Mapping[str, str], *, why: str, source: str) -> T:
    found: T = field(default=value, metadata={"given": Given(unit=unit, why=why, source=source)})
    return found


@dataclass(frozen=True)
class KeepOut:
    block: Block
    why: str


@dataclass(frozen=True)
class Envelope:
    block: Block
    why: str


@dataclass(frozen=True)
class Pose:
    name: str
    joints: dict[str, float]


REST = Pose(name="rest", joints={})


class Master(Skeleton):
    @property
    def poses(self) -> tuple[Pose, ...]:
        return (REST,)
