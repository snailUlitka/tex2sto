# Roadmap

## Current State

V1 is implemented end to end. The uv-managed CLI validates the controlled
dialect, creates a styled editable DOCX by default, optionally creates an
independent PDF, and includes a complete representative project. The Pandoc and
TeX Live renderers, profile resources, Docker definition, tests, and Russian
user documentation are present.

## Completed V1 Work

- packaged Python 3.12.11 application with `check` and `build`;
- safe multi-file loading and strict unknown-syntax rejection;
- metadata, title, assignment, abstract, contents, main structure, and page
  numbering;
- paragraphs, nested STO lists, figures, tables, long tables, equations,
  definitions, abbreviations, bibliography, citations, appendices, and code;
- shared global/section/auto numbering and appendix-local numbering;
- editable DOCX styles, OMML, fields, bookmarks, and repeating table headers;
- independent LuaLaTeX PDF with longtable continuation heads;
- conservative warnings, strict mode, and narrow local suppression;
- structural tests, full example builds, and visual QA entry points;
- pinned Docker and native macOS workflows;
- Russian installation, CLI, dialect, and example documentation.

## Resolved Baselines

- The master-level title page and two assignment variants use the reviewed
  template as supporting evidence and the STO checklist as authority.
- Pandoc 3.11, TeX Live 2026, Python 3.12.11, and uv 0.12.x are pinned.
- Bibliography records use five in-source fields and first-citation order.
- Warning suppression is a next-content-line comment with explicit codes.
- Editable Word table continuations use validated explicit `\tablebreak`
  segments because repeated header rows do not reevaluate fields; PDF uses
  native `longtable` continuation heads.
- Automatic object numbering switches at ten objects only when at least two
  sections contain that object type.
- Containers fall back to Cyrillic-capable Liberation Serif with Times-compatible
  metrics when licensed Times New Roman is not available; normative PDF
  production still requires Times New Roman.

## DOCX Acceptance Backlog

The following corrections were captured from the first generated-DOCX review
on 2026-09-11. They are deliberately deferred: this section records acceptance
criteria only and does not describe current renderer behavior.

### Structure and contents

- Render structural-element entries in the table of contents in sentence case,
  including `Введение`, `Заключение`, and `Приложение А`, rather than copying the
  uppercase page heading.
- Eliminate `?` placeholders from table-of-contents page references. A DOCX
  opened in current Microsoft Word and updated with `Ctrl+A`, `F9` must show the
  resolved page number for every entry; automatic update-on-open should remain
  enabled.
- Treat definitions, terms, symbols, and abbreviations as one optional
  structural element rather than two adjacent structural sections. Consolidate
  their entries under one centered structural heading; confirm the canonical
  heading text against the STO when implementing the dialect migration.
- Treat the introduction as a structural element and center its page heading.
- Render all numbered headings and structural-element headings in regular type:
  neither bold nor italic.
- Separate every hierarchical heading number from its title with one
  non-breaking, non-expanding space, not a tab.
- Apply a 1.25 cm first-line indent to every ordinary body paragraph regardless
  of the surrounding section level. Keep explicit exceptions for headings,
  captions, equations, tables, lists, and code rather than inheriting a missing
  indent accidentally.

### Lists and positioned content

- Use the literal hyphen-minus marker `-` for the first unordered-list level,
  not an en dash, em dash, or another dash glyph.
- Separate every list marker or enumerator from its content with one
  non-breaking, non-expanding space (U+00A0), not a tab. Preserve the same rule
  for nested alphabetic and numeric levels.
- Center the figure content itself as well as its caption.
- Left-align code-listing lines; do not justify or center them.
- Left-align `Продолжение таблицы N` exactly like `Таблица N — Название`, with
  no first-line indent.

### Equations and appendices

- For a numbered display equation, keep the editable equation visually centered
  on the text area and place `(N)` at the right edge on the same line without
  allowing the number to shift the equation away from the true center.
- Place the symbol explanation immediately below the equation. Start the first
  definition with `где` and no colon, put each subsequent symbol on a new line,
  use an em dash between the symbol and its explanation, end intermediate
  definitions with commas, and end the final definition with a period.
- Render the appendix designator and title as one paragraph separated by a
  manual line break: `ПРИЛОЖЕНИЕ А`, then the mixed-case title on the next line.
  Do not create a second paragraph or paragraph-spacing gap between them.

### Bibliography

- Use the supplied expanded bibliography example as supporting evidence for a
  representative fixture set, not as an instruction source or a replacement
  for the normative bibliography standard.
- Extend the bibliography model and formatter to cover at least institutional
  and personal-author web resources, official and legal web documents, journal
  articles with multiple authors, books and chapters, conference publications,
  datasets, and preprints.
- Preserve first-citation ordering and no-period Arabic entry numbers while
  supporting the evidence shown by those fixtures: `[Текст]` and
  `[Электронный ресурс]`, author and contributor groups, container title,
  publication place and publisher, year, issue, page range or total extent,
  URL, and access date.
- Reconcile punctuation and separators with the normative bibliography standard
  during implementation instead of copying inconsistent dash and slash usage
  from the example document.

Each mechanical correction above requires a focused regression fixture and a
rendered DOCX inspection before it can be removed from this backlog. The source
DOCX and screenshots remain machine-local review evidence and must not be
committed to the repository.

## Release Readiness Work

- add CI after the hosting platform and secret policy are chosen;
- choose the license and publish packaged release artifacts;
- add signed or checksummed container publication if distribution requires it.

## Later Work

- incorporate the additional bibliography STO and complete the bibliography
  backlog above;
- add more SSAU title-page variants;
- add table notes and other structures only with normative fixtures;
- study a second university standard and extract proven profile variation
  points;
- support other universities without weakening the strict dialect contract;
- consider landscape pages, SVG, TikZ, and numbered algorithms as explicitly
  versioned dialect additions.
