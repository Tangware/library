from cad.design.catalogue import Item, Kind

DIGIKEY = "Digi-Key"
ADAFRUIT = "Adafruit"
CNC_KITCHEN = "CNC Kitchen"
ACCU = "Accu"
JLC3DP = "JLC3DP"
JLC3DP_QUOTE = "https://jlc3dp.com/3d-printing-quote"
PRINTING_PER_KG = 40.0
PRINTING = (
    "estimate: a print service's PETG rate of about 70 USD/kg (University of Waterloo RPC,"
    " search summary, not opened), less the filament; JLC3DP quotes only after an upload"
)
CHF_USD = 1.25  # estimate: exchange rate, not checked on the day
SPOOL_CHF = 33.50  # 3djake.ch, Prusament PETG Matte Noctua Brown 1 kg, search summary
WIRE = "estimate: 26 AWG stranded hookup wire cut from a reel, under 0.5 m a lead, not quoted"
EUR_USD = 1.16  # estimate: exchange rate, not checked on the day
GBP_USD = 1.33  # estimate: exchange rate, not checked on the day
INSERT_M3_EUR = 84.60 / 1000  # cnckitchen.store, M3 x 5.7, EUR per 1,000 pack
INSERT_SMALL_EUR = 89.90 / 1000  # cnckitchen.store, M2 x 3 and M2.5 x 4, EUR per 1,000 pack
SCREW_GBP = 0.04  # accu.co.uk, A2 ISO 4762 M3 and M2, at 1,000
SCREW_M2_5_GBP = 0.03  # accu.co.uk, A2 ISO 4762 M2.5 x 5 (3803), at 2,000


def made(name: str) -> Item:
    return Item(
        name=name,
        kind=Kind.MADE,
        process="FDM PETG",
        partner=JLC3DP,
        supplier=JLC3DP,
        url=JLC3DP_QUOTE,
        process_per_kg=PRINTING_PER_KG,
        price_source=PRINTING,
        stocked=True,
        moq=1,
        lead_weeks=None,
    )


def insert(name: str, part_number: str, url: str, eur: float) -> Item:
    return Item(
        name=name,
        kind=Kind.BOUGHT,
        supplier=CNC_KITCHEN,
        part_number=part_number,
        url=url,
        unit_price=eur * EUR_USD,
        price_source=f"{url}: {eur * 1000:.2f} EUR per 1,000 (page opened), converted at an"
        " estimated rate",
        stocked=True,
        moq=100,
        lead_weeks=None,
    )


def screw(name: str, part_number: str, gbp: float) -> Item:
    url = "https://www.accu.co.uk/metric-cap-head-screws/"
    return Item(
        name=name,
        kind=Kind.BOUGHT,
        supplier=ACCU,
        part_number=part_number,
        url=url,
        unit_price=gbp * GBP_USD,
        price_source=f"{url}: {gbp:.2f} GBP each at 1,000 for this series (agent opened the"
        " M3 x 8, M2 x 4 and M2.5 x 5 pages; this length's page not opened), converted at an"
        " estimated rate",
        stocked=True,
        moq=1,
        lead_weeks=None,
    )


def lead(name: str, price: float, source: str = WIRE) -> Item:
    return Item(
        name=name,
        kind=Kind.BOUGHT,
        supplier=DIGIKEY,
        url="https://www.digikey.com/en/products/filter/hook-up-wire/468",
        unit_price=price,
        price_source=source,
        stocked=True,
        moq=1,
        lead_weeks=None,
    )


def tool(name: str, supplier: str, url: str, price: float) -> Item:
    return Item(
        name=name,
        kind=Kind.TOOL,
        supplier=supplier,
        url=url,
        unit_price=price,
        price_source="estimate: one tool for the build bench, not checked",
        stocked=True,
        moq=1,
        lead_weeks=None,
    )


CATALOGUE = (
    *(made(name) for name in ("base", "plate", "carousel", "lid", "drawer")),
    Item(
        name="Prusament PETG Matte Noctua Brown, 1.75 mm",
        kind=Kind.CONSUMABLE,
        supplier="Prusa Research",
        part_number="Prusament PETG Matte Noctua Brown (NFC), 1 kg",
        url="https://www.3djake.ch/en-CH/prusa/prusament-petg-matte-noctua-brown-nfc",
        unit_price=SPOOL_CHF * CHF_USD,
        kg=1.0,
        material="PETG brown",
        colour=(0.45, 0.33, 0.25),
        price_source="3djake.ch 33.50 CHF per kg (search summary, page not opened), converted"
        " at an estimated rate; the colour is an estimate of the spool's brown",
        stocked=True,
        moq=1,
        lead_weeks=None,
    ),
    Item(
        name="Raspberry Pi Pico 2 W",
        kind=Kind.BOUGHT,
        supplier=DIGIKEY,
        part_number="2648-SC1633TR-ND (Raspberry Pi SC1633)",
        url="https://www.digikey.com/en/products/detail/raspberry-pi/SC1633/25862726",
        unit_price=7.00,
        price_source="Digi-Key, 7.00 USD at 1,200 on tape and reel (8.42 at 1), page opened",
        stocked=True,
        moq=1,
        lead_weeks=18,
    ),
    Item(
        name="Adafruit 3297 DRV8833 breakout",
        kind=Kind.BOUGHT,
        supplier=ADAFRUIT,
        part_number="3297 (Digi-Key 1528-3297-ND)",
        url="https://www.adafruit.com/product/3297",
        unit_price=4.76,
        price_source="https://www.adafruit.com/product/3297: 4.76 USD at 100+, page opened",
        stocked=True,
        moq=1,
        lead_weeks=4,
    ),
    Item(
        name="Adafruit 858 28BYJ-48 stepper",
        kind=Kind.BOUGHT,
        supplier=ADAFRUIT,
        part_number="858 (Digi-Key 1528-1366-ND)",
        url="https://www.adafruit.com/product/858",
        unit_price=3.96,
        price_source="https://www.adafruit.com/product/858: 3.96 USD at 100+, page opened",
        stocked=True,
        moq=1,
        lead_weeks=4,
    ),
    Item(
        name="Soberton WST-1205S buzzer",
        kind=Kind.BOUGHT,
        supplier=DIGIKEY,
        part_number="433-1029-ND",
        url="https://www.digikey.com/en/products/detail/soberton-inc/WST-1205S/479675",
        unit_price=0.90329,
        price_source="Digi-Key 433-1029-ND, 0.90329 USD at 1,000, page opened",
        stocked=True,
        moq=1,
        lead_weeks=9,
    ),
    Item(
        name="Littelfuse 59140-1-S-02-A reed sensor",
        kind=Kind.BOUGHT,
        supplier=DIGIKEY,
        part_number="HE573-ND",
        url="https://www.digikey.com/en/products/result?keywords=HE573-ND",
        unit_price=2.51436,
        price_source="Digi-Key HE573-ND, 2.51436 USD at 1,000, page opened",
        stocked=True,
        moq=1,
        lead_weeks=16,
    ),
    Item(
        name="Littelfuse 57140-000 actuator",
        kind=Kind.BOUGHT,
        supplier=DIGIKEY,
        part_number="57140-000-ND",
        url="https://www.digikey.com/en/products/result?keywords=57140-000-ND",
        unit_price=1.36835,
        price_source="Digi-Key 57140-000-ND, 1.36835 USD at 1,080, page opened",
        stocked=True,
        moq=1,
        lead_weeks=19,
    ),
    Item(
        name="Kingbright WP7113ID5V LED",
        kind=Kind.BOUGHT,
        supplier=DIGIKEY,
        part_number="754-1732-ND",
        url="https://www.digikey.com/en/products/result?keywords=754-1732-ND",
        unit_price=0.22659,
        price_source="Digi-Key 754-1732-ND, 0.22659 USD at 1,000, page opened",
        stocked=True,
        moq=1,
        lead_weeks=6,
    ),
    Item(
        name="Raspberry Pi SC0623 12.5 W micro-USB power supply",
        kind=Kind.BOUGHT,
        supplier=DIGIKEY,
        part_number="2648-SC0623-ND",
        url="https://www.digikey.com/en/products/result?keywords=2648-SC0623-ND",
        unit_price=8.00,
        price_source="Digi-Key 2648-SC0623-ND, 8.00 USD, only break listed, page opened",
        stocked=True,
        moq=1,
        lead_weeks=30,
    ),
    Item(
        name="3M Bumpon SJ5302",
        kind=Kind.BOUGHT,
        supplier=DIGIKEY,
        part_number="SJ5302-7-ND",
        url="https://www.digikey.com/en/products/result?keywords=SJ5302-7-ND",
        unit_price=0.10516,
        price_source="Digi-Key SJ5302-7-ND, 0.10516 USD at 1,008, page opened",
        stocked=True,
        moq=144,
        lead_weeks=4,
    ),
    insert(
        "CNCKitchen M3 x 5.7 heat-set insert 4270002316409",
        "4270002316409",
        "https://cnckitchen.store/",
        INSERT_M3_EUR,
    ),
    insert(
        "CNCKitchen M2 x 3 heat-set insert 4262391010013",
        "4262391010013",
        "https://cnckitchen.store/",
        INSERT_SMALL_EUR,
    ),
    insert(
        "CNCKitchen M2.5 x 4 heat-set insert 4262391011980",
        "4262391011980",
        "https://cnckitchen.store/",
        INSERT_SMALL_EUR,
    ),
    screw("M3 x 6 socket head cap screw", "Accu SSCF-M3-6-A2", SCREW_GBP),
    screw("M3 x 10 socket head cap screw", "Accu 3819-SSCF-M3-10-A2", SCREW_GBP),
    screw("M2 x 3 socket head cap screw", "Accu SSCF-M2-3-A2", SCREW_GBP),
    screw("M2.5 x 5 socket head cap screw", "Accu 3803-SSCF-M2.5-5-A2", SCREW_M2_5_GBP),
    lead("driver leads, 26 AWG", 0.15),
    lead("light leads, 26 AWG", 0.05),
    lead(
        "buzzer leads, 26 AWG, with its 2N3904 switch",
        0.12,
        "estimate: two short 26 AWG leads, an onsemi 2N3904 and a 1 kΩ resistor in heat-shrink,"
        " not quoted",
    ),
    tool("soldering iron with an M3 insert tip", CNC_KITCHEN, "https://cnckitchen.store/", 12.0),
    tool("soldering iron with an M2 insert tip", CNC_KITCHEN, "https://cnckitchen.store/", 12.0),
    tool("soldering iron with an M2.5 insert tip", CNC_KITCHEN, "https://cnckitchen.store/", 12.0),
    tool("2.5 mm hex key", "Wera", "https://products.wera.de/en/", 4.0),
    tool("2 mm hex key", "Wera", "https://products.wera.de/en/", 4.0),
    tool("1.5 mm hex key", "Wera", "https://products.wera.de/en/", 4.0),
)
