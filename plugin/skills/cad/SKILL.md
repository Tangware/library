---
name: cad
description: Designs a physical product as code with the Tangware CAD library. Use when the person wants to make, design or change a hardware product, or works in a design repo made by `cad new`.
---

`cad` runs the library: inside a design repo, the version its `model/` pins; elsewhere, the `tangware` release on PyPI this plugin pins. Its first run downloads the library's Python packages, which takes about 2 min. A new product starts with `cad new <dir> --name "<product name>"`, which makes it depend on the release that ran it; the new repo's `AGENTS.md` says what to read next. Build it in the studio, which runs every check.
