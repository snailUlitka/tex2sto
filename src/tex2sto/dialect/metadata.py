"""Extract tex2sto metadata commands from an expanded source."""

from __future__ import annotations

from tex2sto.dialect.lab_title import parse_lab_title
from tex2sto.dialect.practice import parse_practice_assignment, parse_practice_title
from tex2sto.dialect.syntax import find_command_calls, find_environment, replace_spans
from tex2sto.errors import SourceError
from tex2sto.model import BibliographyItem, Consultant, DocumentMetadata

SINGLE_COMMANDS: dict[str, tuple[str, int]] = {
    "title": ("title", 1),
    "author": ("author", 1),
    "studentgroup": ("student_group", 1),
    "institute": ("institute", 1),
    "faculty": ("faculty", 1),
    "department": ("department", 1),
    "programcode": ("program_code", 1),
    "programname": ("program_name", 1),
    "studyprofile": ("study_profile", 1),
    "normcontroller": ("norm_controller", 1),
    "city": ("city", 1),
    "year": ("year", 1),
    "assignmentvariant": ("assignment_variant", 1),
    "assignmentapprover": ("assignment_approver", 1),
    "assignmentgoal": ("assignment_goal", 1),
    "assignmentquestions": ("assignment_questions", 1),
    "assignmentissued": ("assignment_issued", 1),
    "assignmentdue": ("assignment_due", 1),
}

BIBLIOGRAPHY_FIELDS = {
    "bibkey": "key",
    "bibkind": "kind",
    "bibtitle": "title",
    "bibauthors": "authors",
    "bibmedium": "medium",
    "bibcontributors": "contributors",
    "bibcontainer": "container",
    "bibplace": "place",
    "bibpublisher": "publisher",
    "bibyear": "year",
    "bibissue": "issue",
    "bibpages": "pages",
    "biburl": "url",
    "bibaccessdate": "access_date",
}


def _one(
    source: str, name: str, arity: int
) -> tuple[tuple[str, ...] | None, list[tuple[int, int, str]]]:
    calls = find_command_calls(source, name, arity)
    if len(calls) > 1:
        raise SourceError(f"metadata command \\{name} may appear only once")
    if not calls:
        return None, []
    call = calls[0]
    return call.args, [(call.start, call.end, "")]


def _clean(value: str) -> str:
    return " ".join(value.split())


def _structured_source(content: str) -> BibliographyItem:
    values: dict[str, str] = {}
    for command, attribute in BIBLIOGRAPHY_FIELDS.items():
        calls = find_command_calls(content, command, 1)
        if len(calls) > 1:
            raise SourceError(f"bibliography command \\{command} may appear only once per source")
        if calls:
            values[attribute] = _clean(calls[0].args[0])
    missing = [field for field in ("key", "kind", "title") if not values.get(field)]
    if missing:
        commands = ", ".join(f"\\bib{field}" for field in missing)
        raise SourceError(f"structured bibliography source is missing: {commands}")
    return BibliographyItem(**values)


def parse_project_source(
    source: str,
) -> tuple[DocumentMetadata, str, list[BibliographyItem]]:
    document_classes = find_command_calls(source, "documentclass", 1)
    if len(document_classes) != 1 or _clean(document_classes[0].args[0]) != "tex2sto":
        raise SourceError("source must declare exactly \\documentclass{tex2sto}")

    document_envs = find_environment(source, "document")
    if len(document_envs) != 1:
        raise SourceError("source must contain exactly one document environment")
    _, _, body = document_envs[0]

    metadata = DocumentMetadata()
    practice_titles = find_command_calls(source, "practicetitle", 1)
    if len(practice_titles) > 1:
        raise SourceError("metadata command \\practicetitle may appear only once")
    if practice_titles:
        call = practice_titles[0]
        if not document_classes[0].end <= call.start < call.end <= document_envs[0][0]:
            raise SourceError("\\practicetitle must appear after documentclass and before document")
        metadata.practice_title = parse_practice_title(call.args[0])
    assignment_calls = find_command_calls(source, "practiceassignment", 3)
    if assignment_calls and not practice_titles:
        raise SourceError("\\practiceassignment requires \\practicetitle")
    for call in assignment_calls:
        if not document_classes[0].end <= call.start < call.end <= document_envs[0][0]:
            raise SourceError("\\practiceassignment must appear in the preamble")
        metadata.practice_assignments.append(parse_practice_assignment(call.args))
    lab_titles = find_command_calls(source, "labtitle", 1)
    if len(lab_titles) > 1:
        raise SourceError("metadata command \\labtitle may appear only once")
    if lab_titles:
        if practice_titles:
            raise SourceError("\\labtitle cannot be combined with \\practicetitle")
        call = lab_titles[0]
        if not document_classes[0].end <= call.start < call.end <= document_envs[0][0]:
            raise SourceError("\\labtitle must appear after documentclass and before document")
        metadata.lab_title = parse_lab_title(call.args[0])
        for command in set(SINGLE_COMMANDS) | {"supervisor", "consultant", "keywords"}:
            if find_command_calls(source, command, 0):
                raise SourceError(f"\\labtitle cannot be combined with \\{command}")
        if find_environment(source, "abstract"):
            raise SourceError("\\labtitle cannot be combined with an abstract")
    removals: list[tuple[int, int, str]] = []
    removals.extend((call.start, call.end, "") for call in [*practice_titles, *assignment_calls])
    for command, (attribute, arity) in SINGLE_COMMANDS.items():
        args, spans = _one(source, command, arity)
        removals.extend(spans)
        if args is not None:
            setattr(metadata, attribute, _clean(args[0]))

    supervisor, spans = _one(source, "supervisor", 2)
    removals.extend(spans)
    if supervisor is not None:
        metadata.supervisor_name = _clean(supervisor[0])
        metadata.supervisor_details = _clean(supervisor[1])

    keyword_args, spans = _one(source, "keywords", 1)
    removals.extend(spans)
    if keyword_args is not None:
        metadata.keywords = tuple(
            keyword.strip() for keyword in keyword_args[0].split(";") if keyword.strip()
        )

    consultant_calls = find_command_calls(source, "consultant", 2)
    metadata.consultants = [
        Consultant(_clean(call.args[0]), _clean(call.args[1])) for call in consultant_calls
    ]
    removals.extend((call.start, call.end, "") for call in consultant_calls)

    abstract_envs = find_environment(source, "abstract")
    if len(abstract_envs) > 1:
        raise SourceError("the abstract environment may appear only once")
    if abstract_envs:
        start, end, abstract = abstract_envs[0]
        metadata.abstract = abstract.strip()
        removals.append((start, end, ""))

    bibliography: list[BibliographyItem] = []
    for call in find_command_calls(source, "source", 5):
        key, kind, authors, title, details = (_clean(value) for value in call.args)
        bibliography.append(
            BibliographyItem(
                key=key,
                kind=kind,
                title=title,
                authors=authors,
                details=details,
            )
        )
        removals.append((call.start, call.end, ""))

    for start, end, content in find_environment(source, "bibsource"):
        bibliography.append(_structured_source(content))
        removals.append((start, end, ""))

    cleaned = replace_spans(source, removals)
    cleaned_document = find_environment(cleaned, "document")
    if len(cleaned_document) != 1:
        raise SourceError("metadata removal damaged the document environment")
    return metadata, cleaned_document[0][2].strip(), bibliography
