# Roadmap

## Current State

The product interview and initial engineering harness are complete. The
repository has no application scaffold or working converter yet.

## Phase 1: Conversion Spike

Prove the risky integration points before expanding the dialect:

- initialize the packaged Python 3.12+ application with uv;
- select and pin exact Pandoc and TeX Live versions;
- convert a minimal supported `.tex` fixture to DOCX through Pandoc;
- verify `reference.docx` style assignment through a Lua filter;
- verify editable OMML equations;
- render the same fixture to PDF through LuaLaTeX;
- test a viable Word behavior for multi-page table headers and the required
  `Продолжение таблицы N` label;
- establish structural and visual test entry points.

The table-continuation mechanism is a spike outcome, not a settled
implementation detail. The requirement itself is not optional.

## Phase 2: Minimal End-to-End CLI

- implement `tex2sto build` with DOCX as the default output;
- implement `-o` and additive `--pdf`;
- implement project-root discovery and safe `\input` expansion;
- implement the initial metadata and master-level title page;
- add paragraphs, sections, subsections, lists, contents, introduction, and
  conclusion;
- add deterministic errors for unknown syntax and invalid structure;
- publish verified Russian installation, CLI, and initial dialect docs.

## Phase 3: Complete V1 Profile

- add figures, captions, references, and appendix-local numbering;
- add long tables, table notes, and continuation behavior;
- add equations, symbol explanations, numbering, and references;
- add abstract statistics and keyword validation;
- add definitions, symbols, abbreviations, assignment pages, and appendices;
- add code listings;
- add structured in-source bibliography entries and citations;
- add warnings, `--strict`, and narrow local suppression;
- implement auto/global/section numbering controls;
- ship pinned Docker and native macOS workflows;
- build the regression suite required for toolchain upgrades.

## Later Work

- incorporate the additional bibliography STO and extend the bibliography data
  model;
- add more SSAU title-page variants;
- study a second university standard;
- extract proven variation points into a general profile format;
- add other universities without weakening the strict dialect contract.

## Explicitly Deferred Decisions

These are known decisions to make during the relevant phase:

- exact fields and final layout of the master-level title page;
- exact Pandoc and TeX Live version pins;
- exact syntax for bibliography records in the `.tex` source;
- exact syntax for local warning suppression;
- the tested OOXML technique for automatic table-continuation labels;
- packaging, release, license, and CI policy.

Do not silently choose one of these while changing unrelated code. Resolve it
with a focused spike, repository evidence, or user confirmation.
