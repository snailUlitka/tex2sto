# tex2sto Agent Guide

## Project

tex2sto is a Python CLI that compiles a deliberately restricted LaTeX dialect
into editable DOCX documents that conform to Samara University
STO 02068410-004-2018. DOCX is the supported release output. The optional PDF path remains an
experimental preview in version 2.0.

The application is implemented as a uv-managed Python 3.12 application. Pandoc 3.11 produces
DOCX using resources owned by the `ssau` profile. LuaLaTeX from TeX Live 2026
produces the experimental PDF preview.

## Audience Boundary

- `docs/` and the root `README.md` are user-facing and must be written in
  Russian.
- `harness/` is for agents and maintainers and must be written in English.
- Code, code comments, identifiers, exceptions, log messages, and developer
  diagnostics must be written in English.
- `AGENTS.md` files must be written in English.
- A user-visible behavior change requires a matching update in `docs/` once
  that behavior is implemented.
- An architecture, invariant, validation, or roadmap change requires a matching
  update in `harness/`.

## Knowledge Map

- [Agent workflow and harness maintenance](harness/README.md)
- [Product scope and decisions](harness/product.md)
- [Architecture and component boundaries](harness/architecture.md)
- [Validation and regression strategy](harness/validation.md)
- [Implementation roadmap and deferred decisions](harness/roadmap.md)
- [Derived SSAU requirements](harness/standards/ssau.md)
- [User documentation index](docs/README.md)

## Core Invariants

- Use established converters where they fit: Python orchestrates, Pandoc and
  Lua filters produce DOCX, and LuaLaTeX produces the experimental PDF preview.
- Do not implement a general LaTeX parser or a DOCX writer from scratch.
- Accept only the documented tex2sto dialect. Unknown LaTeX commands are
  errors, not best-effort raw pass-through.
- Keep university-specific behavior isolated under the `ssau` profile with
  strict project-level overrides in tex2sto.toml.
- Generate DOCX by default. PDF is available only as an explicitly requested
  experimental preview and is outside the DOCX compatibility contract.
- Apply explicit `Tex2Sto ...` Word styles to semantic content. DOCX must remain
  editable; equations should use native OMML when the tested Pandoc path
  supports them.
- Keep LibreOffice out of the production build path. It may be used for
  rendering and visual QA.
- Treat the STO as normative and supplied templates as supporting evidence.
  User-confirmed decisions take precedence over both.
- Never reproduce the full source STO in the repository. Maintain a derived,
  clause-oriented implementation checklist instead.

## Change Discipline

- Preserve the distinction between mechanically enforceable layout or syntax
  rules and semantic writing guidance that requires human judgment.
- Add executable checks for mechanical rules instead of duplicating them as
  prose-only reminders.
- Do not broaden the accepted LaTeX subset without dialect documentation and
  positive and negative fixtures.
- Do not update pinned Pandoc or TeX Live versions casually. Dependency updates
  require the regression gates described in `harness/validation.md`.
- Do not copy machine-local source files from Downloads into the repository
  unless the user explicitly requests it and redistribution is permitted.

## Current Validation

Run the checks relevant to the change:

```sh
uv run ruff check .
uv run pytest
uv run tex2sto check examples/master-thesis/main.tex --strict
uv run tex2sto check examples/lab-report/main.tex --strict
uv run tex2sto check examples/practice-report/main.tex --strict
uv run tex2sto build examples/master-thesis/main.tex -o build/example
uv run tex2sto build examples/lab-report/main.tex -o build/lab-report
uv run tex2sto build examples/practice-report/main.tex -o build/practice-report
uv build
docker build --platform linux/amd64 -t tex2sto:ci .
git diff --check
```

DOCX renderer changes require structural output checks and visual inspection.
DOCX behavior that depends on fields must also be verified in current Microsoft
Word before a release compatibility claim. PDF conformance and mandatory PDF
renderer coverage are deferred beyond version 2.0. Verify that links in this file,
`harness/README.md`, the root README, and `docs/README.md` resolve.
