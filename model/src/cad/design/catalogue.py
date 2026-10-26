from dataclasses import dataclass
from enum import StrEnum

IN_HOUSE = "in house"


class Kind(StrEnum):
    MADE = "made"
    BOUGHT = "bought"
    CONSUMABLE = "consumable"
    TOOL = "tool"


@dataclass(frozen=True, kw_only=True)
class Item:
    name: str
    kind: Kind
    price_source: str
    stocked: bool | None = None
    moq: int | None = None
    lead_weeks: float | None = None
    pack: int = 1
    unit_price: float | None = None
    kg: float | None = None
    material: str = ""
    colour: tuple[float, float, float] | None = None
    process_per_kg: float | None = None
    currency: str = "USD"
    supplier: str = ""
    part_number: str = ""
    url: str = ""
    process: str = ""
    partner: str = ""

    def __post_init__(self) -> None:
        if self.kind is Kind.MADE and self.unit_price is not None:
            raise ValueError(f"{self.name}: a made part is priced by its material")

    def per_kg(self) -> float:
        if self.unit_price is None or self.kg is None:
            raise ValueError(f"{self.name} gives no price per kg")
        return self.unit_price / self.kg
