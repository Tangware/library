---
stage: design
status: draft
---
# Language

Direction: `design/directions/lens-head.md`.

## Decision study
| Decision | Precedent | Rule | Numeric side, source |
|---|---|---|---|
| How the pan joint shows | Sachtler head, radar pedestal | the turning arm sits on the base's top face, coaxial, one running gap | gap = the print table's sliding fit (`Fits.sliding`) |
| How the tilt joint shows | theodolite, gimbal motor cans | a horizontal drum, its axis at right angles to the pan axis, on one side only | the drum's diameter follows the tilt motor's body |
| Pan range | R2 | a quarter turn each way from forward | ±90°, R2 |
| Tilt range | R3 | up a third of a right angle, down a sixth | +30° / −15°, R3 |
| Mass and footprint | P6, S4 | the heaviest part (pan motor) in the base; base no wider than the widest phone | base Ø ≤ 85 mm, R1/S4 |
| Where cables run | M12 | inside the base and arm; one cable loop crosses the pan joint inside the base | bend radius ≥ 6 × cable Ø where it flexes (M12) |
| Controls | P5 | none: it starts when plugged in | — |
| Power entry | R7 | the USB-C socket in the base's back face, on the fixed part | — |
| The lens | P1, S1 | one window, centred under the phone on the cradle's front face | — |
| Material changes | S3 | none on made parts; rubber only on the clamp's pads (bought) | — |
| Colour | S3, P4 | matte black | — |
| Fixings | formal: concealed from the front | screws from underneath and from the back only | M3, one type (M8) |
| Edges | formal: sharp, broken small | every outer edge broken with one chamfer | one size, the print table's edge break |

## Signature elements
1. **Crossed cylinders.** Pan = vertical cylinder (base), tilt = horizontal drum.
   Example: the base and the drum read as two plain cylinders at 90°.
   Counter-example: a sphere or dome head (D2), a ball joint (decoy).
2. **One-sided arm.** The tilt drum is carried from one side.
   Example: an L-shaped arm, motor on the outside of the drum.
   Counter-example: a symmetric fork (X3).
3. **Single lens below the phone.** Example: one small rectangular window, centred, under the clamp. Counter-example: two openings side by side; a lens above the phone.
4. **Rest pose:** forward, level. Counter-example: parked looking down, or nodding.
5. **One edge break** on every made part. Counter-example: soft large fillets (toy).

Special surfaces: the motion obeys element 4 and P2; there is no light or sound.

## Colour, material and finish
Matte black, dyed PA12 (MJF) [derived]: residual in camera gear (black is the code), chosen on screen. Residual is to be avoided by the runbook; here it serves P4/crew — the founder must confirm against physical samples (interview 0023: not done).

## Stress test: the packaging
Applied to the box: a black matte sleeve, two crossed lines (pan and tilt) as the only graphic, no face or mascot, one window showing the lens head. Counter-example: a box with a smiling robot illustration. The rules carry: crossed cylinders → crossed lines; one lens → one window; matte black → matte sleeve.
