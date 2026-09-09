# Validation Strategy

## Compliance Boundary

The validator enforces syntax, structure, references, and layout-related source
rules that can be checked deterministically. It may flag likely prose-level
violations using conservative pattern checks.

It does not judge correctness of claims, academic novelty, choice of technical
terminology, grammatical quality, or requirements that need semantic NLP. Such
requirements remain documented human-review items.

## Diagnostic Model

### Errors

Errors stop the build because a reliable conforming output cannot be produced.
Expected errors include:

- an unknown or forbidden LaTeX command;
- invalid dialect syntax or nesting;
- an `\input` path outside the project root;
- a missing input or asset;
- an include cycle;
- duplicate labels;
- a reference to a missing object;
- a figure without its required caption;
- structurally invalid metadata or document ordering;
- an empty table cell when the SSAU rule requires a dash or explicit value.

### Warnings

Warnings report a probable STO violation with plausible legitimate contexts.
The normal build continues and emits its outputs. Planned warning examples
include:

- `%`, `№`, or a bare mathematical comparison sign in prose;
- a minus sign before a negative value in prose;
- a number from one through nine written as a digit without a unit;
- a potentially breakable space between a number and its unit;
- a non-standard abbreviation;
- a word break in a heading or caption that the renderer may need to prevent.

`--strict` promotes every warning to an error. A narrow, rule-specific local
suppression mechanism is required, but its source syntax is deliberately
deferred until the dialect grammar is designed. Blanket suppression should not
be the default.

All machine-facing diagnostic identifiers and messages are written in English.
Russian user documentation explains their meaning and resolution.

## Test Layers

### Unit tests

Use pytest for include resolution, dialect recognition, label/reference rules,
numbering selection, profile validation, and diagnostic severity. Include both
positive and negative cases for every dialect construct.

### Semantic fixtures

Maintain small `.tex` projects for each supported feature and at least one
representative full document covering the complete v1 structure. Fixtures
should make expected output metadata and numbering explicit.

### DOCX structural tests

Inspect selected OOXML properties instead of snapshotting the entire binary:

- A4 portrait sections and 30/15/20/20 mm margins;
- bottom-centered page numbering and suppressed title-page display;
- explicit `Tex2Sto ...` styles;
- editable OMML equations;
- bookmarks, references, and static display text;
- table header repetition and continuation behavior;
- caption placement and appendix-local numbering;
- 14 pt body text and 12 pt tables and listings.

### Render tests

Render DOCX through LibreOffice for development-time visual QA while treating
Microsoft Word as the priority consumer. Render PDF pages with Poppler. Check
representative and boundary pages for clipping, overlap, font substitution,
caption separation, table splitting, page numbering, and unexpected blank
pages.

DOCX and PDF golden checks are independent. A page-count difference is not a
failure by itself.

### Manual release checks

Before claiming Word compatibility for a release, open the representative
document in a supported current Microsoft Word for macOS build and verify
styles, editability, fields, equations, table continuation, and pagination.

## Dependency Upgrade Gate

Pandoc and TeX Live are pinned in the Docker image. An upgrade is an explicit
change that must:

1. update the recorded versions and lock material;
2. run all unit and semantic fixtures;
3. run DOCX structural checks;
4. regenerate and inspect DOCX and PDF golden renders;
5. receive the manual Word compatibility check when DOCX output changed;
6. record intentional output differences.

## Planned Python Checks

Python 3.12+, uv, pytest, and Ruff are confirmed choices. No dedicated type
checker is planned. Do not add commands to this document until `pyproject.toml`
exists and those commands have been executed successfully.
