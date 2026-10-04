"""Parse the single, preamble-only laboratory title declaration."""

from __future__ import annotations

import re

from tex2sto.dialect.syntax import parse_named_arguments
from tex2sto.errors import SourceError
from tex2sto.model.document import LabTitle

REQUIRED_FIELDS = {"number", "course", "author", "group", "reviewer", "year"}
OPTIONAL_FIELDS = {"variant", "city", "author-label", "reviewer-label"}


def _plain_text(value: str) -> str:
    result = []
    cursor = 0
    while cursor < len(value):
        char = value[cursor]
        if char == "\\":
            cursor += 1
            if cursor == len(value) or value[cursor] not in "%&#_{}":
                raise SourceError("labtitle values accept plain text and escaped symbols only")
            result.append(value[cursor])
        elif char in "{}$^":
            raise SourceError("labtitle values do not accept groups or mathematical markup")
        else:
            result.append(char)
        cursor += 1
    return " ".join("".join(result).split()).replace("~", "\u00a0")


def parse_lab_title(content: str) -> LabTitle:
    values = parse_named_arguments(content)
    unknown = values.keys() - REQUIRED_FIELDS - OPTIONAL_FIELDS
    if unknown:
        raise SourceError(f"unknown labtitle fields: {', '.join(sorted(unknown))}")
    values = {key: _plain_text(value) for key, value in values.items()}
    missing = REQUIRED_FIELDS - values.keys()
    if missing:
        raise SourceError(f"required labtitle fields are missing: {', '.join(sorted(missing))}")
    for key, value in values.items():
        if not value:
            raise SourceError(f"labtitle field must not be empty: {key}")
    if not re.fullmatch(r"[1-9][0-9]*", values["number"]):
        raise SourceError("labtitle number must be a positive integer")
    if not re.fullmatch(r"[0-9]{4}", values["year"]):
        raise SourceError("labtitle year must contain four digits")
    return LabTitle(**{key.replace("-", "_"): value for key, value in values.items()})
