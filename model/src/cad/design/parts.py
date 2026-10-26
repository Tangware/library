from collections.abc import Callable
from inspect import getsourcefile, signature

from cad.library.cache import Designed
from cad.library.shapes import Shaped


def part[**P, R: Shaped](build: Callable[P, R]) -> Designed[P, R]:
    def sourced(*args: P.args, **kwargs: P.kwargs) -> R:
        made = build(*args, **kwargs)
        made.source = str(getsourcefile(build))
        return made

    sourced.__module__ = build.__module__
    sourced.__name__ = build.__name__
    sourced.__qualname__ = build.__qualname__
    sourced.__signature__ = signature(build)  # type: ignore[attr-defined]
    return Designed(sourced)
