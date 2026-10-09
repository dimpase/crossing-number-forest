# Editing this forest

Read README.md, writing-brief.txt, and the affected canonical trees. This is
a reading project for the pinned crossing-number paper and its Lean sources.
Focus on explaining the new proof; older work belongs in the bibliography
and brief context, unless the user requests a detailed comparison.

## Writing and addresses

- Preserve allocated `cn-NNNN` addresses. One canonical addressed note per
  `.tree` file. Do not rename notes when their titles change.
- Give reusable definitions `\taxon{Definition}`, `\tag{definition}`, and
  `\meta{defines}{term; aliases}`. Emphasize the defined term and include the
  note in the definition index. Cite definitions at substantive first uses,
  in statements, and where proof steps rely on them.
- Keep full proofs reachable from statements. Assemble reading accounts by
  transclusion, editing canonical notes rather than duplicating arguments.
- Leave blank lines before and after `\p{...}` blocks in tree sources.
- Every note needs title, taxon, dependencies, and provenance. Dependencies
  are logical prerequisites, not every link or bibliographic citation.
  Keep dependency and transclusion graphs acyclic; ordinary reciprocal links
  are allowed. Use `None.` for empty dependency metadata.
- Results need a visible Statement and Proof. The `proof-account` status
  means a reconstruction of the supplied proof, not a locally compiled Lean
  proof. Use `computational-evidence` for finite examples and explicitly
  describe what they establish. Never upgrade status solely because a build
  or finite computation passes.
- Reference entries have their own tags and `Reference` taxon; collect them
  in cn-0041. Retain precise theorem/section locators at citations.
- Use plain explanatory prose, explicit hypotheses and quantifiers, and
  connecting paragraphs that explain why each step is needed.
- In the algebraic branch, call P: R -> W a univariate polynomial map.
  W is its ambient value space. Distinguish coordinates of W from monomial
  degrees in each scalar coordinate polynomial; avoid calling W a space
  of coefficient vectors, which suggests coefficients of a scalar polynomial.
- For printed TeX equation numbers, escape Forester's metadata command:
  `\startverb\tag{2.1}\stopverb` inside the display.

## Mathematical and source integrity

- Count ordinary crossing points, including repeated crossings of an edge
  pair. Do not substitute pair-crossing or parity counts.
- Adjacent-edge crossings are removed by normalization, not excluded in the
  initial admissible-drawing definition.
- Retain endpoint half-order corrections and shared-spoke averaging in the
  cycle pairing. Diagonal off-star entries are killed by the detector.
- The detector uses one fixed node tuple for all orders. Its images need
  full rank, not positive semidefiniteness. Preserve ordered-pair counting
  and the factor two in the lower bound.
- Preserve the degree-index shift between the paper and Lean, and distinguish
  the challenge's placeholder from the solution's import closure.
- Archived files in source-material/openai-math are immutable snapshots of
  commit fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb. Record any new upstream
  version separately, with hashes and source mappings. Do not rewrite the
  archived paper, bibliography, or Lean code during editorial corrections.
- The current Lean check is static source inspection. Never describe it as
  elaboration, kernel checking, an axiom audit, or Comparator verification.
  If those are run later, record commands, versions, outputs, and scope.

## Environment and validation

- Reuse the explicit `4ary-4tics-forester-5.0` switch; do not change the global
  opam switch. Keep the theme at the pinned revision and put local changes in
  assets/project.xsl and assets/project.css.
- Run `make check` after edits and inspect the affected rendered reading
  paths. For mathematical changes, separately review the argument.
- Serve only output/ on localhost, normally port 8001. Do not disturb the
  existing 4ary forest's server on port 8000.
- Commit coherent source changes after validation. Do not publish or add a
  remote for this project unless requested.
