from dataclasses import dataclass


@dataclass(frozen=True)
class Why:
    decision: str
    reason: str
    requirements: tuple[int, ...] = ()
    sources: tuple[str, ...] = ()
