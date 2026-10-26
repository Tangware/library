# 02 Define

Turn discovery into a brief sharp enough to reject a design. Source: the Offenbach theory of product language (semantic versus formal-aesthetic functions) and Monö's four semantic functions (*Design for Product Understanding*, 1997), applied as Product Semantic Analysis (Chalmers).

Reads `discover/`. Writes `prd.md`, `design/principles.md`, `design/formal.md`, `design/profile.md`, `design/decoy.md`, `design/rejected.md`, `references/board.toml`, `references/images/`.

## Steps

1. **[both] The PRD.** Write `prd.md` as R-numbered outcomes: what the product must do or be for its audiences, never how. A number chosen for look or behaviour is intent: write it with its reason. Every requirement must later map to one test. No status lists, no known issues. *Why:* the PRD holds intent, the model holds numbers, tests verify.

   ```markdown
   ## R3 The user can tell from across the room whether it is on
   ▸ "if I have to walk over to check, it failed"
   ```

2. **[agent] Cost sanity check.** Where the PRD sets a cost target, list the bought core it implies (boards, motors, sensors, power) with a stocked catalogue price for each, and add them up before any CAD. If the core alone misses the target, ask the person which gives way, the target or the core, before going on. *Why:* a target the bought parts already break only surfaces at the bill otherwise, after the model is built around them.

3. **[both] Semantic principles**, in `design/principles.md`: about six principles, each with a `Forbids:` line of specific things; then about five attributes, each with what it demands, what it forbids, and the surfaces it governs. Trace each to `discover/`. *Why:* a principle that forbids nothing cannot reject a design, and an attribute that reaches no surface cannot be checked.

4. **[both] Formal principles**, in `design/formal.md`: one position on each dichotomy (order/complexity, reduction/richness, primitive/sculpted, continuous/articulated, concealed/exposed fixings, uniform/varied materials, sharp/soft, light/heavy, symmetric/asymmetric, matte/gloss), each justified by an attribute and stating what it forbids. Add the hierarchy of emphasis (dominant, subdominant, subordinate) and surface continuity per part (C⁰, C¹, C²). Positions the CAD must hold go into `prd.md` as S-numbered shape rules. *Why:* "too toy-like" (semantic) and "too busy" (formal) are different objections; kept apart, neither is argued as the other.

5. **[agent] The semantic profile**, in `design/profile.md`: Describe, Express, Exhort, Identify (what is it and how is it used; what qualities does it have; what does it make me want to do; what family is it from), each with a **Must** and a **Must never** list, for buyer, user and influencer, at rest and in use. Where the profile repeats a conflict from `discover/audiences.md`, follow the side the shape serves. *Why:* it is the rejection test; "do you like it" returns an opinion poll.

6. **[agent] Score design traditions** (schools, eras, makers) against the attributes, under `## Traditions` in `discover/category.md`. State when the shortlist is biased toward what you already find plausible, and widen it. *Why:* scoring only the plausible is circular.

7. **[agent] The reference board**, `references/board.toml`: objects grouped by the job each does in the argument, one line each, images in `references/images/` or by url. Include a **negative set**: objects the brief forbids, each with the rule that kills it. *Why:* a reference earns its place by yielding a rule; browsing yields taste.

   ```toml
   [[item]]
   title = "…"
   image = "images/….jpg"
   job = "how a fixing can be exposed and finished"
   note = "[derived] …"
   set = "core"  # core | negative | decoy
   ```

8. **[person] The person's own board**, in any tool, on their own time. Add its items with their words as the note. Where it disagrees with the study, ask about it. *Why:* that disagreement is where what the person wants differs from what they said they want.

9. **[agent] The decoy gate.** Have a fresh agent or another model, given only `README.md` and the core references, write a deliberately plausible concept aimed at the brief's weakest point. Put it in `design/decoy.md` and as a `set = "decoy"` item. Run every principle, attribute and profile line against it and record which kill it and why. *Why:* if the rules cannot kill a plausible concept, they are not sharp enough.

10. **[both] Sharpen and re-run.** If the decoy survives, sharpen the rule that should have caught it, then re-run. Re-run the same decoy after every later revision of the brief.

Every position reached and reversed goes into `design/rejected.md` as it happens.

## Gate
- The decoy is killed by named rules, for stated reasons, and `design/decoy.md` records them.
- Every principle, attribute and formal position has a `Forbids:` line.
- Every R and S traces to `discover/` or the person's words.
- The bought core's stocked prices fit the cost target, or the person has chosen what gives way.
- The person approves each file. Then open `03-design.md`.
