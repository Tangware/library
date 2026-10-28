# Tanġware CAD library

Mechanical design as code, on build123d: parts mated as in CAD and assembled. The build in the Tanġware studio exports the STEP, GLB and print STLs and runs the checks, simulation, stress and bill. A coding agent takes a product from idea to a priced, buildable design by following `runbooks/`, under the rules in `AGENTS.md`.

Needs git and [uv](https://docs.astral.sh/uv/).

```sh
git clone https://github.com/Tangware/library
cd library/model
uv sync
uv run cad new ../../my-product --name "My product"
```

## Claude Code plugin

`plugin/` lets Claude Code design with this library and drive the Tanġware studio. Install it with:

```sh
claude plugin marketplace add Tangware/library
claude plugin install tangware@tangware
```

## Examples

Each design in `examples/` is a full repo, from `discover/` to `ops/`, with its model in `model/`; build it in the studio.

- `box`: a printed box that holds a Raspberry Pi Pico 2 and sticks to steel by magnets.
- `fan`: a quiet desk fan whose head sweeps side to side on a stepper.
- `pantilt`: a phone stand that pans and tilts to keep a face in frame.
- `dispenser`: a pill dispenser whose carousel gives each dose at its time.
