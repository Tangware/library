# Runbooks

How a coding agent takes a product idea from nothing to a priced, buildable design, with the person deciding. Read this file, then the runbook of the stage the design repo is in. Steps run in order; each ends in a file, and each stage ends in a gate. A new design repo starts with `cad new <dir>`.

| Stage | Runbook | Writes | Gate |
|---|---|---|---|
| Discover | `01-discover.md` | `README.md`, `discover/` | Every audience conflict named, with the side the shape serves |
| Define | `02-define.md` | `prd.md`, `design/principles.md` `formal.md` `profile.md` `decoy.md`, `references/` | The brief kills a plausible decoy for stated reasons |
| Design | `03-design.md` | `design/divergence.md`, `design/directions/`, `design/language.md` | One direction, read as intended by people outside the room |
| Model | `04-model.md` | `model/` | The gate passes: every check run, none failing |
| Make | `05-make.md` | git tag, `reviews/`, `ops/` | A first article that matches the release |

Marks: **[person]** needs the person or real people; nothing substitutes. **[agent]** the agent runs alone. **[both]** the agent drafts, the person cuts.

Method source: the five-phase product-semantics process (Krippendorff, Monö, Offenbach, Design-by-Analogy, Product Semantic Analysis).

## The interview
- **Ask with your own question tool;** with none, ask in plain chat. One decision per question, short multiple choice, your recommended option first and labelled, with a free-text way out.
- **Zoom in and out:** follow an answer down one level, then step back to the stage's open list.
- **You derive; the person supplies evidence, instincts and refusals.** Never hand over a long document to structure, and never ask a design question the stage exists to answer.
- **Record every question and answer** in `discover/interview.md` the moment it is answered, in order, for every stage:

```markdown
## 0007 · define · formal
Q: Fixings: hidden or exposed?
Options: exposed and finished (recommended) · hidden · mixed
▸ exposed, but not on the front
```

## Files
- Stage files are Markdown with front matter: `stage: discover|define|design|model|make` and `status: draft|approved`. Only the person's yes sets `approved`.
- **Provenance on every line that states a decision:** `▸` before the person's words, verbatim; `[derived]` before your synthesis, which stays unvalidated until the person confirms it.
- `git pull` before each step; commit after it, the message saying what was decided. Generated outputs (meshes, renders, the manifest, bills) are never committed.

## Working rules, every stage
- **A rule forbids specific things.** A principle that forbids nothing is a slogan and cannot reject a design.
- **Keep every rejection** in `design/rejected.md`: the position, what killed it, the error. It stops re-litigation.
- **Watch for the theory arriving after the conclusion.** A position held first and dressed in framework later dies on the first direct question; reopen it.
- **One person makes each taste call.** Gather input broadly; never decide by committee.
- **No deliverable that only communicates to people not in the room** (positioning 2×2s, blue-ocean charts): it gives the design nothing to be checked against.
- **A gate that fails sends you back,** to the step that produced the gap. Never mark a stage approved with a gap open.
