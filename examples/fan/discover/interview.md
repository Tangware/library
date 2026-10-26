---
stage: discover
status: draft
---
# Interview

Every question asked and the answer, in order; verbatim answers are marked ▸.
The founder could not be reached live. Every answer below is quoted from the founder's answer sheet; a question the sheet does not answer is recorded "Founder: not answered" and decided by the agent, marked [derived].

## Question list (written before asking)
Story: 0001 product in one line · 0002 the scene that started it · 0003 what you believed and what broke · 0004 the detours · 0005 why a fan · 0006 why you · 0007 why a physical product, not an app · 0008 why this user, why now · 0009 what has to be true.
Evidence: 0010 who have you watched with the problem.
Purpose and refusals: 0011 what it must be · 0012 what it refuses.
Audiences: 0013 who it is for · 0014 who pays · 0015 who recommends or vets it.
Character: 0016 a character you recognise.
Form: 0017 how it should look · 0018 how it is powered · 0019 how it is controlled · 0020 volume, cost and price.

## 0001 · discover · story
Q: What is the product, in one line?
▸ "A quiet desk fan that slowly sweeps side to side, for a hot home-office desk."

## 0002 · discover · story
Q: The scene that started it: where were you, what happened?
Founder: not answered.
[derived] No scene exists; the story is written from the founder's situation only.

## 0003 · discover · story
Q: What did you believe before, and what broke?
Founder: not answered.
[derived] No reversal on record; story.md marks the gap.

## 0004 · discover · story
Q: What detours did you take?
Founder: not answered.

## 0005 · discover · story
Q: Why this category (a fan)?
Founder: not answered.
[derived] The founder already sells desk accessories; a fan is the desk accessory that needs electronics.

## 0006 · discover · story
Q: Why this, why you?
▸ "a solo maker who sells desk accessories on Etsy and wants a first electronic product."

## 0007 · discover · story
Q: Why a physical product and not an app?
▸ Refuses: "an app."
[derived] The product must work entirely from the object itself.

## 0008 · discover · story
Q: Why this user, why now?
▸ "remote workers at small desks."

## 0009 · discover · story
Q: What has to be true for this to work?
▸ "200 units first batch. Target landed cost under $35; it sells at about $79."
[derived] It must be buildable by one maker in batches of 200 from stocked parts, and quiet enough to sit on a desk during calls.

## 0010 · discover · evidence
Q: Who have you watched living with the problem, and what did they do?
Founder: not answered.
[derived] No observation exists; evidence.md records analogous products and grounding only.

## 0011 · discover · purpose
Q: What must it be above all?
Options: quiet (recommended) · strong airflow · cheap
▸ "quiet above all"

## 0012 · discover · refusals
Q: What do you refuse?
▸ "visible screws on the front, blue LEDs, a remote control, an app."

## 0013 · discover · audiences
Q: Who is it for?
▸ "remote workers at small desks."

## 0014 · discover · audiences
Q: Who pays: the same person?
▸ "Buyer = user."

## 0015 · discover · audiences
Q: Who recommends or vets it?
Founder: not answered.
[derived] The influencer is the Etsy shop page and its reviews, plus people seeing it on video calls.

## 0016 · discover · character
Q: A character you recognise for it?
Options: the quiet craftsman (recommended) · the caregiver · the everyman
Founder: not answered.
[derived] The quiet craftsman: a well-made object that does one thing and stays out of the way.

## 0017 · discover · form
Q: How should it look?
▸ "it looks like an object, not an appliance"

## 0018 · discover · form
Q: How is it powered?
▸ "USB-C powered"

## 0019 · discover · form
Q: How is it controlled?
▸ "one button"

## 0020 · discover · form
Q: Volume, cost and price?
▸ "200 units first batch. Target landed cost under $35; it sells at about $79."

## 0021 · define · prd
Q: How quiet is quiet enough?
Options: inaudible during a call (recommended) · quieter than a laptop fan · no target
Founder: not answered. ▸ "quiet above all"
[derived] No louder than a quiet room (25 dB(A)), so it can stay on during a call.

## 0022 · define · prd
Q: How wide should it sweep?
Options: about 90° total, the category's norm (recommended) · narrower, just the user's seat · adjustable
Founder: not answered.
[derived] 90° total, fixed.

## 0023 · define · formal
Q: Fixings: hidden or exposed?
Options: hidden (recommended) · exposed and finished on the back only
▸ refuses "visible screws on the front"
[derived] Hidden from front and top; underside and back may carry screws.

## 0024 · define · formal
Q: Any light at all (e.g. a warm power light)?
Options: none (recommended) · a warm-white light that fades out
▸ refuses "blue LEDs"
[derived] None: the refusal root (never ask for attention) decides it.

## 0025 · define · board
Q: Your own reference board?
Founder: not answered. [derived] The study board stands alone; no disagreement can be checked.

## 0026 · design · directions
Q: Which direction: Head and puck (still base, turning head) or Drum (whole body turns)?
Options: Head and puck (recommended) · Drum
Founder: not answered.
[derived] Head and puck: the button stays put (▸ "one button"), and the drum's size follows the fan's diagonal.

## 0027 · design · naive viewers
Q: Can you show both directions, printed full size, to people who were not in the room?
Founder: not answered. [person] gap; no readings recorded.

## 0028 · design · colour
Q: Colour and finish against a physical sample?
Options: warm off-white matte PETG (recommended) · black matte · natural
Founder: not answered. [derived] warm off-white matte.

## 0029 · model · bill
Q: The bill with an Adafruit Feather RP2040 lands at about $37, over your $35. Swap to a Seeed XIAO RP2040 held by tape (recommended), or keep the Feather and raise the target?
Options: swap to the XIAO (recommended) · keep the Feather, raise the target to $38
▸ "Target landed cost under $35"
Founder: not answered beyond the target. [derived] Swap to the XIAO.

## 0030 · model · fan supply
Q: The only quiet 5 V PWM 120 mm fan at Mouser/Digi-Key (Same Sky CFM-A225C-015-287-22, 24.8 dB(A)) is sold in factory lots of 510, 17 weeks. Order one lot (2.5 batches) (recommended), or pay $34 for a Noctua NF-A12x25 5V PWM?
Founder: not answered. [derived] One lot of 510; the Noctua alone breaks R8.

## 0031 · make · concept review
Q: Is this the product to make, at this bill and with this unverified list?
Founder: not answered. [derived] Released as `v1` on the agent's instruction; orders not placed.

## 0032 · make · DFM
Q: Which partner reviews manufacturability (in-house printing assumed)?
Founder: not answered. No DFM review held; no tooling is involved.

## 0033 · model · cost with printing
Q: With printer time costed (about $4.45 a fan at 21.5 USD/kg of in-house PETG, estimate), the fan lands at $39.50 against your $35. Which do you want?
Options: raise the target to $40, still a 2× margin at $79 (recommended) · count your own printer time as overhead, not landed cost · cut cost: a smaller printed head and base, or a cheaper fan (louder) · keep $35 and redesign
▸ "Target landed cost under $35; it sells at about $79."
Founder: not answered. R8 is left failing and no v3 release is tagged until this is decided.
