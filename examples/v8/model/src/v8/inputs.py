from v8.master import CYLINDERS, V8Master


def bank_path(deg: float) -> list[str]:
    return ["valvetrain", f"bank {deg:g}"]


def inputs(_: V8Master) -> dict[str, object]:
    banks = sorted({each.bank_deg for each in CYLINDERS})
    return {
        "explode": {
            "blocks": [
                [],
                *(bank_path(deg) for deg in banks),
                *([*bank_path(each.bank_deg), f"{each.name} valves"] for each in CYLINDERS),
            ]
        }
    }
