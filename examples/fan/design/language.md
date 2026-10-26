---
stage: design
status: draft
---
# Language

Direction: Head and puck (`design/directions/head-and-puck.md`).

## Decision study
| Decision | Precedent interrogated | Rule (with teeth) | Numeric side and its source |
|---|---|---|---|
| Head size | Noctua NF-A12x25 (board, core) | the head is the fan plus one structural wall all round; nothing else sets its size | fan frame side from the fan's datasheet/STEP; wall from the fits table's structural wall |
| Head corner radius | Muji, Braun (board, core) | one radius on every corner of the head outline (S2) | the head's corner radius equals one structural wall plus the fan frame's own corner clearance; a design input with its source in the master |
| Grille | Braun HL 1 (core) | concentric rings with radial ribs, cut in the head's front; no separate grille part, no front clip | ring gap narrower than the IEC 61032 test probe B finger (R7) |
| Fixings | Audioengine A1 (core) | screws only from below (puck floor, head underside); one screw type into heat-set inserts (M8) | screw size from the fits table and the board's holes |
| Neck | lighthouse/turntable (divergence) | a plain round post, the narrowest that carries the head and passes the fan cable | post bore from the fan cable's plug, post wall from the fits table |
| Puck | turntable platter (divergence) | a low round puck, its diameter no wider than the head (S4) | puck height = the tallest part inside it plus floor and top walls |
| Button | Muji (core) | one button on top of the puck, centred in front of the neck, its cap round and nearly flush | the button's panel cut-out and thickness range from its datasheet |
| Cable | Audioengine A1 | the USB-C cable leaves the puck at the back, straight out | port position from the board's STEP |
| Light | negative set (blue LED fan) | no light shows: the board's LEDs face into a closed opaque puck | — |
| Feet | quiet (attribute) | four soft adhesive bumpers under the puck, no hard plastic touches the desk | bumper size from its datasheet |
| Material and colour | Muji | every printed part one PETG colour, matte; the fan's black rotor the only contrast | — |
| Mass and footprint | formal: heavy base, light head | the puck carries the motor and boards low; nothing hangs outside the puck's footprint but the head above it | checked by R6's tip test |

## Signature elements
1. **One corner radius** on the head outline. Example: all four corners of the head, the same radius. Counter-example: a larger radius on the top corners "to soften it", or a chamfer on one edge and a fillet on another.
2. **Ring grille in the face.** Example: concentric rings cut through the front wall, crossed by radial ribs, all in the head's own material. Counter-example: a wire guard screwed over the front; a perforated metal disc (the decoy).
3. **Still puck, turning head.** Example: only the head moves; the button stays where the hand left it. Counter-example: the whole body turning (the Drum direction).
4. **Underside fixings.** Example: four screws under the puck, two under the head, all the same. Counter-example: one screw on the back of the head "because it is easier to print".

Special surfaces: the button follows signature 1 (a round cap, edge broken like the head); the grille is signature 2; no light (R5).

## Colour, material and finish
[person] Physical samples under the product's own conditions were not seen (no access to the founder). [derived] Choice: PETG in a warm off-white, matte — residual in the category is gloss white ABS (USB fans) or black (PC fans); warm matte off-white is emergent (Muji-like) and the one to keep. Sample reference: Prusament PETG "Signal White" is the stocked stand-in until a sample is checked.

## Stress test
Applied to a sibling, a "head and puck" phone stand like the pantilt sample: one corner radius on a rounded-square head that holds the phone, no grille because nothing in it breathes, the same still puck with one button under the turning head, screws only underneath. It reads as the same family, and every rule still decides something (one button, no visible fixing, no light seen except its own). Applied to the packaging: a plain card box, the head's corner radius on the box's die-cut window, no screws, no LEDs pictured. The language survives both.
