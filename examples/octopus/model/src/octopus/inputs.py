from octopus.master import ARMS, OctopusMaster


def inputs(_: OctopusMaster) -> dict[str, object]:
    return {"explode": {"blocks": [[], *([f"arm {arm + 1}"] for arm in ARMS)]}}
