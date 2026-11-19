# Version 2.1 release record

## Scope

The user requested a minor release for the formula corrections. Version 2.1.0
adds `T2S-W401` for dotted multiplication and indents every symbol-explanation
line after the first by 1.25 cm. Juxtaposition and `×` remain accepted. The
warning retains normal/strict behavior and next-line suppression. There is no
automatic substitution of mathematical operators.

The existing dialect and configuration resource URIs remain at `v2`. Python,
Pandoc, TeX Live, and locked third-party dependencies retain their versions.
DOCX is the supported release output; PDF remains an experimental preview.

## Validation and publication

The 2026-11-17 implementation evidence in [release-2.0.md](release-2.0.md)
includes visual review and supplementary tests on the installed Pandoc 3.12.1.
That evidence is not a replacement for the pinned 3.11 release gate.

The release CI runs the DOCX tests and builds all three examples in the pinned
linux/amd64 image. It retains the wheel, source distribution, and DOCX examples
as a commit-scoped verification artifact. The optional PDF construction test
is excluded from this DOCX release gate, as established by the product scope.

Release assets are the wheel, source distribution, and `SHA256SUMS`. A GitHub
draft may be prepared before all gates finish; publication remains a separate
action.

## Acceptance evidence, 2026-11-17

- [CI run 44139140638](https://github.com/snailUlitka/tex2sto/actions/runs/44139140638)
  passed for release code commit `313a19b`. The pinned linux/amd64 image built
  successfully with Python 3.12.11, Pandoc 3.11, and TeX Live 2026. All 158 DOCX
  gate tests passed; only the optional PDF construction test was deselected.
  Ruff, the frozen lock check, package construction, and strict checks and
  DOCX builds for all three examples passed.
- The CI wheel and source archive both declare version 2.1.0. The wheel's
  dialect resource matches `docs/dialect.md`. All three example DOCX files
  contain the 709-twip left and hanging indents for `Tex2Sto Symbols`, and the
  thesis equations remain native OMML.
- The bundled DOCX renderer produced 13 thesis pages, two laboratory pages,
  and 14 practice pages from the pinned CI outputs. Every page was inspected.
  The thesis explanation starts at the margin and indents subsequent lines;
  contents, table continuations, covers, and pagination show no new defects.
  The additional no-variant cover and wrapped-explanation visual checks are
  recorded in [release-2.0.md](release-2.0.md).
- Current Word verification remains open. A fresh CI document was selected in
  Word for macOS, but the application did not open it and subsequent native UI
  calls repeatedly timed out. Field updates, Word pagination, and editing were
  not verified for this release. Complete the Word gate in
  [validation.md](validation.md) before publication or a new Word compatibility
  claim; the older release's result does not substitute for this check.

The prepared release is [PR 2](https://github.com/snailUlitka/tex2sto/pull/2)
and an unpublished GitHub draft for `v2.1.0`. Only release-related changes are
included; the pre-existing local `.gitignore` edit is excluded.
