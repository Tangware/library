from cad.cables.models import Cable, Discrete, Plug, Route, RoutePoint, ServiceLoop, Wire
from cad.library.bought.catalogue import NO_BILL, Bill
from cad.library.mates import Connector

from pantilt.master import ProductMaster
from pantilt.models import stepper

DUPONT_WIRE_MM = 1.4
SIGNALS = ("5V", "GND", "UART")
PAN_DRIVER = SIGNALS
TILT_DRIVER = SIGNALS
POWER = ("VBUS", "GND")
COILS = ("A+", "A-", "B+", "B-")
SIGNAL_HARNESS = "Dupont jumper harness, 3 wires, 500 mm"
POWER_HARNESS = "Dupont jumper harness, 2 wires, 150 mm"
PAN_MOTOR = "pan motor, StepperOnline 17HS08-1004S"
TILT_MOTOR = "tilt motor, StepperOnline 17HS08-1004S"
CAMERA = "Seeed XIAO ESP32S3 Sense"
USB_C = "Adafruit 4090 USB-C breakout"
PAN_DRIVER_KEY = "Adafruit 6121 TMC2209 driver #1"
TILT_DRIVER_KEY = "Adafruit 6121 TMC2209 driver #2"
LEAD = "motor lead"
HEADER = "driver header"
TERMINAL = "driver terminal"
PINS = "USB-C pins"
CAMERA_PINS = "camera pins"


def wires(names: tuple[str, ...], diameter: float) -> tuple[Wire, ...]:
    return tuple(Wire(name=name, diameter=diameter, colour=name) for name in names)


def cable(name: str, plugs: tuple[tuple[str, tuple[str, ...]], ...], length: float) -> Cable:
    named = tuple(dict.fromkeys(wire for _, pinout in plugs for wire in pinout))
    return Cable(
        name=name,
        wires=wires(named, DUPONT_WIRE_MM),
        plugs=tuple(Plug(name=plug, model=None, pinout=pinout) for plug, pinout in plugs),
        construction=Discrete(),
        twist_rating=0.0,
        length=length,
        bill=NO_BILL,
    )


SIGNAL_CABLE = cable(
    SIGNAL_HARNESS,
    (("XIAO", SIGNALS), ("pan driver", PAN_DRIVER), ("tilt driver", TILT_DRIVER)),
    500.0,
)
POWER_CABLE = cable(
    POWER_HARNESS, (("USB-C", POWER), ("pan driver", POWER), ("tilt driver", POWER)), 150.0
)


def lead(motor: str) -> Cable:
    return Cable(
        name=f"{motor} lead",
        wires=wires(COILS, stepper.LEAD_WIRE_MM),
        plugs=(
            Plug(name="motor", model=None, pinout=COILS),
            Plug(name="driver", model=None, pinout=COILS),
        ),
        construction=Discrete(),
        twist_rating=0.0,
        length=stepper.LEAD_LENGTH,
        bill=Bill(ships_with=motor),
    )


def harness(m: ProductMaster) -> list[Route]:
    at = m.cable_points

    def point(part: str, name: str) -> RoutePoint:
        return RoutePoint(part=part, at=at[name])

    down_the_arm = (
        point("arm", "behind the column"),
        point("arm", "behind the leg"),
        point("arm", "over the arm's cable hole"),
        point("arm", "under the arm's cable hole"),
        point("arm", "on the arm's clip"),
        ServiceLoop(length=m.pan_loop),
        point("lid", "on the lid's clip"),
        point("lid", "over the lid's hole"),
        point("base", "under the lid"),
        point("base", "in the cable bay"),
    )
    from_the_camera = (
        point("cradle", "behind the cradle"),
        point("cradle", "behind the tilt hub"),
        ServiceLoop(length=m.tilt_loop),
        *down_the_arm,
    )
    return [
        Route(
            cable=lead(PAN_MOTOR),
            plugged=(Connector(PAN_MOTOR, LEAD), Connector(PAN_DRIVER_KEY, TERMINAL)),
            through=((),),
        ),
        Route(
            cable=lead(TILT_MOTOR),
            plugged=(Connector(TILT_MOTOR, LEAD), Connector(TILT_DRIVER_KEY, TERMINAL)),
            through=((point("arm", "behind the drum"), *down_the_arm),),
        ),
        Route(
            cable=SIGNAL_CABLE,
            plugged=(
                Connector(CAMERA, CAMERA_PINS),
                Connector(PAN_DRIVER_KEY, HEADER),
                Connector(TILT_DRIVER_KEY, HEADER),
            ),
            through=(from_the_camera, from_the_camera),
        ),
        Route(
            cable=POWER_CABLE,
            plugged=(
                Connector(USB_C, PINS),
                Connector(PAN_DRIVER_KEY, HEADER),
                Connector(TILT_DRIVER_KEY, HEADER),
            ),
            through=((), ()),
        ),
    ]
