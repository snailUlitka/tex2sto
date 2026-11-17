# Version 2.1 release record

## Scope

The user requested a minor release for the formula corrections. Version 2.1.0
adds `T2S-W401` for dotted multiplication and indents every symbol-explanation
line after the first by 1.25 cm. Juxtaposition and `×` remain accepted. The
warning retains normal/strict behavior and next-line suppression. There is no
automatic substitution of mathematical operators.

The existing dialect and configuration resource URIs remain at `v2`. Python,
Pandoc, TeX Live, and locked third-party dependencies retain their versions.
DOCX is the supported release output; PDF remains an experimental preview.

## Validation and publication

The 2026-11-17 implementation evidence in [release-2.0.md](release-2.0.md)
includes visual review and supplementary tests on the installed Pandoc 3.12.1.
That evidence is not a replacement for the pinned 3.11 release gate.

The release CI runs the DOCX tests and builds all three examples in the pinned
linux/amd64 image. It retains the wheel, source distribution, and DOCX examples
as a commit-scoped verification artifact. The optional PDF construction test
is excluded from this DOCX release gate, as established by the product scope.

Before publication, confirm successful CI for the release commit, inspect the
pinned-toolchain DOCX outputs, and perform the applicable current Word checks
from [validation.md](validation.md). Release assets are the wheel, source
distribution, and `SHA256SUMS`. A GitHub draft may be prepared before these
gates finish; publication remains a separate action.
