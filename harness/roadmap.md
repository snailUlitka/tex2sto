# Roadmap

## Current State

V1 targets the editable DOCX path. The uv-managed CLI validates the controlled
dialect, creates a styled editable DOCX, and includes a complete representative
project. The Pandoc renderer, profile resources, Docker definition, tests, and
Russian user documentation are present. The implemented PDF path remains an
experimental preview until v2.

## Completed V1 Work

- packaged Python 3.12.11 application with `check` and `build`;
- safe multi-file loading and strict unknown-syntax rejection;
- metadata, title, assignment, abstract, contents, main structure, and page
  numbering;
- paragraphs, nested STO lists, figures, tables, long tables, equations,
  definitions, abbreviations, bibliography, citations, appendices, and code;
- shared global/section/auto numbering and appendix-local numbering;
- editable DOCX styles, OMML, fields, bookmarks, and repeating table headers;
- experimental LuaLaTeX PDF preview with longtable continuation heads;
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
  segments because repeated header rows do not reevaluate fields.
- Automatic object numbering switches at ten objects only when at least two
  sections contain that object type.
- The experimental PDF preview falls back to Cyrillic-capable Liberation Serif
  with Times-compatible metrics when licensed Times New Roman is unavailable.

## Completed DOCX Acceptance Work

The corrections captured by the first generated-DOCX review on 2026-09-11 were
implemented and regression-tested on 2026-09-12:

- structural contents entries use sentence case and updateable page-reference
  fields without question-mark placeholders;
- terminology is one optional structural element, introductions are centered,
  headings use regular type, and heading numbers use non-breaking spaces;
- ordinary body paragraphs retain the 1.25 cm indent while positioned content
  uses explicit non-indented styles;
- title details, assignment fields, and wrapped abstract source lines use real
  Word paragraphs rather than pervasive soft line breaks;
- list labels use the prescribed literal hyphen or enumerator followed by U+00A0;
- figure content, code, and continued-table labels use explicit alignments;
- editable equation numbers use a symmetric borderless row that keeps the
  equation centered and its number right-aligned, symbol explanations have
  structured source syntax, and appendix designator/title lines share one
  paragraph;
- structured bibliography records cover web, legal, article, book, chapter,
  conference, dataset, preprint, standard, and thesis sources with normalized
  punctuation and compact responsibility/container separators.

The generated acceptance DOCX and rendered page images remain machine-local QA
evidence and are not committed to the repository. Current Microsoft Word field
refresh remains a manual release gate.

## Release Readiness Work

- GitHub Actions CI validates lint, tests, the representative source, the package
  build, and construction of the Docker image without repository secrets;
- MIT is the project license; keep third-party programs, fonts, and normative
  documents outside that grant;
- publish packaged release artifacts;
- add signed or checksummed container publication if distribution requires it.

## Later Work

- complete PDF conformance for v2, including structural contents entries, full
  assignment metadata, bounded figure sizing, visual regression coverage, and
  mandatory renderer tests in CI;
- incorporate any additional bibliography STO clauses into the structured model
  when normative evidence becomes available;
- add more SSAU title-page variants;
- add table notes and other structures only with normative fixtures;
- study a second university standard and extract proven profile variation
  points;
- support other universities without weakening the strict dialect contract;
- consider landscape pages, SVG, TikZ, and numbered algorithms as explicitly
  versioned dialect additions.
