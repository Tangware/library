from cad.design.catalogue import IN_HOUSE, Item, Kind

from octopus.master import ARMS, CELLS, MOTOR_PAGE, RODS, SEGMENTS
from octopus.parts.arm import crank_name, drive_rod_name, rod_name, segment_name

ACCU = "Accu"
ACCU_SCREWS = "https://accu.co.uk/socket-cap-screws/"
ESTIMATE = "estimate: common hobby retail, page not opened"
DIGIKEY = "DigiKey"
DIGIKEY_READ = "1 unit, page opened 2026-11-02"
E91 = "https://www.digikey.com/en/products/detail/energizer-battery-company/E91/7400186"
HOOKUP_WIRE = "https://www.digikey.com/en/products/detail/alpha-wire/3049-RD005/266589"
SPOOLS = f"{DIGIKEY} A3049R-100-ND red and 3049 BK005 black, 100 ft spools, {DIGIKEY_READ}"
PRUSAMENT = "https://www.prusa3d.com/product/prusament-petg-{}-1kg-nfc/"
SPOOL = "estimate: Prusament PETG 1 kg spool list price, not checked"


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


def swatch(red: int, green: int, blue: int) -> tuple[float, float, float]:
    return (red / 255, green / 255, blue / 255)


def spool(colour: str, slug: str, rgb: tuple[float, float, float]) -> Item:
    return Item(
        name=f"Prusament PETG {colour}, 1.75 mm",
        kind=Kind.CONSUMABLE,
        supplier="Prusa Research",
        part_number=f"Prusament PETG {colour} 1 kg",
        url=PRUSAMENT.format(slug),
        unit_price=29.99,
        kg=1.0,
        material=f"PETG {colour}",
        colour=rgb,
        price_source=SPOOL,
        stocked=True,
        moq=1,
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
        "MPD BC4AAW 4-AA battery holder",
        DIGIKEY,
        "https://www.digikey.com/en/products/detail/mpd-memory-protection-devices/BC4AAW/66733",
        2.77,
        f"{DIGIKEY} BC4AAW-ND, {DIGIKEY_READ}",
    ),
    bought(
        "E-Switch RD11131121 rocker switch",
        DIGIKEY,
        "https://www.digikey.com/en/products/detail/e-switch/RD11131121/4029076",
        0.91,
        f"{DIGIKEY} EG5649-ND, {DIGIKEY_READ}",
    ),
    *(
        bought(
            f"Energizer E91 AA cell {k + 1}",
            DIGIKEY,
            E91,
            1.05,
            f"{DIGIKEY} E91-ND, {DIGIKEY_READ}; discontinued at {DIGIKEY}",
        )
        for k in range(CELLS)
    ),
    bought("arm 1 lead", DIGIKEY, HOOKUP_WIRE, 2 * 73.19, SPOOLS),
    *(
        bought(f"arm {arm + 1} lead", DIGIKEY, HOOKUP_WIRE, 0.0, "cut from the arm 1 lead's spools")
        for arm in ARMS[1:]
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
    spool("Carmine Red", "carmine-red", swatch(0xB5, 0x42, 0x2F)),  # filamentcolors 1659
    spool("Terracotta Light", "terracotta-light", swatch(0xB8, 0x7F, 0x69)),  # filamentcolors 1851
    spool("Anthracite Grey", "anthracite-grey", swatch(0x3F, 0x46, 0x46)),  # filamentcolors 1577
)
