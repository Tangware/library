---
stage: make
status: draft
---
# First article plan, order o1 (release v1)

One unit is built by the release's 12 build steps (the studio's build → `steps`) before any volume. Each check names where its number comes from.

| # | Check | Expected (source) | How |
|---|---|---|---|
| 1 | Fan sits flat on the head's two pads, cover clamps it with no rattle | no free play (model: fan seat, M3 × 30 through the fan's holes) | shake by hand, listen |
| 2 | Head turns ±45° without touching the puck or the button | clear at both ends (R2, `sweep` in the master) | turn by hand, then under firmware |
| 3 | Head's D-bore grips the 28BYJ-48 shaft | no slip at the sweep's reversal (model: D-bore at the datasheet's 3 mm flats) | mark shaft and hub, run 100 sweeps |
| 4 | Noise at 1 m, fan at full speed, sweeping | ≤ 25 dB(A) (R1) | phone SPL app is not enough; a class-2 meter in a quiet room |
| 5 | Current from a USB-C laptop port | ≤ 0.5 A (R3) | USB-C inline meter |
| 6 | No light visible in a dark room | none (R5) | look at the puck with the room lights off; white PETG may glow |
| 7 | Does not tip at full sweep with a 1 N push at the head's top | stays (R6 checks the weight only) | finger push gauge |
| 8 | 12 mm rod cannot touch the blades through either grille | blocked (R7 checks the front only) | Ø12 dowel |
| 9 | No screw seen from the front or top | none (S1) | look |
| 10 | Floor screws and inserts seat fully; USB-C plug enters without hitting the wall | flush (model: counterbore, USB keep-out) | plug three different cables |
| 11 | Printed sizes: head width, puck diameter, D-bore | head 124.4 mm, puck Ø124.4 mm (master) | calipers |
| 12 | Landed cost of this unit | < $35 (R8) | receipts against `ops/quotes/q1.toml` |

## Measurements
Not taken: no unit built.

## Verdict
None yet; needs the founder's signature.
