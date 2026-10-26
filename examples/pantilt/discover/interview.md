---
stage: discover
status: draft
---
# Interview

Every question asked and the answer, in order; verbatim answers are marked ▸.
The founder could not be reached live. Every answer is quoted from the founder's answer sheet; a question the sheet does not answer is recorded as "Founder: not answered" and decided by the agent, marked `[derived]`, unvalidated until the founder confirms it.

## 0001 · discover · story
Q: In your own words, what is the product?
Options: as you said it (recommended) · rephrase
▸ "A phone stand that turns and tilts to keep my face in frame while I teach online."

## 0002 · discover · story
Q: Who are you, and why you?
▸ "an online tutor turned founder, non-technical, with a teaching audience to sell to."

## 0003 · discover · story
Q: The scene that started it: one real lesson where the frame failed you. Where, when, what happened?
Founder: not answered.
[derived] No real scene is on record. The idea implies one: a tutor who moves while teaching (to a whiteboard, to hold up a book) leaves the phone's fixed frame.

## 0004 · discover · story
Q: What did you believe before, and what broke? One place you were wrong.
Founder: not answered.
[derived] No reversal is on record.

## 0005 · discover · story
Q: Why a physical product and not an app (a software crop, Apple's Center Stage or DockKit)?
Founder: not answered.
[derived] A crop loses resolution and cannot follow a teacher who leaves the lens's field; only turning the phone keeps the whole frame.

## 0006 · discover · story
Q: Why this user, why now?
▸ "online teachers and streamers."
[derived] "Why now" is not answered.

## 0007 · discover · evidence
Q: Have you watched real teachers use a stand or a prototype, or work around the problem? One scene: who, where, what they did.
Founder: not answered.
[derived] No observational base. Desk sources stand in under `## Grounding` in `discover/evidence.md`.

## 0008 · discover · purpose
Q: What must the product do, above all?
▸ "smooth, silent motion; fits any phone 60–85 mm wide; it reads as a camera tool, not a toy robot."

## 0009 · discover · refusals
Q: What does it refuse to be or do?
▸ "a face or eyes on the device, cloud accounts, anything that looks cheap in the background of a video."

## 0010 · discover · audiences
Q: Who pays, who lives with it, who recommends or vets it?
Options: buyer = user, students influence (recommended) · a school buys · other
▸ "Buyer = user; influencer = their students, who see the video."

## 0011 · discover · audiences
Q: Volume and price: how many, at what cost and price?
▸ "500 units. Target landed cost under $45; it sells at about $99."

## 0012 · discover · conflicts
Q: The teacher wants to forget the stand; the students see its motion as the camera moving. Which does the shape serve?
Options: the teacher (recommended) · the students
Founder: not answered.
[derived] The teacher. Students are served through motion character. See `discover/audiences.md` C1.

## 0013 · discover · conflicts
Q: A streamer may show the stand on camera; a teacher hides it behind the phone. Which does the shape serve?
Options: seen on camera (recommended) · hidden
Founder: not answered.
[derived] Seen on camera, because of ▸ "anything that looks cheap in the background of a video." See C2.

## 0014 · discover · character
Q: Which character is the stand: a camera operator, a stage hand, a pet, a butler?
Options: a camera operator (recommended) · a stage hand · a pet · a butler
Founder: not answered.
[derived] A camera operator, from ▸ "it reads as a camera tool, not a toy robot."

## 0015 · discover · form
Q: Where does it live: desk, tripod, shelf?
Founder: not answered.
[derived] On the desk in front of the teacher, standing alone.

## 0016 · discover · form
Q: How does it find the face: the phone's camera through an app, or a sensor of its own?
Options: a sensor of its own (recommended: works during any video call, on any phone) · the phone's camera through an app
Founder: not answered.
[derived] A sensor of its own. A video-call app holds the phone's camera, so a companion app cannot see the face during a lesson. One lens, never two: ▸ "a face or eyes on the device."

## 0017 · discover · form
Q: Power: a USB cable, or a battery?
Options: USB-C cable (recommended: a lesson runs for hours) · battery
Founder: not answered.
[derived] USB-C at 5 V from any phone charger; no battery to wear out or ship.

## 0018 · define · prd
Q: Do you approve the PRD as written?
Founder: not answered. `prd.md` stays draft.

## 0019 · define · board
Q: Your own board: objects you'd be proud to have on camera, and ones you'd hate.
Founder: not answered. `references/board.toml` holds the study only.

## 0020 · design · models
Q: Full-scale models in your teaching setup, at rest and in use.
Founder: not answered. None made.

## 0021 · design · readings
Q: Naive viewers: what is it, what does it do, who is it for, what would it do next?
Founder: not answered. No readings exist.

## 0022 · design · choice
Q: Which direction: "Lens head" or "Tower"?
Options: Lens head (recommended) · Tower
Founder: not answered.
[derived] Lens head, the agent's recommendation.

## 0023 · design · CMF
Q: Colour, material and finish against physical samples in your teaching light.
Founder: not answered.
[derived] Matte black, chosen on screen; no samples seen.

## 0024 · model · layout
Q: The envelopes at the rest pose: approve the layout?
Founder: not answered.

## 0025 · model · custom parts
Q: A small carrier board would replace the wired driver modules. Approve a custom PCB?
Options: no: stocked modules and harnesses (recommended for 500 units) · yes: a custom board
Founder: not answered.
[derived] No. Custom-made bought parts need the person's yes, so the design uses stocked modules.

## 0026 · make · concept review
Q: Is this the product to make, at this bill and with these unverified checks?
Founder: not answered. See `reviews/2026-10-23-concept.md`.

## 0027 · make · release
Q: Tag the release `v1`?
Founder: not answered.
Not tagged: `cad gate` fails on R8 (landed cost $90.98 against $45, printing included); see `reviews/2026-10-23-concept.md`.

## 0028 · define · cost
Q: The stocked core (camera board, two motors, two drivers, USB-C board) lands at about $50.51, over the $45 target before any printed part; the whole stand lands at $90.98 with printing ($79.11 of parts, $29.59 of it printed parts). Which gives way?
Options: a custom carrier board (recommended) · raise the target · drop the tracking sensor
Founder: not answered. See `design/cost.md`.
