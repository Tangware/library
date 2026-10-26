---
stage: define
status: draft
---
# fan requirements

R-numbered outcomes, intent only. `▸` marks the person's words, `[derived]` agent synthesis.

## R1 It is quiet enough to leave on during a call
▸ "quiet above all"
[derived] Its loudest setting is no louder than a quiet room: 25 dB(A), the level fan makers quote for a "quiet" 120 mm fan (Noctua NF-A12x25 datasheet, 22.6 dB(A)), so the user never turns it off to speak.

## R2 It sweeps slowly from side to side
▸ "A quiet desk fan that slowly sweeps side to side"
[derived] A sweep of 90° in total, the category's usual oscillation (see `discover/evidence.md`), so it covers a person shifting in their chair; one full sweep and back takes at least 20 s so the motion is never noticed out of the corner of the eye.

## R3 It runs from any USB-C charger
▸ "USB-C powered"
[derived] It draws no more than a USB-C port gives without negotiation (5 V, 500 mA), so any charger or laptop port runs it.

## R4 Everything is done with one button on the object
▸ "one button" · refuses ▸ "a remote control, an app."

## R5 No light shows from outside
▸ refuses "blue LEDs"
[derived] The root of every refusal is that it never asks for attention (`discover/story.md`), so no light of any colour shows.

## R6 It stays put on the desk while it sweeps
[derived] A small desk is knocked and leaned on; the fan must not tip at any point of its sweep.

## R7 Fingers cannot reach the blades
[derived] It sits within reach on a desk; a finger pushed at the grille must not touch a blade.

## R8 One maker can build 200 of them under $36 each, landed
▸ "200 units first batch. Target landed cost under $36; it sells at about $79."

## Shape rules

## S1 No screw is seen from the front
▸ refuses "visible screws on the front"
[derived] Screws go in from the underside or the back only.

## S2 The head is one form with one corner radius
▸ "it looks like an object, not an appliance"
[derived] From `design/formal.md`: primitive and continuous; every corner of the head's outline takes the same radius. (Reached in design: a round head was rejected, see `design/rejected.md`.)

## S3 Every printed part is one material in one colour
[derived] From `design/formal.md`: uniform material, matte.

## S4 Nothing stands wider than the head
▸ "remote workers at small desks."
[derived] Sharpened after the decoy (`design/decoy.md`): the fan takes no more desk than its own face.
