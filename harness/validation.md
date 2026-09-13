# Validation Strategy

## Compliance Boundary

The validator enforces syntax, metadata, structure, references, source order,
and layout-related rules that are deterministic before rendering. Conservative
warnings flag prose patterns with plausible legitimate exceptions.

The program does not judge claims, novelty, terminology, grammar, or other
semantic writing requirements. Those remain human-review items.

## Diagnostics

Errors stop a build. Implemented error families cover unknown syntax, math
commands outside math, unsafe or cyclic `\input`, missing assets, metadata,
structural order, heading form, duplicate or unresolved references, object
labels and first references, table headers and empty cells, appendix order,
symbol-explanation placement, and kind-specific structured bibliography fields.

Warnings cover abstract length, unused sources, and conservative prose patterns:
detached signs, numeric minus, digits one through nine without a unit, breakable
number-unit spaces, and decimal points in Russian prose. `--strict` promotes
warnings to errors. `% tex2sto: ignore=CODE[,CODE]` suppresses listed warnings
only on the next non-comment content line.

All developer diagnostics are English and carry stable `T2S-E...` or
`T2S-W...` identifiers.

## Automated Checks

Run from the repository root:

```sh
uv run ruff check .
uv run pytest
uv run tex2sto check examples/master-thesis/main.tex --strict
uv run tex2sto build examples/master-thesis/main.tex -o build/example
uv build
docker build --platform linux/amd64 -t tex2sto:ci .
git diff --check
```

The pytest suite includes positive and negative dialect fixtures, numbering and
transformation checks, real DOCX construction, OOXML assertions, and preliminary
PDF construction checks. Tests requiring an external renderer skip when that
renderer is absent. Mandatory PDF renderer coverage in CI is deferred to v2;
the v1 CI release gate must build the Docker image successfully.

## Structural Output Gates

DOCX tests inspect selected OOXML rather than snapshotting the binary:

- A4 portrait page size and 30/15/20/20 mm margins;
- explicit `Tex2Sto ...` styles and editable body structures;
- real paragraphs for title details and assignment fields, with soft line breaks
  limited to intentionally single-paragraph structures;
- native OMML equations with profile numbering;
- bookmarks and `NUMPAGES`/`PAGEREF` fields;
- Russian list formats;
- media relationships;
- content-weighted table-grid widths;
- separate longtable segments, explicit page breaks, repeating headers, and
  visible continuation labels without renderer markers.

Existing PDF tests verify a real PDF header, A4 dimensions, selected structural
content, appendices, and longtable continuation text. They exercise the preview
implementation but are not a v1 release gate.

## Visual and Manual Gates

After DOCX renderer changes, render DOCX with the workspace `render_docx.py`
helper. Inspect all pages of the representative example, with special attention
to title and assignment pages, contents, section page breaks, float order,
equations, split tables, bibliography, and appendices.

Before claiming a release compatible with Word, open the representative DOCX
in a current Microsoft Word for macOS build, update all fields, and verify
styles, editability, contents, equation layout, explicit table continuations,
and pagination. The V1 representative document passed this gate after replacing
the non-working repeated-row conditional field with explicit table segments.

## Dependency Upgrade Gate

Pandoc, TeX Live, Python, uv, and Python dependencies are pinned. A v1 dependency
upgrade must update version records and lock material, pass every automated
command, regenerate and inspect the DOCX, receive Word field verification when
DOCX changes, and record intentional output differences. PDF visual and CI
upgrade gates become mandatory in v2.
