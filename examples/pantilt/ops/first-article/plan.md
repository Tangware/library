---
stage: make
status: draft
---
# First-article plan

One unit built from the release's steps (the studio's build → manifest `steps`), checked against the model and the PRD.

| Check | From | How |
|---|---|---|
| Base outside diameter 70 mm, no wider than 85 mm | S4, master `body_diameter` | calipers |
| Pan turns ±90° without touching | R2, test_r2 | turn by hand to each stop, cables connected |
| Tilt +30° / −15° without touching | R3, test_r3 | turn by hand |
| A 60 mm and an 85 mm phone are both held; the jaw slides down onto each | R1 | two phones (or blocks) at 60 and 85 mm |
| It stands with a 270 g phone at both pan stops, tilted up and down | R5 | weighted block, on a desk |
| The tilt motor holds that phone, powered, at both tilt ends | R5 | powered hold for 1 minute each |
| One window shows; the lens sees past the cradle | S1, R6 | look; camera stream shows no cradle edge |
| USB-C plug seats from behind with the base fixed | R7 | a standard charger cable |
| Motion is silent on a call | R4 | record a video call; listen for motor noise |
| The signal harness reaches both drivers with the arm at both pan stops and the cradle at both tilt ends | M12 | turn by hand, wires connected |
| Every screw goes in with the listed hex key, in step order | M29 | build log |
| Mass vs model | manifest | scale |

Verdict: not run; no release exists.
