# Architecture

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
        +--> SSAU LaTeX class --> LuaLaTeX / TeX Live 2026 --> PDF
```

The renderers share source metadata, labels, citations, validation results, and
numbering decisions. They own output-specific layout and may paginate
differently.

## Component Boundaries

### Python application

`src/tex2sto/cli.py` owns `check` and `build`, exit codes, and CLI options.
`dialect/` performs balanced-argument recognition and safe local `\input`
expansion without attempting to parse arbitrary LaTeX. `model/` stores the
document and builds deterministic object and citation indices. `validation/`
enforces the accepted syntax, metadata, structure, references, and conservative
prose warnings. `transform.py` lowers semantic commands into renderer input.

### DOCX path

Pandoc parses supported prose, headings, lists, tables, images, and math. The
`ssau.lua` filter assigns profile styles and the profile `reference.docx`
supplies A4 setup, margins, fonts, footer, and the `Tex2Sto ...` style family.

Focused Python post-processing adds the title and assignment pages, abstract
statistics, editable page fields and contents entries, bookmarks, right-aligned
equation numbers, Russian list numbering, repeating table rows, and conditional
continuation labels. It patches Pandoc output rather than constructing the
package from scratch.

### PDF path

LuaLaTeX receives lowered LaTeX directly. `tex2sto-ssau.cls` owns A4 geometry,
typography, structural pages, headings, lists, fixed object placement, longtable
continuations, equations, listings, and page numbering. The PDF path never
round-trips through DOCX or LibreOffice.

### QA-only rendering

LibreOffice is used only to render DOCX during visual QA. Poppler renders and
inspects PDF. Microsoft Word is the priority DOCX consumer and remains the
manual release gate for nested field behavior.

## Repository Shape

```text
src/tex2sto/
  cli.py
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
checklist. A general external profile schema remains deferred until a second
real standard exposes stable variation points.

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
`uv.lock` freezes Python dependencies. Docker installs the same pins and native
macOS uses the same runtime contract.
