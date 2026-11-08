# Current release scope

Version 2.0 extends the established DOCX pipeline with project configuration,
practice reports, layout corrections, and post-render checks. PDF remains
experimental in 2.0; its conformance work is deferred beyond this release.


## Design Principle

Use mature document technologies for conversion and custom code only for
dialect control, SSAU semantics, orchestration, validation, and narrow format
gaps. tex2sto is neither a general TeX engine nor a DOCX writer.

## Implemented Pipeline

```text
controlled .tex project
        |
        v
Python include expansion, metadata parsing, validation, and shared numbering
        |
        +--> Pandoc 3.11 --> Lua style filter --> reference.docx
        |                                      |
        |                                      v
        |                       focused python-docx OOXML patches --> DOCX
        |
        +--> SSAU LaTeX class --> LuaLaTeX / TeX Live 2026 --> experimental PDF
```

The renderers share source metadata, labels, citations, validation results, and
numbering decisions. DOCX is the supported release output. The PDF branch remains an
experimental preview until its independent conformance work is completed after release 2.0.

## Component Boundaries

### Python application

`src/tex2sto/cli.py` owns `check` and `build`, exit codes, and CLI options.
`src/tex2sto/mcp_server.py` exposes a local stdio MCP server with a short dialect
guide, a full dialect resource, and a DOCX build tool. The build tool reuses the
same project loader, validator, `BuildOptions`, and renderer orchestration as the
CLI. The packaged dialect resource is kept identical to `docs/dialect.md` by a
test; MCP errors carry the existing diagnostic codes.
`dialect/` performs balanced-argument recognition and safe local `\input`
expansion without attempting to parse arbitrary LaTeX. `model/` stores the
document and builds deterministic object and citation indices. `validation/`
enforces the accepted syntax, metadata, structure, references, and conservative
prose warnings. `transform.py` lowers semantic commands into renderer input.

`\labtitle` is a single preamble declaration with a strict, balanced
`key={value}` grammar and plain-text values. It produces a separate `LabTitle`
model instead of overloading thesis metadata. The presence of that model
selects laboratory structural validation and front matter in both renderers.
`profiles/ssau/lab_title.py` owns the supplied laboratory cover's wording and
layout; common dialect code owns field parsing, multiplicity, and placement.

### DOCX path

Pandoc parses supported prose, headings, lists, tables, images, and math. The
`ssau.lua` filter assigns profile styles and the profile `reference.docx`
supplies A4 setup, margins, fonts, footer, and the `Tex2Sto ...` style family.

Focused Python post-processing adds the title and assignment pages with real
Word paragraphs for logically separate fields, abstract statistics, editable
page fields and contents entries, bookmarks, editable equation rows with
symmetric side columns, Russian list numbering, repeating table rows, and
explicit continuation segments at validated `\tablebreak` points. Soft line
breaks are reserved for structures that must remain within one paragraph, such
as symbol explanations and the two-line appendix heading. Table-grid widths are
balanced from visible cell content before a longtable is split. The processor
patches Pandoc output rather than constructing the package from scratch.

The laboratory cover uses dedicated `Tex2Sto Lab ...` paragraph styles and
separate editable paragraphs for each participant field. Its city/year lives
in the first-page footer so wrapped names and course text do not move it.
The ordinary footer retains continuous page numbering from the second page.
A single break before the first body paragraph avoids an empty page between
the laboratory cover and a leading structural heading. Laboratory front matter
omits the thesis assignment, abstract, and contents.

### Experimental PDF path

LuaLaTeX receives lowered LaTeX directly. `tex2sto-ssau.cls` owns A4 geometry,
typography, structural pages, headings, lists, fixed object placement, longtable
continuations, equations, listings, and page numbering. The PDF path never
round-trips through DOCX or LibreOffice. Its current output is not part of the
v1 compatibility or conformance contract.

### QA-only rendering

LibreOffice is used only to render DOCX during visual QA. Poppler renders and
inspects PDF. Microsoft Word is the priority DOCX consumer and remains the
manual release gate for page and contents fields.

## Repository Shape

```text
src/tex2sto/
  cli.py
  mcp_server.py
  resources/dialect.md
  dialect/
  model/
  validation/
  renderers/
  profiles/ssau/
    pandoc/ssau.lua
    pandoc/reference.docx
    latex/tex2sto-ssau.cls
    toolchain.toml
tests/
examples/master-thesis/
docs/
harness/
Dockerfile
```

Package resources are shipped inside the Python wheel. Generated `build/` and
`dist/` artifacts are not source-controlled.

## Profile Boundary

`ssau` is the only V1 profile. Profile resources own university-specific page
layout and renderer behavior. The current Python validation rules are allowed
to be hardcoded while they are clearly SSAU-derived and covered by the profile
checklist. A general external university-profile schema remains deferred until a second
real standard exposes stable variation points. `tex2sto.toml` is a narrow project
configuration for the existing SSAU renderer, not an arbitrary layout schema.

### Project configuration and practice reports

`config.py` owns immutable validated settings and strict TOML loading. Discovery
uses the master source directory; explicit paths are supported. Defaults are
merged with TOML and then explicit CLI/MCP overrides. Relative configured output
paths use the master directory; explicit CLI/MCP output paths retain their
working-directory semantics. Unknown sections/keys and invalid values are errors.
Build overrides do not mutate a caller's project. Source validation and rendering
receive the same settings object.

The optional combined terminology block is written in the configured position:
before introduction by default, or after conclusion before sources/appendices.
Renderers preserve that position rather than moving source text implicitly.
Table spacing defaults to 1.5. Generated separators default to hyphens; ranges
use en dashes. Em-dash separators require explicit permission. List wrapping
returns to the left margin, while first lines retain the paragraph indent.

`\practicetitle` adds typed practice-specific metadata to the shared metadata.
Common author/institution/program fields remain existing commands. Repeated
`\practiceassignment` commands form a typed competency/outcome/task matrix.
The SSAU practice module owns wording and editable service-page layout. The
matrix has no ordinary body caption or reference and repeats its header when
paginated. This does not weaken validation of ordinary body tables.

### Post-render page checks

`check-pages` and MCP `check_pages` consume an already rendered PDF using
Poppler `pdfinfo`. Optional inclusive minimum/maximum limits produce warnings;
strict mode promotes them. No limits apply by default. The checker neither
renders DOCX nor trusts cached DOCX page properties. The caller must supply a
current rendering and select/extract the desired page scope. LibreOffice stays
outside the production build path.

## Numbering Policy

Figures, tables, and equations choose numbering independently. The default
`auto` mode selects section-local numbering for a type when the document has at
least two sections, that type occurs in at least two sections, and its count is
at least the threshold of 10. Otherwise numbering is global. CLI overrides can
set the common mode, threshold, or per-type mode.

Appendix objects always use appendix-local identifiers. Appendix letters use
the STO-permitted sequence and exclude forbidden Cyrillic letters.

## Toolchain Contract

`src/tex2sto/profiles/ssau/toolchain.toml` pins Pandoc 3.11, TeX Live 2026,
and Python 3.12. Renderer startup rejects incompatible external versions.
`uv.lock` freezes Python dependencies. Docker installs the same pins on the
official TeX Live `medium` multi-architecture image, locked by manifest digest.
The CI gate builds the image, while DOCX construction and visual inspection
remain the release output gates. Native macOS uses the same runtime contract.
