---
stage: design
status: draft
---
# Mechanisms

Every way to move air and sweep it, from the PRD. [derived] Drafted by the agent; the person adds and cuts.

## Air
- **Axial fan behind a grille.** A stocked 5 V PC fan; quiet comes from size run slow (R1), and its square frame sets the head.
- **Bladeless ring.** An impeller in the base pushes air through a slot; louder than a slow axial fan (R1).
- **Cross-flow (tangential) rotor.** A long rotor behind a tall slot; a wide even stream, but no stocked 5 V rotor fits the brief (`design/divergence.md`).
- **Centrifugal blower.** Air turned 90° in a scroll; louder than an axial fan for the same air (R1, rejected as the Jellyfish bell).

## Sweep
- **Head on its own stepper (two motors).** A geared stepper turns only the head; the base and its button stay still (R4), and the sweep is set in firmware (R2). Chosen.
- **Head on a geared oscillator (one motor).** The classic crank-and-gear off the fan's shaft; a brushless PC fan has no shaft to take it from, and gears whine (P3).
- **Whole body turns.** The fan fixed in one body that turns on a foot; the button turns away from the hand (P4), and the drum grows to the fan's diagonal (S4).
- **Louvres sweep, fan still.** Vanes in front of a fixed fan swing the stream; nothing outside moves, but vanes in the stream add noise (R1).
- **No sweep: wide spread.** A grille that fans the air out instead of moving; fails R2 by definition.
