# 01 Discover

Find out why the product exists, who it is for, what they already do, and what the category has taught. Nothing is drawn. Source: product semantics' second-order understanding (Krippendorff, *The Semantic Turn*): design from how each audience will read the object, not from the designer's view.

Writes `README.md` and `discover/`: `interview.md`, `story.md`, `evidence.md`, `audiences.md`, `category.md`.

## Steps

1. **[agent] Write the questions before asking any**, in order: story, evidence, purpose and refusals, audiences, character, then form. Assume no fact about the product. *Why:* a fact the agent assumed is unreliable; only the method carries over.

2. **[both] One line for `README.md`:** what the product is, in the person's words. *Why:* every later file is checked against it.

3. **[person] The founding story**, to these headings: the scene that started it · what you believed before and what broke · the detours · why this form or category · what you refuse · what a person should feel · why this, why you · why a physical product and not an app · why this user, why now · what has to be true. Ask them one heading at a time; the ones the person cannot answer become later questions. Require **one real scene** and **one place the person was wrong**. Write `discover/story.md`. *Why:* a story with no reversal is a brochure.

4. **[person] The observational base:** real people with the product, a prototype or the problem; specific scenes, what they did, not what they said. With none, the person runs **analogous-experience research** (places outside the industry where the same problem is already solved) and **extreme-user interviews** (the very familiar and the completely unfamiliar), separately for buyer, user and influencer. Write each scene in `discover/evidence.md`, with who, where and when. *Why:* behaviour beats stated preference. Source: IDEO Method Cards.

5. **[agent] Ground every hypothesis.** For each claim the story or evidence rests on, find a source; record under `## Grounding` in `discover/evidence.md` the claim, the source, whether it held, and where it broke. *Why:* an unchecked claim is a thought masquerading as a conclusion.

6. **[both] Purpose and refusals.** List what the product refuses to be or do, then trace every refusal to one root; write both in `discover/story.md`. *Why:* refusals with one root are one refusal, and the root decides new cases.

7. **[both] Audiences.** Name the **buyer** (pays), the **user** (lives with it) and the **influencer** (recommends or vets it); one person may hold two roles. For each: what they must take from the object at a glance. Write `discover/audiences.md`.

8. **[both] Name the conflicts** wherever two audiences read the object differently. Write each down; do not compromise it. For each, the person decides which audience the **shape** serves; the others are served through material, packaging, voice and the product's special surfaces (anything it owns beyond its shell: a screen, a light, a sound, a motion). *Why:* one object cannot express two identities well.

9. **[both] Character.** Use the twelve brand archetypes only as a start; resolve to one named character the person recognises, and write what each rejected archetype forbids. Add to `discover/audiences.md`. *Why:* a named character carries more constraint than a type.

10. **[agent] Story structure check.** If the product itself guides the user, the brand cannot also play guide; choose the brand's role and record it in `discover/story.md`. *Why:* otherwise the story collapses into the object.

11. **[agent] Category audit.** Pick the neighbouring categories with the person, plus a **failed-products set**: products that tried this and failed, each with its named failure mode and source. Per object, pull the codes: form vocabulary, proportion, palette, materials, face or not, joints and seams, how its special surfaces show, what it does when idle. Write `discover/category.md`. *Why:* the failed set rejects more directions than anything else, and almost nobody builds it.

## `discover/audiences.md` shape

```markdown
---
stage: discover
status: draft
---
## Buyer
▸ …
## Conflicts
### C1 Buyer reads <x>, user reads <y>
Shape serves: user ▸ …
Buyer served through: material, packaging [derived]
```

## Gate
- `discover/story.md` holds one real scene and one reversal.
- Every audience conflict is named, each with the side the shape serves and the person's words.
- The failed-products set has at least one product with a sourced failure mode.
- The person approves each file. Then open `02-define.md`.
