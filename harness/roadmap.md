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
- Editable Word table continuations use a repeated conditional field row; PDF
  uses `longtable` continuation heads.
- Automatic object numbering switches at ten objects only when at least two
  sections contain that object type.
- Containers fall back to TeX Gyre Termes when licensed Times New Roman is not
  available; normative PDF production still requires Times New Roman.

## Release Readiness Work

- complete the manual Microsoft Word gate for conditional table continuation
  fields on every supported Word version;
- add CI after the hosting platform and secret policy are chosen;
- choose the license and publish packaged release artifacts;
- add signed or checksummed container publication if distribution requires it.

## Later Work

- incorporate the additional bibliography STO and extend source fields;
- add more SSAU title-page variants;
- add table notes and other structures only with normative fixtures;
- study a second university standard and extract proven profile variation
  points;
- support other universities without weakening the strict dialect contract;
- consider landscape pages, SVG, TikZ, and numbered algorithms as explicitly
  versioned dialect additions.
