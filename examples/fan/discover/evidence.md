---
stage: discover
status: draft
---
# Evidence

## Observed scenes
Founder: not answered. No person has been observed with the problem, a prototype or the product; this gate item is open. [derived] Analogous-experience research and extreme-user interviews are needed before the brief is trusted (buyer = user; influencer: shop reviews).

## Grounding
| Claim | Source | Held? | Where it broke |
|---|---|---|---|
| Fan noise is set mostly by blade tip speed, so a larger fan at lower speed is quieter for the same airflow | Fan affinity laws (noise rises ~50·log10 of speed); e.g. Noctua's "fan noise" FAQ, https://noctua.at/en/support/faq (not opened in this build) | held (textbook) | not checked against a measured pair of fans here |
| A 5 V USB-C source gives at least 5 V × 0.5 A without negotiation | USB Type-C spec, Default USB power (USB 2.0: 500 mA) — https://www.usb.org/document-library/usb-type-cr-cable-and-connector-specification (not opened) | held | a Type-C source without the Rd resistors detected may give 0 V; the board must present Rd (the chosen board does) |
| Oscillating desk fans sweep about 80–90° in total | Vornado and Honeywell product pages list ~90° oscillation (not opened; from memory of the category) | estimate | unchecked |
| Remote workers keep small desks | founder ▸ "remote workers at small desks." | founder's word only | no measurement |
