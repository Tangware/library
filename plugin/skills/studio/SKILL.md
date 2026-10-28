---
name: studio
description: Drives the Tanġware studio the person has open in their browser, showing what you talk about. Use for every answer about something the studio shows (a requirement, constraint, design idea, part, check, bill line, board, recording, shot, test, quote or commit), and to give the first tour of the studio.
---

The studio is a read-only view of this repo at one commit. You drive it: open a page, select something, and spotlight it with a short caption, while you answer in the terminal. Show something whenever your answer is about something visible, without being asked. The person clicks anywhere in the studio to take over.

## The hosted studio

For https://tangware.com/studio, run `tangware login` once on this machine: it opens the browser to confirm a code. Once the repo is on GitHub (`gh repo create --private --source . --push`), `tangware link`, run in the design's folder (the repo's root, or a folder such as `hardware/`), makes it a project, asking GitHub for access to this one repo if needed, and opens it in the studio.

After the person presses Build in the studio, run `tangware build`, then fix what it reports. If it says the build is still running, wait a little and run it again. Only the person starts builds.

## show.sh

```sh
show.sh go <page> [--select <id>] [--highlight <id or CSS selector>] [--title <text>] [--caption <text>] [--commit <sha>]
```

- `--select` clicks the item so its details open. `--highlight` spotlights something else; without it the selected item is spotlighted.
- `--caption` is one short plain line. The full answer goes in the terminal.
- A page is one of the seven pages, such as `engineering`; `--select` picks a thing on it. Highlight `.insp` to spotlight what it opened.
- When an answer is about a check, show the check (it highlights the parts it involves), then its part (`go engineering --select <item id>`).
- Calls run in order, one spotlight at a time. If it prints that no studio page is open, answer in the terminal only.

```sh
show.sh go design --select <the chosen concept's node id> --caption "The chosen concept, as it was generated."
show.sh go engineering --select <a part's item id> --highlight .insp --caption "<what the part is and what it does>."
show.sh go engineering --select check:<id> --highlight .insp --caption "R8 fails: the landed cost is over the target."
```

## The studio's map

Run `show.sh map` for the seven pages and the ids each one can select at this commit.

## The first tour

Offer it at the start. When the person accepts, give one step at a time: run the `show.sh` call, then say the lines in the terminal, adapting the facts to this repo. Wait for them before the next step. Skip a step whose page has nothing at this commit. Fill each `<…>` from the repo.

1. `show.sh go spec --select <a requirement id, such as R1> --highlight .insp --caption "What the product must do, in the founder's words."`
   Say: everything starts from what the person said they want. Each requirement is an outcome, traced to the founder's own words (▸) and to the checks that prove it.
2. `show.sh go spec --select constraint:<a constraint id> --caption "Real constraints, and what drives what."`
   Say: the constraints come from physics, the requirements, cost and the person. The lines show which one drives which, so every later decision can be traced back.
3. `show.sh go design --select <the chosen concept's node id> --caption "The concept that was chosen."`
   Say: every mechanism and concept is on one tree, and the thick line is the path the founder chose. Name the chosen concept and why, from its `why`.
4. `show.sh go design --select <a rejected concept's node id> --caption "Rejected, with its reason."`
   Say: rejected ideas stay on the tree, dashed, with what killed them. Give this one's reason in a sentence.
5. `show.sh go engineering --select <the main part's item id> --highlight .insp --caption "The real product, built from code at this commit."`
   Say: pressing Build turns any commit into the CAD. Tapping a part shows its Why, its bill line and the checks that cover it. Say what this part is for.
6. `show.sh go engineering --select <a module, as module:<ref>> --highlight .canvas --caption "Every module, wire and power rail."`
   Say: the electrical plan is checked for errors before a board exists.
7. `show.sh go engineering --select check:<a failing check's id, or the first check's> --highlight .insp --caption "<what it checks, and its verdict>."`
   Say: each check says what it covers and what it doesn't catch. If one fails, say why in plain words.
8. `show.sh go media --highlight .shot-card --caption "Shots rendered from the same model."`
   Say: promotional shots are plain scripts run on request; framing and motion are approved before render time is spent.
9. `show.sh go marketing --select price --highlight .insp --caption "Tested before tooling."`
   Say: each campaign puts one question to people, its variants read against a go line, and the decision links to what it changed in the spec, design or engineering.
10. `show.sh go production --select quotes --highlight .card --caption "A quote you can order."`
    Say: a fixed price for a release, from the model and the partners' price tables.
11. `show.sh go home --select rounds --highlight ".commits li" --caption "Every commit is a version."`
    Say: any point can be reopened, and any two can be compared: geometry, bill, cost and checks. End by asking what they'd like to look at.

## Rules

- Answer from the repo. If it doesn't cover the question, say so.
- The studio is read-only. If the person asks for a change, say what you would change, and make it only when they confirm here.
