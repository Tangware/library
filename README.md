# Tanġware CAD library

Mechanical design as code, on build123d: parts mated as in CAD and assembled. The build in the Tanġware studio exports the STEP, GLB and print STLs and runs the checks, simulation, stress and bill. A coding agent takes a product from idea to a priced, buildable design by following `runbooks/`, under the rules in `AGENTS.md`.

Needs git and [uv](https://docs.astral.sh/uv/).

```sh
uvx --from tangware==0.1.1 cad new my-product --name "My product"
```

## Claude Code plugin

`plugin/` lets Claude Code design with this library and drive the Tanġware studio. Install it with:

```sh
claude plugin marketplace add Tangware/library
claude plugin install tangware@tangware
```

## Examples

Each design in `examples/` is a full repo with its model in `model/`; build it in the studio.

- `box`: a printed box that holds a Raspberry Pi Pico 2 and sticks to steel by magnets.
- `fan`: a quiet desk fan whose head sweeps side to side on a stepper.
- `pantilt`: a phone stand that pans and tilts to keep a face in frame.
- `dispenser`: a pill dispenser whose carousel gives each dose at its time.
- `strandbeest`: Theo Jansen's walking linkage, twelve printed legs on one crank.
- `v8`: a one-third scale Chevrolet small-block 350 with a working valvetrain.
- `cessna`: the retracting main landing gear of a Cessna 337 at one-sixth scale.
- `octopus`: a desk robot with eight arms, each on its own gearmotor.
