# 05 Make

Release the design, price it, order it, and check the first unit against the model. Ordering tools are not built yet; until they are, do these steps by hand with the files below.

Reads the released commit and its build in the studio. Writes an annotated git tag, `reviews/<date>-<kind>.md`, `ops/quotes/<id>.toml`, `ops/orders/<id>.toml`, `ops/first-article/<order>/`.

## Steps

1. **[person] Concept review.** Show the renders at the rest pose, the bill with unit cost per volume tier, and the unverified list. The person confirms this is the product to make. Record their words in `reviews/<date>-concept.md`. *Why:* the last cheap moment to change the design.

2. **[agent] Release.** On the reviewed commit, with the gate passing, create an annotated tag (`git tag -a v<n>`), its message listing the gate result and the unverified list. Only with the person's yes. *Why:* quotes and orders point at a tag, so what was priced is what gets made.

3. **[agent] Quote.** For each made part: its process and material from the manifest, a quote from at least one partner who makes that process. For each bought line: the catalogue price at the quantity. Write `ops/quotes/<id>.toml`: release tag, quantities, lines, landed cost (parts, shipping, duties), each price with its source. Flag every estimate.

4. **[person] DFM sign-off.** Send the made parts to the chosen partner for a manufacturability review. Each finding becomes a model change through `04-model.md` (failing check first) and a new release, or is accepted in writing. Record it in `reviews/<date>-dfm.md`. No tooling (moulds, dies, fixtures) is paid for before the person signs. *Why:* tooling is the one cost a later change throws away.

5. **[person] Order.** The person accepts a quote and places the orders. Write `ops/orders/<id>.toml`: quote, partner lines, status changes, tracking.

6. **[both] First article.** Before any volume, one unit is built from the release's steps. Write `ops/first-article/<order>/` with the plan (which dimensions, fits and requirements to check, each from the model or the PRD), the measurements, photos and a verdict. A mismatch is a fact: find why the model or the checks missed it, then fix through `04-model.md`. *Why:* the first article is where the model meets the world.

## Gate
- The first article matches the release on every planned check, or each mismatch has a fix released and re-checked.
- The person signs the verdict.
