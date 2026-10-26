# 03 Design

Generate far more ideas than needed, narrow to one direction people read as intended, and turn it into rules the CAD can follow. Sources: Design-by-Analogy (Keshwani and Casakin, *Biomimetics*, 2024); Product Semantic Analysis for testing; design language as brand DNA → positioning → principles → signature elements.

Reads `prd.md`, `design/`, `references/`. Writes `design/divergence.md`, `design/directions/<name>.md`, `design/language.md`, `design/rejected.md`.

## Divergence

1. **[agent] Analogy at three distances, run separately:** biological (nature), cross-domain (distant engineering), within-domain (near products). Many quick thumbnails per round: a one-line form idea, and a rough image in `references/images/` where you can make one. Nothing rendered, nothing finished. Tag each with its distance and source. Write `design/divergence.md`. *Why:* unstructured brainstorming produces the average idea, and left alone, designers default to biological analogies.

2. **[agent] Read the clusters.** Count thumbnails per distance and per formal position; push a further round into the empty regions. Evaluate nothing until the set is full. *Why:* attachment ends divergence early.

3. **[agent] The kill pass.** Run every thumbnail against the brief; each one killed goes to `design/rejected.md` with the rule that killed it.

If prototyping has already fixed the envelope, divergence may run inside definition, each idea proposed and killed in one pass; record that, and its cost, at the top of `design/divergence.md`.

## Convergence

4. **[both] At least two genuinely distinct directions** from the survivors, each in `design/directions/<name>.md`: name, form vocabulary, palette, motion character (if it moves), one-line story, verdict. Distinct means they differ on a formal position or the dominant element; two that read alike mean divergence was too narrow: go back. *Why:* with one direction, the choice was defaulted into, not made.

5. **[agent] Run each direction against the profile and the decoy's killing rules;** record each Must and Must-never line it meets or breaks.

6. **[person] Full-scale models in the real setting:** printed, foam or card, in real light, at rest and in use. *Why:* the rest pose is where the product spends its life, and a screen hides scale.

7. **[person] Semantic testing on naive viewers**, people who were not in the room. Ask what it is, what it does, who it is for, what it would do next. Never ask whether they like it. Record each answer verbatim under `## Readings` in the direction's file, at rest and in use, beside the profile line it confirms or breaks. *Why:* a profile only the designers have read is untested.

8. **[person] The choice.** The person picks one direction. Set every other direction's verdict to rejected, with the reason, and add it to `design/rejected.md`.

## Design language

9. **[agent] The decision study.** List every decision the CAD must make (how joints show, where cables run, mass and footprint, how controls work, where materials change, colour…). For each, interrogate the precedents on the board and derive a rule with teeth plus its numeric side, the number's source named. Write `design/language.md`. *Why:* it is the only precedent research a CAD model can read.

10. **[both] Signature elements:** the repeatable features that carry the identity (a joint treatment, a section, a transition, one governing radius, one material break, a rest pose). Each is a rule with an example and a **counter-example**, in `design/language.md`. Govern the special surfaces by the same language. *Why:* guidelines that only show correct use get reinterpreted.

11. **[person] Colour, material and finish against physical samples**, under the product's own conditions (its own light or heat, if it makes any). Code each choice residual, dominant or emergent in its category; avoid the residual. Record the choices and the sample references in `design/language.md`. *Why:* colour and finish judged on screen are wrong.

12. **[agent] Stress test:** apply the language to something other than this product (a sibling product, its packaging) and show the result. *Why:* a language that fits one object is a style.

## Gate
- One direction chosen, with naive viewers' verbatim readings matching the profile at rest and in use.
- At least two directions were drawn, and every rejected one is in `design/rejected.md`.
- `design/language.md` turns every CAD decision into a rule with a counter-example, and survives the stress test.
- The person approves each file. Then open `04-model.md`.
