# tangware — mechanical design as code
`model/` holds `cad`, the generic machinery for modelling a mechanism in code. Parts are build123d solids, mated as in CAD. The mates are the only record of how parts join and move; the build service derives the simulation from them, so no part list, joint table or gear ratio exists anywhere else, and a CAD mistake shows up in the simulation. A design built on `cad` lives in its own package; nothing here names one.

`runbooks/` takes a product from idea to a priced, buildable design, one runbook per stage; start at `runbooks/README.md`.

Model lengths in mm, forces in N, torques in Nm, angles in degrees.

`src/cad/`, layered by `.importlinter`:
- `library/` — the part builders' decorator (M3), shapes and connectors, mates, fits and printing (M17), `Why` (M6), shared `features/`, `standard/` parts, `bought/` parts read from makers' STEP or `models/` (ours, for parts without maker CAD), gears and the extension spring.
- `generators/`, `cables/` — the only maths (M18); `cables/` here declares cables.
- `assembly/` — the part tree.
- `design/` and `cli.py` — a design package (master, `@part` builders, assemblies, catalogue) and `cad new` and `cad upgrade`; `examples/box/` is the worked example.

The part cache, the export, the checks, analysis, the MJCF, the bill and the renders run on the build service, which adds `cad export`, `cad check` and `cad render` to the same `cad` command.

---

## Running it
Do feature work in a worktree (`git worktree add .worktrees/<name>`), never on `main`. `just install`, then `just hooks` once per clone and once per worktree. `just lint` — ruff, mypy, the import contracts and the CAD rules in `model/src/cad/lint/rules/`; the pre-commit hook runs it. `just test` — `model/tests`. `build/` is a local output, under the directory the design runs from.

Every PR is born a draft; `just land` is the only path to `main` — runs the full local suite, and only on green flips the PR out of draft and merges. `gh pr create` without `--draft`, `gh pr ready`, and `gh pr merge` are denied by `.claude/hooks/require_draft_pr.py` — use `just pr`/`just land` instead. `just check` runs pre-commit checks without committing. `just release` publishes the package to PyPI.

---

## How we work
- **Finish the work.** No TODO or work-tracking comments, no "later" notes anywhere: fix it now, or say so and stop. Never report something done while a gap remains; "done, except…" is not done.
- **Fix at the root.** Fix an error where it comes from; the same kind of error twice means fixing the mechanism that makes it. A cause too deep for the change at hand goes to the person with a recommendation, never patched around.
- **A defect against an existing convention is fixed, not asked about.** Only real trade-offs (requirements, form, layout) go to the person.
- **Simplest path first:** fix our own bug or remove a feature before adding parts, part types or machinery; ask at most one or two questions.
- **A change that replaces machinery deletes what it replaced, in the same change.** A decided rule lives in the repo next to what it governs, not in a plan file.
- **Name things as the code names them;** no invented shorthand.

## Evidence
- **Check before claiming.** Before saying what a change touches, what depends on what, or that something is fine, trace it in the model and say what was traced; otherwise say "not checked yet". Report what was not verified before what was.
- **Every check states what it doesn't catch** (forces, tolerances, feel), so a pass is never read as more than it proves.
- **Hand math first.** On a sizing question, do the few lines of statics from the model's own values and read the existing load tests before any research.
- **Label every number** as measured (model, datasheet, test) or estimated.
- **No made-up numbers.** Never turn loose words ("a bit further") into an invented angle, margin or clearance; build it from sizes that have a source, and prefer the smallest move that meets the ask.
- **Suspect the check first.** A big failure in a planned design is more likely a check or model bug (an unreachable pose, a misplaced load, a stale cache); prove the check right before changing the design.
- **What the person sees is a fact.** A clash seen in the viewer is real: find why the model or the checks missed it, fix that, then the geometry.
- **Before blaming a vendor file or datasheet,** rule out our side (the query picked the wrong feature, the datasheet was misread) and show the evidence chain and an independent cross-check.
- **Check a method's preconditions** against our model before proposing it.
- **Cite the primary:** who was measured, under what conditions, and whether the source was opened. A vendor number carries its flag wherever it travels.

## Requirements and design
- **The PRD holds intent; the model holds numbers; tests verify.** A requirement is an outcome, never an implementation. A number chosen for look or behaviour is intent and goes in the PRD with its reason. No status or known-issue lists in it.
- **Design changes are decided with the person.** Bring the finding and a recommendation, then wait. An agent may correct modelling (seats, mates, a check), fix what its own change broke, and do a design step already chosen. How a seat, clamp or contact face works follows the model as built.
- **A builder never shrinks or drops a specified feature to make a build pass;** that is a design change.
- **"Keep the design" means the outside.** Internal layout (drive placement, orientation, drive type) is engineering's choice.
- **Build the MVP for manufacture:** it tests what production will have and adds nothing only the MVP needs. Settle a durability issue now if its later fix would change the layout or mechanism; leave it if a better grade of the same thing in the same space fixes it.
- **Access only through parts production also has.**
- **Leave room for a known future change; add nothing for it now.**

## Code
- **One settings module reads the environment;** nowhere else, tests included. A value with more than one correct answer gets no default.
- **Fail fast on broken infrastructure or invariants.** Never a blanket `except` that logs and continues; catch a specific, documented transient with bounded retry.
- **No silent fallbacks.** An unknown key answered with a default (the last frame, the nearest face) raises instead.
- **Don't engineer for the impossible or the negligible;** prefer a simple, explicit escape hatch over an automatic one that fails silently.
- **Search before you assume** a library's API or config format. Use latest stable versions.
- **Write no new comments, docstrings or doc text by default;** change the code instead (a name, an explaining variable, an assertion). One that's genuinely needed is listed at the end of the work for approval.
- **Existing text only shrinks.** A comment states its reason at the smallest scope that owns it, as the code is now. A docstring is a one-line imperative summary ending in a period, then `Args:`/`Returns:`/`Raises:` only if earned. A change that makes a doc false corrects it.
- **A closed set is a `StrEnum`;** `Literal` only for a single-value tag.
- `except A, B:` without parentheses is valid Python 3.14 (PEP 758); don't "fix" it.
- **Rebasing a branch with merge commits needs `git rebase --rebase-merges`.**

---

## Modelling rules
Each rule keeps its number: tests are named after them.
- M1 Simplest first, then smallest and lightest; simple wins when they conflict. Minimise every size and every part type (bearings, fasteners, rod ends), below structural correctness and the outside form.
- M2 Top-down: a design's few named inputs feed its skeleton; every shared axis, frame, plane, envelope, mating and rotation point, swing and limit is a property of the skeleton, as a formula of the inputs. A record read by two or more areas is a skeleton interface; one read by two builders in one area is that area's record; one read by one builder belongs in it.
- M3 A part is a pure function of explicit inputs — its own numbers, the skeleton records it is given, and bought parts' interfaces; never another of our parts. Built in its own frame, placed by its pose; the build service caches it keyed by its code and the values of the skeleton items it reads, and only there. Nothing is computed at import.
- M4 Sizes are round numbers or catalogue values, stored as named inputs; a calculation is a test that checks them and never writes them into the model.
- M5 A bought part's interfaces (frames, axes, hole patterns) are derived from its STEP by a query that selects by type, axis, radius and position with explicit tolerances and fails unless it finds exactly the expected count; the result is cached by the STEP's hash and the query's code. The model never picks vendor faces by size thresholds, and no size comes from a mesh. The STEP is the maker's or a catalogue's, stored with part number and supplier link (or, where its licence doesn't allow sharing, downloaded from the maker on first build and checked by its sha256) and checked against the maker's own data; one behind a login is asked for, not substituted. A bought part without a maker's CAD gets one model of its own in `library/models/`, built from its datasheet (cited), and exposes its interfaces by name. A standard part (fastener, nut, bearing, circlip) comes from a standard-parts library, and its holes, pockets and lengths are taken from that same part, never from our own tables.
- M6 Why: a component choice or design decision that isn't self-evident carries a `Why(decision, reason, requirements)` in its module's `WHY`, written once, keyed by each part-tree node it concerns. The reason states the constraints that make it right (what must stay fixed, which way each load goes and what carries it, what it beat), never a description of the parts, and no numbers. The build service writes them to `why.json`. Routine choices such as a common screw need none.
- M7 Assemblies: a part only cuts its holes; its assembly adds every screw, insert, nut, bearing and bought part, and declares every mate. A part belongs to what it is mated to: a joint's drive (motor, gears, bearings) is one group under the assembly it moves; otherwise to the part it stays on when taken apart: a nut or insert to the part it is set in, a screw to the part it holds.
- M8 Fastening follows one standard: one screw type, into heat-set inserts, a captive nut only where an insert can't fit; a board's holes take the size they are made for. Outside screws, where unavoidable, are out of sight, one type, flush and symmetric.
- M9 Screw lengths come from one short list, the fewest that fit every joint: engaged the full insert or nut, two threads past a nut, never bottoming or leaving what it joins. A bought part's own screws don't count.
- M10 Bought parts lead: the design is shaped around cheap, documented catalogue parts that normal distributors stock, each used with its real data (catalogue length, maker CAD, real mating frames). If a derived size isn't stocked, change the relation so it lands on one. Custom-made parts only with explicit approval. The bill only adds where to buy the exact modelled part; a substitute is proposed with its STEP, and where the bill and the model disagree, the model is right.
- M11 Every moving part runs for its life with no maintenance.
- M12 Cables: one cable is one object from connector to connector; bends at least 6 × its diameter where it flexes repeatedly and 4 × where it lies loose (CENELEC HD 516); joints crossed by twist through hollow axes where possible; nothing touches a spring.
- M13 Mechanics first: electronics and cables are laid out once the mechanics are stable.
- M14 The model is modelled the way a person would model it in CAD: each part is a few sketches, derives and features, and its code is about as long as its feature list. Code much longer means the design is wrong; fix the design. A change that grows the model adds a capability.
- M15 Each part is its feature tree: one builder, a named step per feature in modelling order — a sketch on the part's own frame or the skeleton, the solid, cuts, standard holes, patterns and mirrors, fillets and chamfers last. An edge is picked by the feature that made it, never searched for.
- M16 Every number in a feature has a source: a design input, a skeleton interface, a standard's or bought part's queried value, a pattern spread over the feature it sits on, or a named constant whose name says what it is. A position is never a constant: it is a relation to what it sits against. A standard part is named by its size (`M3`), and a screw's length follows from what it clamps. One name has one meaning and is defined once; a part never recomputes a skeleton value.
- M17 Fits and printing come from one table: each fit and print allowance is named once and used by name. Every printed part declares how it prints and stays within the table in that orientation. A fastener's hole keeps the minimum wall all round, and every screw, nut and insert lies within the parts it joins.
- M18 Geometry speaks the CAD library: named planes, axes, locations and patterns, no bare coordinates. No maths (trigonometry, vector arithmetic, `math`, numpy, `Vector`) outside `generators/` (each file explicitly approved), `cables/` and the build service's analysis, which never touches CAD. Lint enforces it. Symmetry is a mirror, not a sign; a cut at a plane is a split by it; every value is a named field, never an index; a point, direction or size comes from the feature already there.
- M19 A combination of features used twice is one named feature.
- M20 Nothing is measured to drive a feature: a position or size comes from a skeleton plane, a sketch constraint or a relation, never read back from built geometry. Where a construction has several solutions, the one meant is picked by a named relation, never by query order; a relation raises unless it finds exactly one answer. Every part can be rebuilt 1:1 in a parametric CAD program; vendor parts are read only to mate to them.
- M21 Relations are direct formulas: offsets and ratios of their neighbours. A search or solver runs only offline to pick a number.
- M22 Every load-carrying part stays within its rating under the design's loads: a standard's or datasheet rating, else finite elements in its own material.
- M23 A face that ends inside another cavity ends well inside it or exactly on a face it already has, never near one: shared edges in one sketch, or up to the existing face. Two features never take two references for the same boundary.
- M24 Round features about one axis are one revolved profile on one plane through the axis, their steps lines of one sketch.
- M25 Print support is chosen per cavity: a cavity wider than a bridge prints on supports; a teardrop roof only where support scars would spoil a locating bore. Roofs that must exist share one ceiling plane.
- M26 Every finished part has its edges broken. Edge breaks and design features (fillets, chamfers, ribs) are added by hand, per part, where a designer would put them, each a named feature sized for its place; never an automatic pass over every part.
- M27 No knife edges, no slivers, no blends, lofts or trims piled onto an existing shape. A part that needs strength or smoothness is remodelled simply, as a person would CAD it.
- M29 Simplest assembly: fewest parts and steps, one fastening direction, screws from the service side. Screw a part straight onto what it sits on rather than adding keepers, clamps or brackets.
- M30 Move, then fix: a structural move changes no geometry and is checked identical; each geometry fix is its own commit naming the parts it expects to change, and the check passes only if exactly those changed.

```python
# before: positions computed by hand
pts = [(cx + r * cos(a), cy + r * sin(a)) for a in (30, 150, 270)]

# after: a pattern on a named plane
with Locations(hub.face), PolarLocations(r, count=3, start_angle=30):
    ClearanceHole(screw)
```

---

## Tests
- T1 Every test verifies a requirement (R) or shape rule (S) from the PRD, or a modelling rule (M), and names it; a test that can't is deleted.
- T2 It checks the outcome the rule states, where it's decided (a built and mated part, a command, an output file), never a stand-in, and never by re-deriving the model's own formula; one test per outcome, failing for one reason. Complex logic (a fold, a kinematics computation, a parser) also earns direct unit tests.
- T3 Clearance and interference run on meshes with the tessellation tolerance in the margin; line of sight by rays; an exact boolean only where a volume is itself the requirement.
- T4 Every test is fast: parts come from the cache and the suite runs in under a minute on a warm cache. A check that can't be made fast is a study run on demand.
- Never test the code's shape (source text, signatures, a name's absence), a constant against itself, or a value the code just set; assert the effect, not the configuration. No test mocked past the thing under test; no meta-tests.
- No skips, xfails, accepted reds or allow lists: config refuses skip and xfail (ruff), an empty parametrize and unregistered markers (pytest `strict`). A check that collects nothing fails, never passes.
- Timings are numbers to read, never assertions. Files go under `tmp_path`, no fixed ports; under xdist, surface a value by raising.
- A running suite reads the live source tree: don't edit the model until it reports.
