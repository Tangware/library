from collections.abc import Callable
from contextvars import Context
from functools import wraps


class Skeleton:
    pass


class Derived[**P, R]:
    def __init__(self, build: Callable[P, R]) -> None:
        self.build = build
        wraps(build)(self)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return Context().run(self.build, *args, **kwargs)


class Designed[**P, R](Derived[P, R]):
    pass


def derived[**P, R](build: Callable[P, R]) -> Derived[P, R]:
    return Derived(build)
