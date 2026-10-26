# 04 Model

Build the chosen direction as code with the library, in four steps: master sketch → parts → assemblies → bill. Each step reads only what the table allows, so a change flows one way. The library's `AGENTS.md` governs every line of `model/`: its rules M1–M30 and T1–T4 are the standard, and its Evidence section is how you report.

Reads `prd.md`, `design/language.md`, the chosen `design/directions/<name>.md`. Writes `model/` (scaffolded by `cad new`).

| Step | File | Holds | Reads | Never |
|---|---|---|---|---|
| 1 Master sketch | `model/src/<package>/master.py` | inputs, layout, interface records (frames, axes, planes, envelopes, swings, limits), keep-outs, poses | the PRD, the language, bought parts' data | any part's geometry |
| 2 Parts | `parts/<part>.py` | one part design per file, its feature list | the master only | another part, hardware, mates |
| 3 Assemblies | `assemblies/<asm>.py` | placement, every screw, insert, bearing, board and cable, mates, motion; hold order = build order | the parts and the master's records | new geometry |
| 4 Bill | `catalogue.py` | where to buy each bought part: supplier, part number, price, url, stocked, minimum order, lead time | the assemblies | swapping a part |

## Steps

1. **[agent] Bought parts first.** For each function the PRD needs (motor, board, bearing, fastener…), pick a cheap, documented part that normal distributors stock, with the maker's STEP and datasheet. A part behind a login is asked for, never substituted. Custom-made bought parts only with the person's yes. *Why:* the design is shaped around real catalogue parts; a size no one stocks makes an unbuildable design.

2. **[agent] Master sketch.** Write the design's few named inputs and derive everything shared from them as formulas: frames, axes, envelopes, swings, keep-outs, the rest pose. Every input carries its `why` and `source` (an R or S line, a language rule, a datasheet), and its label: measured or estimated. *Why:* every number has a source; a loose word ("a bit wider") is never turned into an invented one.

3. **[both] Layout review.** Commit and look at the studio's build of the commit yourself first, then show the person the envelopes at the rest pose. Real trade-offs (a requirement, the outside form, the layout) are theirs: one question each, your recommendation first, unit cost per option where known. Internal layout is yours.

4. **[agent] Parts**, one at a time: a few sketches and features in modelling order, edge breaks last, each feature a named step. Commit after each part and look at its build in the studio. *Why:* a part debugged feature by feature fails where the fault is.

5. **[agent] Assemblies:** place the parts, add all hardware, declare every mate and its limits, order the holds as the person will build it. Look at the exploded render in the commit's build.

6. **[agent] Bill:** fill `catalogue.py` for every bought line, including mating connector halves, cables, tools and the material each made part is priced from by weight (`kg`, the `material` the parts name, and its `colour`), and each made part's printing (`process_per_kg`). `price_source` is a url or `estimate: <reason>`. A substitute for a modelled part goes to the person with its STEP; where bill and model disagree, the model is right.

7. **[agent] Tests:** one per requirement (R), shape rule (S) or modelling rule (M), named after it, asserting the outcome on the built model.

8. **[agent] Read the gate**, which the studio's build of each commit runs: every check's verdict lands in the manifest as pass, fail, missing or stale. On a fail, suspect the check first: prove it right before changing the design. Report what was not verified before what was, and every check's `does_not_catch`.

9. **[person] Design review.** Show the renders, the bill with unit cost, and the unverified list. A design change is the person's call: bring the finding and a recommendation, then wait.

Commit after each step. A builder never shrinks or drops a specified feature to make a check pass; that is a design change.

## Screenshot marks
The person draws on a screenshot and pastes it with a text block: commit, camera, and the parts and faces under the strokes, each face with its `made_by` (file, line, feature step).
1. **[agent] Confirm the commit** is the one checked out; if not, check it out or ask.
2. **[agent] Treat the mark as a fact.** What the person sees is real; find why the model or the checks missed it. Go to the feature through `made_by`; if it is `null`, find it in the part's feature list and say so, never guess.
3. **[agent] Write the failing check first** (a test named after its R, S or M), see it fail, then fix the feature, see it pass. Commit with the trailer `Fixes-check: <test name>`.
4. **[agent] Build in the studio and show the same camera.**

## Gate
- The gate passes on the commit: every check ran, none fails, none is missing or stale.
- Every bill line is stocked, with a price source; every input has a source.
- Every R and S has a test.
- The person has seen the unverified list and approved the design. Then open `05-make.md`.
