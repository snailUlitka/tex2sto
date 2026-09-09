# Product Scope

## Goal

tex2sto lets a student author an academic document in a controlled LaTeX
dialect and produce an editable DOCX and, optionally, a PDF that independently
conform to Samara University STO 02068410-004-2018.

The product should automate every encoded and mechanically verifiable rule.
Claims about meaning, terminology, novelty, or writing quality remain subject
to human review. The project must make that boundary visible rather than imply
that a formatter can certify semantic compliance.

## Intended Users

The initial user is a Samara University student who prefers LaTeX authoring but
must submit a Word document. The dialect and CLI documentation are therefore
user-facing, Russian-language products, not internal implementation notes.

## First Meaningful Deliverable

The first end-to-end deliverable is a packaged CLI that accepts one master-level
SSAU document written in the supported dialect and produces a styled, editable
DOCX by default. The same source can additionally produce a conforming PDF with
`--pdf`.

## V1 Document Scope

V1 supports these constructs, with the author selecting which optional
structural elements are present:

- a master-level title page;
- an assignment page;
- an abstract, including document statistics and keywords;
- a table of contents;
- an introduction, numbered sections, subsections, items, and subitems;
- paragraphs and nested lists;
- figures with required captions and references;
- tables, including tables that continue across pages;
- editable equations, explanations of symbols, numbering, and references;
- definitions, symbols, and abbreviations;
- a conclusion;
- a basic structured bibliography and citations;
- appendices with appendix-local numbering;
- code listings, normally placed in appendices.

Detailed bibliography rules from the additional university standard are
deferred, but the v1 source format stores structured bibliography fields inside
the `.tex` project rather than using a `.bib` file.

## Output Contract

- DOCX is the default and priority output.
- PDF is opt-in through `--pdf`.
- `-o` selects the output directory.
- DOCX remains editable. Native Word content is preferred over rendered images,
  including native OMML equations through the tested Pandoc path.
- Static table-of-contents entries, captions, and cross-reference display text
  are acceptable, provided semantic Word styles and navigation structures are
  applied where practical.
- Every semantic DOCX element uses an explicit custom style in the
  `Tex2Sto ...` family.
- DOCX and PDF need not have identical pagination. Each output must satisfy the
  applicable SSAU profile independently.

## Authoring Contract

- Input is a documented tex2sto dialect, not arbitrary LaTeX.
- The dialect may add purpose-specific commands for document metadata and
  structures.
- Unknown commands are build errors.
- Arbitrary visual-formatting commands such as `\textbf` and `\underline` are
  not accepted merely because standard LaTeX accepts them. The profile owns
  presentation.
- A restricted `\input{...}` form is supported for multi-file projects. It may
  resolve only inside the project root and must detect missing files and cycles.
- User documentation must describe every accepted command and its constraints.

## Presentation Decisions

- Body text uses 14 pt Times New Roman.
- Tables and code listings use 12 pt Times New Roman.
- Only portrait pages are in v1.
- Figures require captions. SVG and TikZ input are not in v1.
- Code listings have no separate known STO layout beyond being readable and at
  least 12 pt; the v1 default is 12 pt.
- Numbered algorithm environments are not in v1.
- Appendix labels use `Приложение А` in the table of contents and
  `ПРИЛОЖЕНИЕ А` on the appendix page.

## Platform and Distribution Decisions

- Docker is the primary reproducible environment.
- Native macOS is required and uses Homebrew for external dependencies.
- Homebrew is not used inside the Linux Docker image.
- Python 3.12 or newer is the planned application runtime.
- uv is the planned Python project and dependency manager.
- pytest and Ruff are planned. There is no dedicated mypy or pyright step;
  Ruff provides linting and lightweight static checks but is not represented as
  a full type checker.
- Pandoc and TeX Live versions are pinned. Upgrades are explicit maintenance
  operations guarded by regression tests.

## Explicit Non-goals for V1

- accepting or rendering arbitrary LaTeX;
- semantic or NLP review of academic prose;
- page-identical DOCX and PDF output;
- a general declarative schema for arbitrary universities;
- title pages other than the initial master-level variant;
- landscape pages;
- SVG or TikZ rendering;
- numbered algorithm environments;
- production dependence on LibreOffice.

The initial SSAU implementation is intentionally hardcoded behind a profile
boundary. A general profile format is a later design problem informed by the
working implementation, not a prerequisite for v1.
