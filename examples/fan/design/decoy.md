---
stage: define
status: draft
---
# Decoy

Written by a fresh agent given only `README.md` and the core references, told to aim at the brief's weakest point.

## Halo Breeze (the decoy, verbatim summary)
A short matte-white powder-coated aluminium cylinder with a soft-touch silicone ring around the waist, about 28 cm tall, on a weighted round base. Fine-perforated metal mesh front over 200 mm blades. A slim warm-white light ring under the rim glows while it runs. Flat brushed-aluminium touch pad on top with a 4-step swipe slider. USB-C out of the back; a small Phillips screw plate on the back holds the guard. Sweeps about 70°, one pass in about 20 s, driven by a visible slim pivot column. About 26 dB on low. Around 89 EUR. Optional companion app for schedules and a timer.
Aimed at: "P2, S1 and P4 are wide, so a soft warm ring, a mesh face, a slider and an app timer all sound tasteful while breaking all three."

## Run against the brief
| Decoy feature | Rule | Verdict |
|---|---|---|
| warm-white light ring | R5 (no light of any colour), P2 (forbids any light seen from outside) | killed |
| touch slider | R4, P4 (forbids a touch strip, a second control) | killed |
| optional companion app | R4 (refuses ▸ "an app"), P4 (forbids any radio) | killed |
| 26 dB on its *lowest* setting | R1 (loudest setting ≤ 25 dB(A)) | killed |
| aluminium + silicone ring + brushed top | formal: uniform materials (forbids a second material on the shell), matte (forbids brushed sheen) | killed |
| Phillips screw plate on the back | S1, P5 allow the back | survives, as intended: the founder refused screws on the front only |
| perforated mesh face | P1 forbids a wire cage; a mesh is not one | survives; acceptable — R7 governs it |
| 28 cm tall, weighted base, 200 mm head | **no rule** reached the size of the object on a small desk | survived the first run |

## Sharpened and re-run
The decoy found one real gap: nothing in the brief tied the object to ▸ "small desks". Added S4 to `prd.md`: nothing stands wider than the head, so the fan takes no more desk than its own face. Re-run: the decoy's base is "weighted", width not stated; under S4 a base wider than its 200 mm head is forbidden, and the 200 mm head itself fails R8's cost (no stocked 5 V 200 mm fan, see `design/rejected.md`). The decoy is killed by R1, R4, R5, P2, P4 and the formal material positions; S4 now closes the size gap.
