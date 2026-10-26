---
stage: define
status: draft
---
# Cost sanity check

Run late: the runbook added this step (`02-define.md` step 2) after the model was built. It is recorded as if run at Define, on the same bought core the model uses.

▸ "500 units. Target landed cost under $45; it sells at about $99."

| Core part | Qty | Unit | Source |
|---|---|---|---|
| Seeed XIAO ESP32S3 Sense 113991115 | 1 | $13.90 | seeedstudio.com, single-unit price read 2026-10-23 |
| StepperOnline 17HS08-1004S | 2 | $6.67 | omc-stepperonline.com, volume price opened 2026-10-23 |
| Adafruit 6121 TMC2209 driver | 2 | $7.16 | adafruit.com, 100+ tier read 2026-10-23 |
| Adafruit 4090 USB-C breakout | 1 | $2.36 | adafruit.com, 100+ tier read 2026-10-23 |
| **Core total** | | **$43.92** | |
| Landed (+15% shipping and duties, estimate) | | **$50.51** | |

Result: the bought core alone breaks the $45 target before any printed part, screw or cable. The modelled stand lands at $90.98 with printing included (`ops/quotes/q1-500-units.toml`).

Question for the founder (interview 0028): which gives way, the target or the core? Options: a custom carrier board that puts the ESP32-S3, both TMC2209 drivers and the USB-C socket on one board (recommended; needs the founder's yes for a custom part) · raise the target · fewer features (no tracking sensor).
Founder: not answered. The model goes on with the stocked core, and `test_r8` fails honestly.
