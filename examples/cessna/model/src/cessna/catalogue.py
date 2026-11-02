from cad.design.catalogue import IN_HOUSE, Item, Kind

from cessna.master import CELLS, MOTOR_PAGE

ACCU = "Accu"
ACCU_SCREWS = "https://accu.co.uk/socket-cap-screws/"
ESTIMATE = "estimate: common hobby retail, page not opened"
DIGIKEY = "DigiKey"
DIGIKEY_READ = "1 unit, page opened 2026-11-02"
EN91 = "https://www.digikey.com/en/products/detail/energizer-battery-company/EN91/704822"
HOOKUP_WIRE = "https://www.digikey.com/en/products/detail/alpha-wire/3049-RD005/266589"
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
            "stand",
            "main plate",
            "pivot bracket",
            "motor saddle",
            "output shaft",
            "rack",
            "motor pinion",
            *(
                f"{side} {name}"
                for side in ("left", "right")
                for name in (
                    "pillow block",
                    "tube hanger",
                    "shaft yoke",
                    "spider",
                    "side tube",
                    "spring leg",
                    "wheel",
                )
            ),
        )
    ),
    bought(
        "Pololu 3069 298:1 Micro Metal Gearmotor HPCB 6V",
        "Pololu",
        MOTOR_PAGE,
        26.45,
        f"{MOTOR_PAGE}/specs, 1 unit, read 2026-11-01",
    ),
    *(
        bought(f"M3 x {length} socket head cap screw", ACCU, ACCU_SCREWS, 0.08, ESTIMATE, 100)
        for length in (10, 16)
    ),
    *(
        bought(f"ISO 8734 dowel pin Ø3 x {length}", ACCU, ACCU_SCREWS, 0.2, ESTIMATE, 10)
        for length in (12, 14, 20)
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
            f"Energizer EN91 AA cell {k + 1}",
            DIGIKEY,
            EN91,
            0.6025,
            f"{DIGIKEY} N107-ND, the 4-unit price, page opened 2026-11-02",
        )
        for k in range(CELLS)
    ),
    bought(
        "switch leads",
        DIGIKEY,
        HOOKUP_WIRE,
        2 * 73.19,
        f"{DIGIKEY} A3049R-100-ND red and 3049 BK005 black, 100 ft spools, {DIGIKEY_READ}",
    ),
    bought(
        "TE Raychem RNF-100-3/32-BK heat-shrink sleeve",
        DIGIKEY,
        "https://www.digikey.com/en/products/detail/te-connectivity-raychem-cable-protection/RNF-100-3-32-BK-STK/573411",
        2.37,
        f"{DIGIKEY} RNF332K-ND, a 4 ft stick, page opened 2026-11-02",
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
    spool("Anthracite Grey", "anthracite-grey", swatch(0x3F, 0x46, 0x46)),  # filamentcolors 1577
    spool("Signal White", "signal-white", swatch(0xE5, 0xE0, 0xE1)),  # filamentcolors 1338
    spool("Jet Black", "jet-black", swatch(0x29, 0x2B, 0x2B)),  # filamentcolors 509
)
