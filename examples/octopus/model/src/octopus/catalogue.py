from cad.design.catalogue import IN_HOUSE, Item, Kind

from octopus.master import ARMS, MOTOR_PAGE, RODS, SEGMENTS
from octopus.parts.arm import crank_name, drive_rod_name, rod_name, segment_name

ACCU = "Accu"
ACCU_SCREWS = "https://accu.co.uk/socket-cap-screws/"
ESTIMATE = "estimate: common hobby retail, page not opened"


def printed(name: str) -> Item:
    return Item(
        name=name,
        kind=Kind.MADE,
        process="FDM PETG",
        partner=IN_HOUSE,
        supplier=IN_HOUSE,
        price_source="in-house printing, priced by the build",
        stocked=True,
        moq=1,
    )


def bought(name: str, supplier: str, url: str, price: float, source: str, pack: int = 1) -> Item:
    return Item(
        name=name,
        kind=Kind.BOUGHT,
        supplier=supplier,
        url=url,
        unit_price=price,
        price_source=source,
        stocked=True,
        moq=pack,
        pack=pack,
    )


def tool(name: str, supplier: str, url: str, price: float) -> Item:
    return Item(
        name=name,
        kind=Kind.TOOL,
        supplier=supplier,
        url=url,
        unit_price=price,
        price_source=ESTIMATE,
        stocked=True,
        moq=1,
    )


CATALOGUE = (
    *(
        printed(name)
        for name in (
            "body",
            "mantle",
            "motor cap",
            *(crank_name(arm) for arm in ARMS),
            *(drive_rod_name(arm) for arm in ARMS),
            *(segment_name(arm, k) for arm in ARMS for k in SEGMENTS),
            *(rod_name(arm, k) for arm in ARMS for k in RODS),
        )
    ),
    *(
        bought(
            f"Pololu 3069 298:1 Micro Metal Gearmotor HPCB 6V {arm + 1}",
            "Pololu",
            MOTOR_PAGE,
            26.45,
            f"{MOTOR_PAGE}/specs, 1 unit, read 2026-11-01",
        )
        for arm in ARMS
    ),
    *(
        bought(f"M3 x {length} socket head cap screw", ACCU, ACCU_SCREWS, 0.08, ESTIMATE, 100)
        for length in (10,)
    ),
    bought(
        "Pololu 1159 4-AA battery holder with switch",
        "Pololu",
        "https://www.pololu.com/product/1159",
        3.0,
        ESTIMATE,
    ),
    bought(
        "CNCKitchen M3 x 5.7 heat-set insert 4270002316409",
        "CNC Kitchen",
        "https://cnckitchen.store/products/heat-set-insert-m3-x-5-7-100-pieces",
        0.12,
        "estimate: a 100-piece pack at about 12 USD, not checked",
        100,
    ),
    tool("2.5 mm hex key", "Wera", "https://products.wera.de/en/", 4.0),
    tool("soldering iron with an M3 insert tip", "CNC Kitchen", "https://cnckitchen.store/", 12.0),
    Item(
        name="PETG, white, 1.75 mm",
        kind=Kind.CONSUMABLE,
        supplier="Prusa Research",
        url="https://www.prusa3d.com/product/prusament-petg-signal-white-1kg/",
        unit_price=29.99,
        kg=1.0,
        material="PETG white",
        price_source="estimate: Prusament PETG 1 kg spool list price, not checked",
        stocked=True,
        moq=1,
    ),
)
