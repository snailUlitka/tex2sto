"""Strict validation for the documented tex2sto v1 dialect."""

from __future__ import annotations

import re
from collections import Counter

from tex2sto.diagnostics import DiagnosticBag
from tex2sto.dialect.metadata import BIBLIOGRAPHY_FIELDS, SINGLE_COMMANDS
from tex2sto.dialect.syntax import (
    CONTROL_WORD_RE,
    control_words,
    find_command_calls,
    find_environment,
    line_number,
    mask_comments,
    replace_spans,
)
from tex2sto.model import SourceProject
from tex2sto.model.numbering import APPENDIX_LETTERS
from tex2sto.validation.prose import check_prose

METADATA_COMMANDS = set(SINGLE_COMMANDS) | set(BIBLIOGRAPHY_FIELDS) | {
    "consultant",
    "keywords",
    "source",
    "supervisor",
}
STRUCTURE_COMMANDS = {
    "introduction",
    "conclusion",
    "definitions",
    "abbreviations",
    "printbibliography",
    "appendix",
    "definition",
    "symbol",
}
CONTENT_COMMANDS = {
    "appendix",
    "begin",
    "caption",
    "centering",
    "cite",
    "documentclass",
    "emph",
    "end",
    "hline",
    "href",
    "includegraphics",
    "input",
    "item",
    "label",
    "ldots",
    "newline",
    "paragraph",
    "printbibliography",
    "ref",
    "section",
    "subparagraph",
    "subsection",
    "subsubsection",
    "tablebreak",
    "tablehead",
    "texttt",
    "url",
}
MATH_COMMANDS = {
    "alpha",
    "beta",
    "gamma",
    "delta",
    "epsilon",
    "varepsilon",
    "zeta",
    "eta",
    "theta",
    "vartheta",
    "iota",
    "kappa",
    "lambda",
    "mu",
    "nu",
    "xi",
    "pi",
    "varpi",
    "rho",
    "varrho",
    "sigma",
    "varsigma",
    "tau",
    "upsilon",
    "phi",
    "varphi",
    "chi",
    "psi",
    "omega",
    "Gamma",
    "Delta",
    "Theta",
    "Lambda",
    "Xi",
    "Pi",
    "Sigma",
    "Upsilon",
    "Phi",
    "Psi",
    "Omega",
    "frac",
    "sqrt",
    "sum",
    "prod",
    "int",
    "iint",
    "iiint",
    "lim",
    "sin",
    "cos",
    "tan",
    "cot",
    "log",
    "ln",
    "exp",
    "min",
    "max",
    "det",
    "left",
    "right",
    "cdot",
    "times",
    "div",
    "pm",
    "mp",
    "le",
    "leq",
    "ge",
    "geq",
    "ne",
    "neq",
    "approx",
    "infty",
    "partial",
    "nabla",
    "mathrm",
    "mathbf",
    "mathit",
    "operatorname",
    "text",
    "quad",
    "qquad",
    "overline",
    "underline",
    "hat",
    "bar",
    "vec",
    "begin",
    "end",
}
ALLOWED_COMMANDS = METADATA_COMMANDS | STRUCTURE_COMMANDS | CONTENT_COMMANDS | MATH_COMMANDS
ALLOWED_ENVIRONMENTS = {
    "abstract",
    "align",
    "align*",
    "aligned",
    "array",
    "cases",
    "description",
    "document",
    "enumerate",
    "equation",
    "equation*",
    "figure",
    "itemize",
    "longtable",
    "matrix",
    "pmatrix",
    "table",
    "tabular",
    "verbatim",
    "bibsource",
    "symbols",
}
MATH_ENVIRONMENTS = {
    "align",
    "align*",
    "aligned",
    "array",
    "cases",
    "equation",
    "equation*",
    "matrix",
    "pmatrix",
}
REQUIRED_METADATA = {
    "title": "\\title",
    "author": "\\author",
    "student_group": "\\studentgroup",
    "institute": "\\institute",
    "department": "\\department",
    "program_code": "\\programcode",
    "program_name": "\\programname",
    "study_profile": "\\studyprofile",
    "supervisor_name": "\\supervisor",
    "norm_controller": "\\normcontroller",
    "year": "\\year",
}


def _mask_verbatim(source: str) -> str:
    replacements: list[tuple[int, int, str]] = []
    for start, end, _ in find_environment(source, "verbatim"):
        replacements.append((start, end, " " * (end - start)))
    return replace_spans(source, replacements)


def _validate_commands(project: SourceProject, diagnostics: DiagnosticBag) -> None:
    source = _mask_verbatim(project.expanded_source)
    for command, line in control_words(source):
        if command not in ALLOWED_COMMANDS:
            diagnostics.error(
                "T2S-E101",
                f"unknown or forbidden command: \\{command}",
                path=project.master,
                line=line,
            )
    environment_calls = [
        *find_command_calls(source, "begin", 1),
        *find_command_calls(source, "end", 1),
    ]
    for call in environment_calls:
        environment = call.args[0].strip()
        if environment not in ALLOWED_ENVIRONMENTS:
            diagnostics.error(
                "T2S-E102",
                f"unknown or forbidden environment: {environment}",
                path=project.master,
                line=call.line,
            )
    math_spans = [
        (start, end)
        for environment in MATH_ENVIRONMENTS
        for start, end, _ in find_environment(source, environment)
    ]
    math_spans.extend(
        (match.start(), match.end())
        for pattern in (r"(?<!\\)\$(?:\\.|[^$])*\$", r"\\\[.*?\\\]")
        for match in re.finditer(pattern, source, flags=re.DOTALL)
    )
    masked = mask_comments(source)
    for match in CONTROL_WORD_RE.finditer(masked):
        command = match.group(1)
        if command in MATH_COMMANDS - {"begin", "end"} and not any(
            start <= match.start() < end for start, end in math_spans
        ):
            diagnostics.error(
                "T2S-E103",
                f"math command may appear only in math: \\{command}",
                path=project.master,
                line=line_number(source, match.start()),
            )
    bibliography_environments = find_environment(source, "bibsource")
    for command in BIBLIOGRAPHY_FIELDS:
        nested = sum(
            len(find_command_calls(content, command, 1))
            for _, _, content in bibliography_environments
        )
        if len(find_command_calls(source, command, 1)) != nested:
            diagnostics.error(
                "T2S-E104",
                f"\\{command} may appear only inside bibsource",
                path=project.master,
            )


def _validate_metadata(project: SourceProject, diagnostics: DiagnosticBag) -> None:
    for attribute, command in REQUIRED_METADATA.items():
        if not getattr(project.metadata, attribute):
            diagnostics.error("T2S-E201", f"required metadata is missing: {command}")
    if project.metadata.assignment_variant not in {"none", "1", "2"}:
        diagnostics.error("T2S-E202", "assignment variant must be none, 1, or 2")
    if project.metadata.assignment_variant != "none":
        required_assignment = {
            "assignment_approver": "\\assignmentapprover",
            "assignment_questions": "\\assignmentquestions",
            "assignment_issued": "\\assignmentissued",
            "assignment_due": "\\assignmentdue",
        }
        for attribute, command in required_assignment.items():
            if not getattr(project.metadata, attribute):
                diagnostics.error("T2S-E203", f"assignment metadata is missing: {command}")
    keyword_count = len(project.metadata.keywords)
    if not 5 <= keyword_count <= 15:
        diagnostics.error(
            "T2S-E204",
            "keywords must contain between 5 and 15 semicolon-separated items",
        )
    abstract_length = len(re.sub(r"\\[A-Za-z@]+|[{}]", "", project.metadata.abstract))
    if not project.metadata.abstract:
        diagnostics.error("T2S-E205", "an abstract environment is required")
    elif abstract_length > 850:
        diagnostics.warning("T2S-W201", "the recommended abstract limit is 850 characters")


def _validate_structure(project: SourceProject, diagnostics: DiagnosticBag) -> None:
    body = project.body
    required = ("introduction", "section", "conclusion")
    positions: dict[str, int] = {}
    for name in required:
        calls = find_command_calls(body, name, 0 if name != "section" else 1)
        if not calls:
            diagnostics.error("T2S-E301", f"required document structure is missing: \\{name}")
        else:
            positions[name] = calls[0].start
    if len(positions) == len(required) and not (
        positions["introduction"] < positions["section"] < positions["conclusion"]
    ):
        diagnostics.error(
            "T2S-E302",
            "introduction, main sections, and conclusion are out of order",
        )
    bibliography_marker = find_command_calls(body, "printbibliography", 0)
    if project.bibliography and not bibliography_marker:
        diagnostics.error("T2S-E303", "\\printbibliography is required when sources are declared")
    if bibliography_marker and not project.bibliography:
        diagnostics.warning(
            "T2S-W301",
            "bibliography marker is present but no sources are declared",
        )
    conclusion = find_command_calls(body, "conclusion", 0)
    appendices = find_command_calls(body, "appendix", 2)
    if bibliography_marker and conclusion and bibliography_marker[0].start < conclusion[0].start:
        diagnostics.error("T2S-E304", "bibliography must follow the conclusion")
    if appendices:
        boundary = (
            bibliography_marker[0].start
            if bibliography_marker
            else conclusion[0].start
            if conclusion
            else None
        )
        if boundary is not None and appendices[0].start < boundary:
            diagnostics.error("T2S-E305", "appendices must follow the bibliography or conclusion")
        if len(appendices) > len(APPENDIX_LETTERS):
            diagnostics.error(
                "T2S-E306",
                f"v1 supports at most {len(APPENDIX_LETTERS)} single-letter appendices",
            )
    introduction = find_command_calls(body, "introduction", 0)
    if introduction:
        for command in ("definitions", "abbreviations"):
            calls = find_command_calls(body, command, 0)
            if calls and calls[0].start > introduction[0].start:
                diagnostics.error("T2S-E307", f"\\{command} must precede the introduction")
    for command in ("definitions", "abbreviations"):
        if len(find_command_calls(body, command, 0)) > 1:
            diagnostics.error("T2S-E310", f"\\{command} may appear only once")
    for command in ("section", "subsection", "subsubsection"):
        for call in find_command_calls(body, command, 1):
            title = call.args[0].strip()
            first_letter = next((character for character in title if character.isalpha()), "")
            if first_letter and not first_letter.isupper():
                diagnostics.error(
                    "T2S-E308",
                    f"\\{command} title must start with an uppercase letter",
                    line=call.line,
                )
            if title.endswith("."):
                diagnostics.error(
                    "T2S-E309",
                    f"\\{command} title must not end with a period",
                    line=call.line,
                )


def _environment_label(content: str) -> str | None:
    labels = find_command_calls(content, "label", 1)
    return labels[0].args[0].strip() if labels else None


def _validate_objects(project: SourceProject, diagnostics: DiagnosticBag) -> None:
    source = project.body
    labels = [call.args[0].strip() for call in find_command_calls(source, "label", 1)]
    labels.extend(call.args[0].strip() for call in find_command_calls(source, "appendix", 2))
    for label, count in Counter(labels).items():
        if count > 1:
            diagnostics.error("T2S-E401", f"duplicate label: {label}")
    reference_calls = find_command_calls(source, "ref", 1)
    references = [call.args[0].strip() for call in reference_calls]
    first_references: dict[str, int] = {}
    for call in reference_calls:
        first_references.setdefault(call.args[0].strip(), call.start)
    for reference in references:
        if reference not in labels:
            diagnostics.error("T2S-E402", f"reference points to a missing label: {reference}")

    for environment, prefix in (("figure", "fig:"), ("table", "tab:"), ("longtable", "tab:")):
        for start, _, content in find_environment(source, environment):
            captions = find_command_calls(content, "caption", 1)
            label = _environment_label(content)
            if len(captions) != 1:
                diagnostics.error("T2S-E403", f"every {environment} requires exactly one caption")
            if label is None or not label.startswith(prefix):
                diagnostics.error("T2S-E404", f"every {environment} requires a {prefix} label")
            elif label not in references:
                diagnostics.error("T2S-E405", f"every {environment} must be referenced: {label}")
            elif first_references[label] >= start:
                diagnostics.error(
                    "T2S-E416",
                    f"{environment} must follow its first reference: {label}",
                )
            if captions and captions[0].args[0].strip().endswith("."):
                diagnostics.error(
                    "T2S-E417",
                    f"{environment} caption must not end with a period",
                    line=captions[0].line,
                )
            if environment == "longtable":
                table_heads = find_command_calls(content, "tablehead", 1)
                if len(table_heads) != 1:
                    diagnostics.error(
                        "T2S-E413",
                        "every longtable requires exactly one \\tablehead command",
                    )
                table_breaks = find_command_calls(content, "tablebreak", 0)
                if not table_breaks:
                    diagnostics.error(
                        "T2S-E420",
                        "every longtable requires at least one \\tablebreak command",
                    )

                cleaned = replace_spans(
                    content,
                    [
                        (call.start, call.end, "")
                        for command, arity in (
                            ("caption", 1),
                            ("label", 1),
                            ("tablehead", 1),
                            ("hline", 0),
                        )
                        for call in find_command_calls(content, command, arity)
                    ],
                )
                segments = re.split(r"\\tablebreak(?![A-Za-z@])", cleaned)
                for segment in segments:
                    row_count = sum("&" in row for row in segment.split(r"\\"))
                    if row_count == 0:
                        diagnostics.error(
                            "T2S-E421",
                            "each longtable segment must contain at least one data row",
                        )
                    elif row_count > 18:
                        diagnostics.error(
                            "T2S-E422",
                            "longtable segments may contain at most 18 data rows",
                        )

    all_table_heads = len(find_command_calls(source, "tablehead", 1))
    nested_table_heads = sum(
        len(find_command_calls(content, "tablehead", 1))
        for _, _, content in find_environment(source, "longtable")
    )
    if all_table_heads != nested_table_heads:
        diagnostics.error("T2S-E415", "\\tablehead may appear only inside longtable")
    all_table_breaks = len(find_command_calls(source, "tablebreak", 0))
    nested_table_breaks = sum(
        len(find_command_calls(content, "tablebreak", 0))
        for _, _, content in find_environment(source, "longtable")
    )
    if all_table_breaks != nested_table_breaks:
        diagnostics.error("T2S-E423", "\\tablebreak may appear only inside longtable")

    for environment in ("tabular", "longtable"):
        for _, _, content in find_environment(source, environment):
            cleaned = replace_spans(
                content,
                [
                    (call.start, call.end, "")
                    for command, arity in (
                        ("caption", 1),
                        ("label", 1),
                        ("tablehead", 1),
                        ("tablebreak", 0),
                    )
                    for call in find_command_calls(content, command, arity)
                ],
            )
            for row in cleaned.split(r"\\"):
                if "&" not in row:
                    continue
                cells = [
                    re.sub(r"\\hline|^\s*\{[^{}]*\}", "", cell).strip() for cell in row.split("&")
                ]
                if any(not cell for cell in cells):
                    diagnostics.error(
                        "T2S-E414",
                        "empty table cells must contain an explicit dash",
                    )

    appendix_calls = find_command_calls(source, "appendix", 2)
    for call in appendix_calls:
        label = call.args[0].strip()
        if not label.startswith("app:"):
            diagnostics.error("T2S-E406", "appendix labels must start with app:", line=call.line)
        elif label not in references:
            diagnostics.error("T2S-E407", f"every appendix must be referenced: {label}")
        elif first_references[label] >= call.start:
            diagnostics.error(
                "T2S-E419",
                f"appendix must follow its first reference: {label}",
                line=call.line,
            )
    referenced_appendices = sorted(
        (first_references[call.args[0].strip()], call.args[0].strip())
        for call in appendix_calls
        if call.args[0].strip() in first_references
    )
    declared_appendices = [call.args[0].strip() for call in appendix_calls]
    if [label for _, label in referenced_appendices] != [
        label for label in declared_appendices if label in first_references
    ]:
        diagnostics.error("T2S-E418", "appendices must follow first-reference order")

    for environment in ("equation", "align"):
        for _, _, content in find_environment(source, environment):
            label = _environment_label(content)
            if label is None or not label.startswith("eq:"):
                diagnostics.error("T2S-E411", f"every {environment} requires an eq: label")
            elif label not in references:
                diagnostics.error("T2S-E412", f"every {environment} must be referenced: {label}")

    numbered_equations = sorted(
        (start, end)
        for environment in ("equation", "align")
        for start, end, _ in find_environment(source, environment)
    )
    symbol_environments = find_environment(source, "symbols")
    for start, _, content in symbol_environments:
        symbols = find_command_calls(content, "symbol", 2)
        if not symbols:
            diagnostics.error("T2S-E424", "every symbols environment requires a \\symbol command")
        for call in symbols:
            if not all(value.strip() for value in call.args):
                diagnostics.error(
                    "T2S-E425",
                    "symbol and explanation must not be empty",
                    line=call.line,
                )
        preceding = [end for _, end in numbered_equations if end <= start]
        if not preceding or mask_comments(source[max(preceding) : start]).strip():
            diagnostics.error(
                "T2S-E426",
                "symbols must immediately follow a numbered equation or align environment",
            )
    nested_symbols = sum(
        len(find_command_calls(content, "symbol", 2))
        for _, _, content in symbol_environments
    )
    if len(find_command_calls(source, "symbol", 2)) != nested_symbols:
        diagnostics.error("T2S-E427", "\\symbol may appear only inside symbols")

    for call in find_command_calls(source, "includegraphics", 1):
        asset = (project.root / call.args[0].strip()).resolve()
        try:
            asset.relative_to(project.root)
        except ValueError:
            diagnostics.error("T2S-E408", f"image path escapes the project root: {call.args[0]}")
            continue
        if asset.suffix.lower() in {".svg", ".svgz"}:
            diagnostics.error("T2S-E409", "SVG images are not supported in v1")
        elif asset.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            diagnostics.error(
                "T2S-E420",
                f"unsupported image format: {asset.suffix or '(none)'}",
            )
        elif not asset.is_file():
            diagnostics.error("T2S-E410", f"image file does not exist: {call.args[0]}")


def _validate_bibliography(project: SourceProject, diagnostics: DiagnosticBag) -> None:
    keys = [item.key for item in project.bibliography]
    for key, count in Counter(keys).items():
        if count > 1:
            diagnostics.error("T2S-E501", f"duplicate source key: {key}")
    allowed_kinds = {
        "article",
        "book",
        "chapter",
        "conference",
        "dataset",
        "legal",
        "preprint",
        "standard",
        "thesis",
        "web",
    }
    for item in project.bibliography:
        if not re.fullmatch(r"[A-Za-z0-9:_-]+", item.key):
            diagnostics.error("T2S-E503", f"invalid source key: {item.key}")
        if item.kind not in allowed_kinds:
            diagnostics.error("T2S-E504", f"unsupported source kind: {item.kind}")
        if not item.title or (item.details == "" and not item.kind):
            diagnostics.error(
                "T2S-E505",
                f"source requires a kind and title: {item.key}",
            )
        if item.details:
            continue
        required_fields = {
            "article": ("container", "year", "pages"),
            "book": ("place", "publisher", "year", "pages"),
            "chapter": ("container", "publisher", "year", "pages"),
            "conference": ("container", "year", "pages"),
            "dataset": ("publisher", "year", "url", "access_date"),
            "legal": ("url", "access_date"),
            "preprint": ("container", "year", "url", "access_date"),
            "standard": ("place", "publisher", "year", "pages"),
            "thesis": ("place", "year", "pages"),
            "web": ("url", "access_date"),
        }
        missing = [
            field
            for field in required_fields.get(item.kind, ())
            if not getattr(item, field)
        ]
        if missing:
            diagnostics.error(
                "T2S-E506",
                f"structured source {item.key} is missing fields: {', '.join(missing)}",
            )
    citations = [call.args[0].strip() for call in find_command_calls(project.body, "cite", 1)]
    for citation in citations:
        for key in (part.strip() for part in citation.split(",")):
            if key not in keys:
                diagnostics.error("T2S-E502", f"citation points to a missing source: {key}")
    cited = {part.strip() for citation in citations for part in citation.split(",")}
    for key in keys:
        if key not in cited:
            diagnostics.warning("T2S-W501", f"declared source is never cited: {key}")


def validate_project(project: SourceProject) -> DiagnosticBag:
    diagnostics = DiagnosticBag()
    _validate_commands(project, diagnostics)
    _validate_metadata(project, diagnostics)
    _validate_structure(project, diagnostics)
    _validate_objects(project, diagnostics)
    _validate_bibliography(project, diagnostics)
    check_prose(project.body, path=project.master, diagnostics=diagnostics)
    return diagnostics
