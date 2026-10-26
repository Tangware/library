from collections.abc import Callable
from contextvars import Context
from functools import wraps
from typing import Protocol


class Skeleton:
    pass


class Builds(Protocol):
    def __call__[**P, R](
        self, builder: Cached[P, R], /, *args: P.args, **kwargs: P.kwargs
    ) -> R: ...


class Cached[**P, R]:
    def __init__(self, build: Callable[P, R]) -> None:
        self.build = build
        wraps(build)(self)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return builds(self, *args, **kwargs)


class Designed[**P, R](Cached[P, R]):
    pass


def plainly[**P, R](builder: Cached[P, R], /, *args: P.args, **kwargs: P.kwargs) -> R:
    return Context().run(builder.build, *args, **kwargs)


# The build service puts its part cache here.
builds: Builds = plainly


def cached[**P, R](build: Callable[P, R]) -> Cached[P, R]:
    return Cached(build)
