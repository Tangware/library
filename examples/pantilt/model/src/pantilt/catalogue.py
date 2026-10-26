from cad.design.catalogue import Item, Kind

JLC3DP = "JLC3DP"
JLC3DP_QUOTE = "https://jlc3dp.com/3d-printing-quote"
PRINTED = "FDM PAHT-CF, black"
STEPPER_PAGE = (
    "https://www.omc-stepperonline.com/"
    "nema-17-bipolar-1-8deg-16ncm-22-6oz-in-1a-3-7v-42x42x20mm-4-wires-17hs08-1004s"
)
STEPPER_USD = 6.67
PRINTING_PER_KG = 60.0
PRINTING = (
    "estimate: a print service's FDM rate of about 100 USD/kg for engineering nylon, less "
    "the filament; no quote, no page opened"
)
STEPPER_PRICE = f"{STEPPER_PAGE}, opened 2026-10-23: from $7.99, 'as low as $6.67' by volume"
ADAFRUIT_READ = "100+ tier, page read 2026-10-23"
ACCU = "Accu"
ACCU_SCREWS = "https://accu-components.com/us/metric-cap-head-screws"
ACCU_REFUSED = "estimate: ISO 4762 A2 in packs of 100; the Accu page refused the fetch (403)"
CNC_KITCHEN = "CNC Kitchen"
WERA = "https://products.wera.de/en/"


def printed(name: str) -> Item:
    return Item(
        name=name,
        kind=Kind.MADE,
        process=PRINTED,
        partner=JLC3DP,
        supplier=JLC3DP,
        url=JLC3DP_QUOTE,
        process_per_kg=PRINTING_PER_KG,
        price_source=PRINTING,
        stocked=True,
        moq=1,
        lead_weeks=None,
    )


def stepper(name: str) -> Item:
    return Item(
        name=name,
        kind=Kind.BOUGHT,
        supplier="StepperOnline",
        part_number="17HS08-1004S",
        url=STEPPER_PAGE,
        unit_price=STEPPER_USD,
        price_source=STEPPER_PRICE,
        stocked=True,
        moq=1,
        lead_weeks=None,
    )


def tool(name: str, url: str, price: float, why: str) -> Item:
    return Item(
        name=name,
        kind=Kind.TOOL,
        supplier=url,
        url=url,
        unit_price=price,
        price_source=f"estimate: {why}, not checked",
        stocked=True,
        moq=1,
        lead_weeks=None,
    )


CATALOGUE = (
    printed("base"),
    printed("lid"),
    printed("arm"),
    printed("cap"),
    printed("cradle"),
    printed("jaw"),
    stepper("pan motor, StepperOnline 17HS08-1004S"),
    stepper("tilt motor, StepperOnline 17HS08-1004S"),
    Item(
        name="Dupont jumper harness, 3 wires, 500 mm",
        kind=Kind.BOUGHT,
        supplier="AliExpress",
        url="https://www.aliexpress.com/w/wholesale-dupont-jumper-wire-500mm.html",
        unit_price=0.3,
        price_source="estimate: 3 of a 40-wire female-female 500 mm ribbon at about $3.50, "
        "not opened",
        stocked=True,
        moq=1,
        lead_weeks=None,
    ),
    Item(
        name="Dupont jumper harness, 2 wires, 150 mm",
        kind=Kind.BOUGHT,
        supplier="AliExpress",
        url="https://www.aliexpress.com/w/wholesale-dupont-jumper-wire-150mm.html",
        unit_price=0.1,
        price_source="estimate: 2 of a 40-wire female-female ribbon, not opened",
        stocked=True,
        moq=1,
        lead_weeks=None,
    ),
    Item(
        name="Adafruit 6121 TMC2209 driver",
        kind=Kind.BOUGHT,
        supplier="Adafruit",
        part_number="6121",
        url="https://www.adafruit.com/product/6121",
        unit_price=7.16,
        price_source=f"https://www.adafruit.com/product/6121, {ADAFRUIT_READ}",
        stocked=True,
        moq=1,
        lead_weeks=None,
    ),
    Item(
        name="Adafruit 4090 USB-C breakout",
        kind=Kind.BOUGHT,
        supplier="Adafruit",
        part_number="4090",
        url="https://www.adafruit.com/product/4090",
        unit_price=2.36,
        price_source=f"https://www.adafruit.com/product/4090, {ADAFRUIT_READ}",
        stocked=True,
        moq=1,
        lead_weeks=None,
    ),
    Item(
        name="Seeed XIAO ESP32S3 Sense",
        kind=Kind.BOUGHT,
        supplier="Seeed Studio",
        part_number="113991115",
        url="https://www.seeedstudio.com/XIAO-ESP32S3-Sense-p-5639.html",
        unit_price=13.90,
        price_source="https://www.seeedstudio.com/XIAO-ESP32S3-Sense-p-5639.html, "
        "single-unit price read 2026-10-23; no volume tier listed",
        stocked=True,
        moq=1,
        lead_weeks=None,
    ),
    Item(
        name="M3 x 6 socket head cap screw",
        kind=Kind.BOUGHT,
        supplier=ACCU,
        part_number="SSCF-M3-6-A2",
        url=ACCU_SCREWS,
        unit_price=0.06,
        price_source=ACCU_REFUSED,
        stocked=True,
        moq=100,
        lead_weeks=None,
    ),
    Item(
        name="M2 x 4 socket head cap screw",
        kind=Kind.BOUGHT,
        supplier=ACCU,
        part_number="SSCF-M2-4-A2",
        url=ACCU_SCREWS,
        unit_price=0.06,
        price_source=ACCU_REFUSED,
        stocked=True,
        moq=100,
        lead_weeks=None,
    ),
    Item(
        name="CNCKitchen M3 x 5.7 heat-set insert 4270002316409",
        kind=Kind.BOUGHT,
        supplier=CNC_KITCHEN,
        part_number="4270002316409",
        url="https://cnckitchen.store/products/heat-set-insert-m3-x-5-7-100-pieces",
        unit_price=0.12,
        price_source="estimate: a 100-piece pack at about 12 USD; "
        "the store refused the fetch (429)",
        stocked=True,
        moq=100,
        lead_weeks=None,
    ),
    Item(
        name="CNCKitchen M2 x 3 heat-set insert 4262391010013",
        kind=Kind.BOUGHT,
        supplier=CNC_KITCHEN,
        part_number="4262391010013",
        url="https://cnckitchen.store/products/heat-set-insert-m2-x-3-100-pieces",
        unit_price=0.10,
        price_source="estimate: a 100-piece pack at about 10 USD, not opened",
        stocked=True,
        moq=100,
        lead_weeks=None,
    ),
    Item(
        name="extension spring LE 031C 05 S",
        kind=Kind.BOUGHT,
        supplier="Lee Spring",
        part_number="LE 031C 05 S",
        url="https://www.leespring.com/extension-springs",
        unit_price=1.5,
        price_source="estimate: a stock stainless extension spring, not opened",
        stocked=True,
        moq=1,
        lead_weeks=None,
    ),
    Item(
        name="PAHT-CF, black, 1.75 mm",
        kind=Kind.CONSUMABLE,
        supplier="Bambu Lab",
        part_number="PAHT-CF 0.5 kg",
        url="https://us.store.bambulab.com/products/paht-cf",
        unit_price=40.0,
        kg=0.5,
        material="PAHT-CF black",
        colour=(0.14, 0.14, 0.15),
        price_source="estimate: a 0.5 kg spool, not opened",
        stocked=True,
        moq=1,
        lead_weeks=None,
    ),
    tool("2.5 mm hex key", WERA, 4.0, "a single L-key"),
    tool("1.5 mm hex key", WERA, 4.0, "a single L-key"),
    tool("soldering iron with an M3 insert tip", "https://cnckitchen.store/", 12.0, "a tip"),
    tool("soldering iron with an M2 insert tip", "https://cnckitchen.store/", 12.0, "a tip"),
)
