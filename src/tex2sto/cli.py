"""Command-line interface with shared project configuration."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from tex2sto.config import override_settings
from tex2sto.dialect import load_project
from tex2sto.errors import Tex2StoError
from tex2sto.validation import validate_project
from tex2sto.validation.pages import check_rendered_pages
from tex2sto.version import __version__


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tex2sto")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("check", "validate source"),
        ("build", "build DOCX"),
        ("check-pages", "check an already rendered PDF"),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("source", type=Path)
        command.add_argument("--config", type=Path)
        command.add_argument("--strict", action=argparse.BooleanOptionalAction, default=None)
        if name == "check-pages":
            command.add_argument("rendered_pdf", type=Path)
        if name != "build":
            continue
        command.add_argument("-o", "--output", type=Path)
        command.add_argument(
            "--pdf",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="add an experimental PDF preview",
        )
        command.add_argument("--numbering", choices=("auto", "global", "section"))
        command.add_argument("--numbering-threshold", type=int)
        for kind in ("figure", "table", "equation"):
            command.add_argument(f"--{kind}-numbering", choices=("auto", "global", "section"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        project = load_project(args.source, config=args.config)
        values = {
            name: getattr(args, name, None)
            for name in (
                "strict",
                "pdf",
                "numbering",
                "numbering_threshold",
                "figure_numbering",
                "table_numbering",
                "equation_numbering",
            )
        }
        project.settings = override_settings(project.settings, **values)
        settings = project.settings
        if args.command == "check-pages":
            count, bag = check_rendered_pages(args.rendered_pdf, settings)
        else:
            bag = validate_project(project)
        diagnostics = bag.with_strict_warnings() if settings.strict else bag.items
        for diagnostic in diagnostics:
            print(diagnostic.format(), file=sys.stderr)
        if any(item.severity.value == "error" for item in diagnostics):
            return 1
        if args.command == "check-pages":
            print(f"Rendered pages: {count}")
        if args.command != "build":
            return 0
        from tex2sto.build import BuildOptions, build_project

        output = args.output or project.root / settings.output_dir
        for path in build_project(project, BuildOptions(output_dir=output)):
            print(path)
        return 0
    except (Tex2StoError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
