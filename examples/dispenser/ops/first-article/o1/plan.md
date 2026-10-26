---
stage: make
status: draft
---
# First article plan, order o1 (release v1)

One unit built from the `v1` build steps (the studio's build → steps), before any volume. Each check names its source.

## Build
Follow the 17 steps of the release. The build has no step for the wiring (cables are routed but not stepped): solder the leads to the Pico 2 W before step 7 (Pico and driver fitted), with the buzzer's 2N3904 and 1 kΩ in heat-shrink on its lead.

## Dimensions and fits
| Check | Expected | Source |
|---|---|---|
| Drum diameter, base and lid | equal, 238.4 mm | master `radius`; S2 |
| Lid lifts off by hand, sits back without aligning | no tool, no latch | R3, P5 |
| Carousel turns free on the shaft, no rub on the floor | 0.2 mm running gap | fit table `sliding` |
| D-bore grips the shaft flats without play | press allowance | fit table `press` |
| Drawer slides out and back without catching | sliding fit both sides | master `guide_x` |
| A 20 mm fingertip reaches the outer end of every pocket | fits | R3 test probe |
| A large hand's fingers fit under the drawer lip | 100 mm wide, 8 mm high | R7 |
| LED dome flush with the drum front | flush | S3 |
| Power plug enters the back opening fully | plug seats | keep-out `usb_keepout` |

## Requirements
| Check | Pass | Source |
|---|---|---|
| Rest: no pill reaches the drawer with the carousel at home | none in 20 shakes | R1 |
| One step of 1/29 turn drops exactly one pocket | the pocket's pills only | R1 |
| A full carousel (28 doses of 8 real tablets) turns every step | 29 steps, no stall | R9 |
| Alert heard across a kitchen | founder's father hears it from the next room | R4 (measure dB at 1 m, record) |
| Drawer open/close seen by the reed sensor | every time in 50 pulls | R5 |
| Missed dose reaches the child's phone | within the firmware's window | R6 |
| Landed cost from the real invoices | under 60 USD | R8 |

## Measurements, photos, verdict
Not started: no order has been placed.
