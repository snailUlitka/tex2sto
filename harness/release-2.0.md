# Version 2.0 acceptance record

The user approved these changes after reviewing the practice report template.
This is a DOCX major release; PDF remains an experimental preview. The earlier
roadmap's association of PDF conformance with the next major version is
superseded by this release scope.

## Required behavior

- Strict optional `tex2sto.toml`; empty and absent files use defaults. Resolve
  defaults, project configuration, and explicit CLI/MCP overrides in that order.
- Share configuration across source validation, DOCX builds, and MCP.
- Configure optional terminology before introduction or after conclusion.
- Restore 1.25 cm first-line indents for numbered headings and abstract keywords.
- Configure table line spacing, retaining 1.5 by default.
- Generate hyphen separators and numeric en-dash ranges by default; warn about
  authored em dashes unless enabled. Also support en/em-dash separators.
- Fix list wrapping indents and support decimal-only nested enumeration.
- Support the practice cover and editable assignment competency matrix without
  importing the source document or its personal data into the repository.
- Require references before numbered equations; support symbol explanations
  after unnumbered equations, semicolon-separated explanations, equation spacing,
  and mechanical warnings for programming multiplication operators.
- Remove the bottom border of interrupted longtable parts.
- Warn about configurable minimum/maximum page counts after real pagination;
  no default bounds and no production dependency on LibreOffice.
- Document, test, render, inspect, package, and release version 2.0.0.

## Accepted limitations

- Contents page-reference fields are sufficient; a full Word TOC is unnecessary.
- Keep uncited sources with warnings; strict mode may promote the warning.
- No citation page locators, landscape pages, or source-age checks in this change.
- Report content and competency attainment remain subject to human review.

## Evidence

Implementation and release validation are recorded here as they complete.

### Local acceptance on 2026-11-08

- Ruff and 106 tests passed, including real DOCX and experimental PDF builds.
- All three tracked examples passed strict source validation and DOCX builds.
- All rendered pages were inspected: thesis 13 pages, practice 14 pages,
  laboratory 2 pages, plus laboratory covers without a variant and with long
  fields. The earlier overflow in the thesis example was corrected by moving
  its explicit table-break point. No source renderer markers remain in output.
- Microsoft Word for macOS 16.101.1 opened the thesis and practice DOCX, updated
  page/contents fields to the actual 13/14-page layouts, exposed the equation
  as an editable Equation object, and displayed the continuation on the next
  page with a repeated header and an open first-part bottom border.
- Actual rendered PDF checks exercised minimum/maximum warnings, strict failure,
  and inclusive equal bounds. No default limits were applied.
- Pandoc remained 3.11; the temporary official macOS archive matched its published
  SHA-256. No existing dependency versions changed in the lock file.

The GitHub CI workflow builds the pinned linux/amd64 image and builds all three
representative DOCX documents inside it. Release assets contain the wheel,
source distribution, and SHA-256 checksums. Publishing follows green CI for the
release commit; Word/PNG intermediates remain local QA evidence.

### Distribution acceptance

The final linux/amd64 Docker image built successfully with Python 3.12.11,
uv 0.12.8, Pandoc 3.11, and TeX Live 2026. All three examples built with strict
validation inside that image, and its Poppler checker read the rendered
practice PDF as 14 pages. The wheel and source distribution were built by the
pinned uv inside Docker. The wheel was reinstalled in a disposable container
and successfully built the practice report using its packaged resources.
Both archives were inspected; local source documents and QA output are absent.
SHA-256 sums are delivered alongside the two release archives.
