---
stage: make
status: draft
---
# Make plan

Blocked before step 2 (release): the gate fails on R8 (landed cost). Steps below are written for the release that follows the founder's cost decision.

## 1 Concept review [person]
`reviews/2026-10-23-concept.md`. Needs the founder's choice: custom carrier board, or a higher target.

## 2 Release [agent]
On the reviewed commit with `cad gate` all-pass: `git tag -a v1`, message = gate result + unverified list.

## 3 Quote [agent]
- Made parts (base, lid, arm, cap, cradle, jaw): FDM PAHT-CF black at JLC3DP; upload the six STEP files from the studio's build, 500 of each. Every made-part price in `ops/quotes/q1-500-units.toml` is an estimate until this quote.
- Bought lines at 500: StepperOnline (17HS08-1004S, volume tier), Adafruit (6121, 4090; 100+ tier, ask for 500), Seeed (113991115; ask for a 500 tier), Lee Spring (LE 031C 05 S), Accu (M3 x 6, M2 x 4), Dupont harnesses, CNC Kitchen (M3 and M2 inserts).
- Landed: shipping and duties quoted, replacing the 15% estimate.

## 4 DFM sign-off [person]
JLC3DP reviews the six parts. Known risks to raise: the arm's 70 mm foot disc is solid (cost, warp); the lid is held by three screws in the front third only; the camera board sits in a pocket without a retainer; the jaw's 6 mm stem slides in a printed channel (wear, M11).

## 5 Order [person]
`ops/orders/<id>.toml` once a quote is accepted. No tooling: every made part is printed.

## 6 First article [both]
`ops/first-article/plan.md`.
