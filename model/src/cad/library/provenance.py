from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from inspect import currentframe
from typing import Protocol


@dataclass(frozen=True)
class Feature:
    step: int
    name: str
    file: str
    line: int


@dataclass(frozen=True)
class Provenance:
    features: tuple[Feature, ...]
    made_by: tuple[int | None, ...]


class Recording(Protocol):
    def begin(self, name: str, file: str, line: int) -> Feature: ...

    def end(self, feature: Feature) -> None: ...


# The build service records each step here while it builds a part.
RECORDING: ContextVar[Recording | None] = ContextVar("recording", default=None)


@contextmanager
def step(name: str) -> Iterator[None]:
    recording = RECORDING.get()
    if recording is None:
        yield
        return
    here = currentframe()
    if here is None or here.f_back is None or here.f_back.f_back is None:
        raise RuntimeError("the interpreter keeps no frames to trace a step to its line")
    caller = here.f_back.f_back
    feature = recording.begin(name, caller.f_code.co_filename, caller.f_lineno)
    yield
    recording.end(feature)
