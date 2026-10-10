# Crossing-number forest

A local Forester reading project for OpenAI's *The crossing number of
complete bipartite graphs* (23 September 2026), with a guide to its Lean
development. It follows the linked-definition and proof style of the existing
4ary forest. The focus is the new argument; older work appears as context
and in the bibliography.

## Run it

No opam activation commands are needed. The Makefile explicitly selects the
already installed `4ary-4tics-forester-5.0` switch: OCaml 5.3.0, Forester 5.0.

```sh
cd /home/dima/work/papers/4ary/crossing-number-forest
make check
make serve
```

Open **http://127.0.0.1:8001/index/index.html**. This is a separate server from
the 4ary forest on port 8000. Stop it with Ctrl-C. If it is already running,
edit a source, run `make check` in another terminal, and refresh the page.
There is no file watcher. Use `make serve PORT=8002` if another process uses
8001.

If the server runs on a remote host, forward its port from your browser's
computer, for example:

```sh
ssh -N -L 8001:127.0.0.1:8001 dima@tarski
```

Then use the same localhost URL. The server binds only to localhost and
serves only generated output/.

## Reading routes

There are 71 trees: the landing page and cn-0001 through cn-0070, including
21 tagged definitions and 19 bibliographic entries. Next unused: cn-0071.

- cn-0001: guided reading; cn-0007: main theorem and proof assembly.
- cn-0070: rewritten proof introduction, beginning with the paper's equation
  (1.2), with explicit notation and links to definitions and full arguments.
- cn-0061: algebraic branch, from polynomial constraints to the rank sum.
- cn-0060: topological branch, from normalization to the block relation.
- cn-0062: detector branch, including two-triangle interpolation.
- cn-0035–0037: odd lower bound, axis upper bound, even-size deletion.
- cn-0040: an exact four-by-four detector and its determinant.
- cn-0038: paper-to-Lean route and notation differences.
- cn-0039: source versions and verification scope; cn-0041: references.
- cn-0065: an editorial extension of the algebraic inequality to arbitrary
  fields, and the distinction between interpolation maps and drawing arcs.
- cn-0066: independent crossing counts; cn-0009 and cn-0035 explain why the
  normalization and lower-bound arguments do not establish a bound for this
  different count. cn-0067 records the July 2026 survey's open question.

The label `proof-account` identifies an exposition of the supplied proof.
The local checks do not establish a successful Lean or Comparator run.
See AGENTS.md and writing-brief.txt for editorial conventions, including
blank lines between paragraph blocks in the native sources.

## Files and source preservation

Edit trees/*.tree. Longer accounts transclude canonical notes. The project
uses stable cn tags, visible proof dependencies/provenance, and an indexed
definition for each reusable concept. output/ is regenerated; do not edit it.

source-material/openai-math contains 362 archived files: the paper PDF and
complete LaTeX source, all 339 Crossing Lean modules, and selected repository,
challenge, and build metadata. The snapshot is pinned to commit
`fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb`. Each archived file has a SHA-256
entry in source-material/manifest.json. The upstream license is preserved.
The source subset contains all project modules imported by Crossing.Main;
Mathlib, Lean binaries, and unrelated OAI files are not vendored.

source-material/references preserves the 2012 *Adjacent Crossings Do Matter*
paper and the ninth edition (17 July 2026) of Schaefer's crossing-number
survey. Their versions and SHA-256 hashes are recorded in the same manifest.

source-map.json connects paper locations to notes. lean-map.json connects
key paper results to actual source declarations. computations/ stores the
exact example script, results, static Lean audit, and its checker.

## Build and checks

| Command | Purpose |
| --- | --- |
| `make setup` | Verify the pinned environment; recreate its switch from the export if missing. |
| `make build` | Check sources, compile Forester, apply XSLT locally, and check HTML links. |
| `make check` | Build, then recompute exact examples and the static Lean source audit. |
| `make serve` | Build and serve output/ on localhost, port 8001 by default. |

The exact checks cover detector ranks, cancellation and factorizations for all
orders when n=3 or 5, four specified orders when n=7, and arithmetic identities
through 30. They illustrate the argument; they are not a general proof.

The static Lean check records the 339-module import closure, scans uncommented
proof sources for placeholders and additional axiom declarations, compares
ten shared challenge/solution definitions textually, and checks the curated
declaration map. The challenge's one `sorry` is intentional: its theorem is
the target for comparison against the separate solution. There are no such
placeholders in the inspected proof-source closure. A source scan is not a
kernel axiom audit. Lean and Comparator were not run locally.

## Restoration

The theme is the same pinned Forester 5.0 submodule as in the 4ary forest.
environment.json, opam-switch.export, and opam-packages.txt record the
environment. A new machine needs opam, Git, Make, Python and requirements.txt;
initialize opam, restore the theme with `git submodule update --init -- theme`,
then run `make setup`. Installing missing dependencies requires network access.
Routine reading and building use local assets and fonts.

An optional Python environment can be created with:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
make check PYTHON=.venv/bin/python
```

To restore Forester into a different switch without changing the global one,
use `make setup FORESTER_SWITCH=crossing-forester-restored`, then use that
same variable for build/check/serve. The setup refuses to overwrite an
incompatible existing switch.

## Lean verification later

Forester does not need Lean. The source archive is a reading snapshot, not
a provisioned Lean workspace. It records Lean 4.34.1 and Mathlib commit
`d13f23b723b8a846827a245b89c10fc7d3f11612`. To perform a full check, obtain the
upstream repository at the recorded commit and follow its Lean and Comparator
READMEs, using ComparatorChallenges/BipartiteCrossing.json as the configuration.
The upstream library is large; its README recommends building only needed
parts. No compilation of that library is part of `make check` here.
