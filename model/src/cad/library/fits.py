from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Metal:
    name: str
    yield_mpa: float
    modulus_mpa: float
    poisson: float
    source: str


STAINLESS_A2_70 = Metal(
    name="A2-70",
    yield_mpa=450.0,
    modulus_mpa=193000.0,
    poisson=0.29,
    source="ISO 3506-1, A2-70, Rm at least 700 MPa, Rp0.2 at least 450 MPa",
)
STEEL_4_6 = Metal(
    name="4.6",
    yield_mpa=240.0,
    modulus_mpa=210000.0,
    poisson=0.3,
    source="ISO 898-1, property class 4.6, the lowest class, ReL at least 240 MPa",
)
STEEL_4_8 = Metal(
    name="4.8",
    yield_mpa=340.0,
    modulus_mpa=210000.0,
    poisson=0.3,
    source="ISO 898-1, property class 4.8, ReL at least 340 MPa",
)
STEEL_8_8 = Metal(
    name="8.8",
    yield_mpa=640.0,
    modulus_mpa=210000.0,
    poisson=0.3,
    source="ISO 898-1, property class 8.8 up to M16, Rp0.2 at least 640 MPa",
)
STEEL_12_9 = Metal(
    name="12.9",
    yield_mpa=1100.0,
    modulus_mpa=210000.0,
    poisson=0.3,
    source="ISO 898-1, property class 12.9, Rp0.2 at least 1100 MPa",
)
PIN_DOUBLE_SHEAR_N = {3.0: 6320.0, 5.0: 17540.0, 6.0: 26040.0}  # ISO 8752 minimum double shear
ALUMINIUM_6063_T6 = Metal(
    name="6063 T6",
    yield_mpa=170.0,
    modulus_mpa=69000.0,
    poisson=0.33,
    source="EN 755-2, 6063 T6 tube up to 10 mm wall, Rp0.2 at least 170 MPa",
)
ALUMINIUM_6061_T6 = Metal(
    name="6061 T6",
    yield_mpa=240.0,
    modulus_mpa=69000.0,
    poisson=0.33,
    source="EN 755-2, 6061 T6 bars up to 200 mm, Rp0.2 at least 240 MPa",
)
BRASS = Metal(
    name="CW614N",
    yield_mpa=160.0,
    modulus_mpa=97000.0,
    poisson=0.34,
    source=(
        "https://www.totalmateria.com/en-us/material/3041238, "
        "EN 12164 CW614N R400, Rp0.2 160 MPa, E 97 GPa"
    ),
)


@dataclass(frozen=True, kw_only=True)
class Filament:
    plastic: str
    in_layer_mpa: float
    across_layers_mpa: float
    modulus_mpa: float
    poisson: float
    density_kg_m3: float
    long_term_share: float
    fatigue_share: float
    source: str

    def allowable(self, *, across_layers: bool, constant: bool) -> float:
        strength = self.across_layers_mpa if across_layers else self.in_layer_mpa
        if constant:
            return strength * self.long_term_share
        return strength * self.fatigue_share


PETG = Filament(
    plastic="PETG",
    in_layer_mpa=47.0,
    across_layers_mpa=18.0,
    modulus_mpa=1500.0,
    poisson=0.37,
    density_kg_m3=1270.0,
    long_term_share=0.30,
    fatigue_share=0.30,
    source=(
        "Prusament PETG TDS v1.1: ISO 527-1 strength and modulus, interlayer adhesion; "
        "Ultimaker PETG TDS v1.00; density from the Prusament listing, filament2print.com; "
        "Poisson Wikło et al. 2025, doi 10.3390/ma18051086; long-term share from PETG creep, "
        "doi 10.3390/polym17152075 and 10.3390/polym13234132; fatigue share Martins et al. "
        "2024, doi 10.3390/polym16131868"
    ),
)
PAHT_CF = Filament(
    plastic="PAHT-CF",
    in_layer_mpa=88.0,
    across_layers_mpa=64.0,
    modulus_mpa=3860.0,
    poisson=0.40,
    density_kg_m3=1060.0,
    long_term_share=0.30,
    fatigue_share=0.30,
    source=(
        "Bambu PAHT-CF TDS V2.0, ISO 527 dry and annealed: X-Y and Z tensile strength, X-Y "
        "modulus, ISO 1183 density; Poisson of printed short-carbon-fibre nylon, Onyx parallel, "
        "doi 10.3390/polym15071708; no creep or fatigue share is published for printed "
        "CF-nylon, so both shares are PETG's"
    ),
)
FILAMENTS = {filament.plastic: filament for filament in (PETG, PAHT_CF)}
METALS = {"steel": STEEL_4_6, "stainless": STAINLESS_A2_70, "aluminium": ALUMINIUM_6063_T6}
NUT_PROOF_MPA = 700.0  # ISO 3506-2:2020, property class 70, style 1


@dataclass(frozen=True, kw_only=True)
class Fits:
    sliding: float
    bearing_seat: float
    bearing_proud: float
    snap: float
    membrane: float
    min_wall: float
    structural_wall: float
    overhang_deg: float
    printed_hole: float
    press: float
    clearance_fit: Literal["Close", "Normal", "Loose"]
    plastic_pilot: float
    plastic_thread: float
    insert_pull_out_n: dict[float, float]
    spring_force_share: float

    def printed(self, hole: float) -> float:
        return hole + self.printed_hole

    def pressed(self, pin: float) -> float:
        return self.printed(pin) - self.press


FITS_UNITS = {
    "sliding": "mm",
    "bearing_seat": "mm",
    "bearing_proud": "mm",
    "snap": "mm",
    "membrane": "mm",
    "min_wall": "mm",
    "structural_wall": "mm",
    "overhang_deg": "deg",
    "printed_hole": "mm",
    "press": "mm",
    "clearance_fit": "-",
    "plastic_pilot": "x screw diameter",
    "plastic_thread": "x screw diameter",
    "insert_pull_out_n": "N by screw diameter in mm",
    "spring_force_share": "-",
}
