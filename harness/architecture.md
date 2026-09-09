# Architecture

## Design Principle

Use mature document technologies for their strengths and write custom code only
for dialect control, SSAU-specific behavior, orchestration, validation, and
conversion gaps. tex2sto must not grow into a general TeX engine or a DOCX
writer.

## Tool Responsibilities

### Python

Python owns the CLI, project-root discovery, restricted `\input` expansion,
diagnostics, profile selection, metadata, validation, numbering decisions,
external-process orchestration, and focused OOXML post-processing.

Python must not parse the full LaTeX language. It recognizes the tex2sto
dialect, delegates supported document syntax to Pandoc, and rejects unsupported
raw TeX instead of guessing.

### Pandoc and Lua filters

Pandoc is the primary DOCX conversion engine. Its parsed document model is the
main representation for supported prose, lists, tables, images, citations, and
math on the DOCX path. Lua filters translate tex2sto-specific structures into
Pandoc elements and assign custom Word styles.

A profile-owned `reference.docx` supplies page setup, base typography, and the
`Tex2Sto ...` style family. Pandoc's tested math conversion should produce
native OMML equations.

### Focused OOXML post-processing

Python may patch the generated DOCX where Pandoc cannot reliably express a
required Word behavior. Expected examples include explicit style assignment,
bookmarks or fields, repeating table headers, table-continuation behavior, and
other properties verified by structural tests.

This layer patches a Pandoc-produced document. It does not construct the DOCX
package from scratch.

### LuaLaTeX

LuaLaTeX is the PDF engine. The validated source is rendered with an SSAU-owned
class or package. The PDF path does not round-trip the already-LaTeX source
through Pandoc.

### LibreOffice

LibreOffice is not required to build user outputs. It may be installed in a
development or test image to render DOCX for visual regression checks. Microsoft
Word remains the priority consumer for final DOCX behavior.

## Planned Pipeline

```text
controlled .tex project
        |
        v
Python include resolver and dialect validator
        |
        +--> Pandoc parse/AST --> Lua filters --> reference.docx
        |                                      |
        |                                      v
        |                            focused OOXML patches --> DOCX
        |
        +--> SSAU LaTeX class/package --> LuaLaTeX --> PDF
```

The renderers share source metadata, labels, validation results, and numbering
policy. They own output-specific layout so they can satisfy the same standard
without requiring identical page breaks.

## Planned Repository Shape

The implementation scaffold should use a packaged uv application with the
distribution and import name `tex2sto`:

```text
src/tex2sto/
  cli.py
  dialect/
  model/
  validation/
  renderers/
  profiles/
    ssau/
      pandoc/
      latex/
      reference.docx
tests/
  unit/
  fixtures/
  golden/
```

Directories should be created only when the corresponding implementation or
fixture is added. Do not add empty package trees to imitate this map.

## Profile Boundary

`ssau` is the first profile. Its metadata records STO 02068410-004-2018 and the
2019 edition with Amendment No. 1. Its initial rules may be ordinary Python
constants and profile resources.

Keep profile-owned concerns out of generic orchestration:

- accepted structural elements and required metadata;
- typography, margins, captions, and page-numbering rules;
- title-page resources;
- numbering defaults;
- profile-specific validation rules;
- Pandoc filters, Word styles, and LaTeX class/package resources.

Do not design a universal external profile schema until the SSAU implementation
has exposed real variation points.

## Numbering Policy

Figures, tables, and equations choose numbering independently.

The default mode is `auto`. For a given object type, auto mode selects
section-local numbering when:

- the document contains at least two numbered sections;
- objects of that type occur in at least two numbered sections; and
- the object count is at least the threshold, initially 10.

Otherwise it selects global numbering. The selected mode stays consistent for
that object type throughout the document.

The planned CLI controls are:

- `--numbering auto|global|section` for the common mode;
- `--numbering-threshold N` for the auto threshold;
- `--figure-numbering`, `--table-numbering`, and `--equation-numbering` for
  per-type overrides.

Appendix objects always use appendix-local prefixes such as `А.1` regardless of
the main-document selection.

## CLI Contract

The planned interface is:

```text
tex2sto build document.tex
tex2sto build document.tex -o output --pdf
```

The first form writes DOCX only. `--pdf` adds PDF rather than replacing DOCX.
No command in this section is operational until the packaged application is
implemented and verified.
