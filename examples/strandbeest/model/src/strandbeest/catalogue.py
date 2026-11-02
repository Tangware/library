from cad.design.catalogue import IN_HOUSE, Item, Kind

from strandbeest.master import MASTER, MOTOR_PAGE

ACCU = "Accu"
ACCU_SCREWS = "https://accu.co.uk/socket-cap-screws/"
POLOLU_HOLDER = "https://www.pololu.com/product/1159"
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


CATALOGUE = (
    *(
        printed(name)
        for name in (
            "upper link",
            "lower link",
            "rocker",
            "coupler",
            "triangle",
            "foot",
            "left plate",
            "right plate",
            "deck",
            "sail",
            "motor cap",
            *(piece.name for piece in MASTER.crank_pieces),
        )
    ),
    bought(
        "Pololu 3069 298:1 Micro Metal Gearmotor HPCB 6V",
        "Pololu",
        MOTOR_PAGE,
        26.45,
        f"{MOTOR_PAGE}/specs, 1 unit, read 2026-11-01",
    ),
    bought(
        "Pololu 1159 4-AA battery holder with switch",
        "Pololu",
        POLOLU_HOLDER,
        4.34,
        f"{POLOLU_HOLDER}, 1 unit, read 2026-11-01",
    ),
    *(
        bought(f"M3 x {length} socket head cap screw", ACCU, ACCU_SCREWS, 0.08, ESTIMATE, 100)
        for length in (8, 16, 20)
    ),
    bought(
        f"aluminium tube Ø6 x 1, cut to {MASTER.tube_length:.0f} mm",
        "Hobby metals retailer",
        ACCU_SCREWS,
        3.0,
        ESTIMATE,
    ),
    bought(
        f"DIN 976-1 M4 A2-70 threaded rod, cut to {MASTER.rod_length:.0f}",
        ACCU,
        ACCU_SCREWS,
        3.0,
        ESTIMATE,
    ),
    bought("M3 DIN 985 nylon-insert lock nut", ACCU, ACCU_SCREWS, 0.06, ESTIMATE, 100),
    bought("M4 hex nut", ACCU, ACCU_SCREWS, 0.05, ESTIMATE, 100),
    bought(
        "CNCKitchen M3 x 5.7 heat-set insert 4270002316409",
        "CNC Kitchen",
        "https://cnckitchen.store/products/heat-set-insert-m3-x-5-7-100-pieces",
        0.12,
        "estimate: a 100-piece pack at about 12 USD, not checked",
        100,
    ),
    Item(
        name="2.5 mm hex key",
        kind=Kind.TOOL,
        supplier="Wera",
        url="https://products.wera.de/en/",
        unit_price=4.0,
        price_source=ESTIMATE,
        stocked=True,
        moq=1,
    ),
    Item(
        name="soldering iron with an M3 insert tip",
        kind=Kind.TOOL,
        supplier="CNC Kitchen",
        url="https://cnckitchen.store/",
        unit_price=12.0,
        price_source=ESTIMATE,
        stocked=True,
        moq=1,
    ),
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
