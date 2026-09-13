"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from tex2sto.dialect import load_project
from tex2sto.errors import Tex2StoError
from tex2sto.validation import validate_project
from tex2sto.version import __version__


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tex2sto")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="validate a tex2sto source project")
    check.add_argument("source", type=Path)
    check.add_argument("--strict", action="store_true", help="promote warnings to errors")

    build = subparsers.add_parser("build", help="build DOCX")
    build.add_argument("source", type=Path)
    build.add_argument("-o", "--output", type=Path)
    build.add_argument(
        "--pdf",
        action="store_true",
        help="add an experimental PDF preview (not covered by v1 compatibility)",
    )
    build.add_argument("--strict", action="store_true", help="promote warnings to errors")
    build.add_argument("--numbering", choices=("auto", "global", "section"), default="auto")
    build.add_argument("--numbering-threshold", type=int, default=10)
    for kind in ("figure", "table", "equation"):
        build.add_argument(
            f"--{kind}-numbering",
            choices=("auto", "global", "section"),
            default=None,
        )
    return parser


def _emit_diagnostics(project_path: Path, *, strict: bool) -> bool:
    project = load_project(project_path)
    bag = validate_project(project)
    diagnostics = bag.with_strict_warnings() if strict else bag.items
    for diagnostic in diagnostics:
        print(diagnostic.format(), file=sys.stderr)
    return any(diagnostic.severity.value == "error" for diagnostic in diagnostics)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "check":
            return 1 if _emit_diagnostics(args.source, strict=args.strict) else 0
        if args.command == "build":
            project = load_project(args.source)
            bag = validate_project(project)
            diagnostics = bag.with_strict_warnings() if args.strict else bag.items
            for diagnostic in diagnostics:
                print(diagnostic.format(), file=sys.stderr)
            if any(diagnostic.severity.value == "error" for diagnostic in diagnostics):
                return 1
            from tex2sto.build import BuildOptions, build_project

            output = args.output or args.source.resolve().parent / "build"
            options = BuildOptions(
                output_dir=output,
                pdf=args.pdf,
                numbering=args.numbering,
                numbering_threshold=args.numbering_threshold,
                figure_numbering=args.figure_numbering,
                table_numbering=args.table_numbering,
                equation_numbering=args.equation_numbering,
            )
            outputs = build_project(project, options)
            for path in outputs:
                print(path)
            return 0
    except Tex2StoError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
