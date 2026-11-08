"""Parse explicit practice metadata and competency assignment rows."""

from __future__ import annotations

from datetime import date

from tex2sto.dialect.lab_title import _plain_text
from tex2sto.dialect.syntax import parse_named_arguments
from tex2sto.errors import SourceError
from tex2sto.model.document import PracticeAssignment, PracticeTitle

REQUIRED = {
    "kind",
    "type",
    "start",
    "end",
    "order-date",
    "order-number",
    "organization",
    "author-dative",
}
OPTIONAL = {"study-level", "submitted", "defended", "grade"}


def plain(value: str) -> str:
    try:
        return _plain_text(value)
    except SourceError as error:
        raise SourceError(str(error).replace("labtitle", "practice")) from error


def parse_practice_title(content: str) -> PracticeTitle:
    values = parse_named_arguments(content)
    unknown = values.keys() - REQUIRED - OPTIONAL
    if unknown:
        raise SourceError(f"unknown practicetitle fields: {', '.join(sorted(unknown))}")
    values = {name: plain(value) for name, value in values.items()}
    missing = REQUIRED - values.keys()
    if missing:
        raise SourceError(
            f"required practicetitle fields are missing: {', '.join(sorted(missing))}"
        )
    if any(not value for value in values.values()):
        raise SourceError("practicetitle fields must not be empty")
    for name in ("start", "end", "order-date", "submitted", "defended"):
        if name not in values:
            continue
        try:
            parsed = date.fromisoformat(values[name])
            if parsed.isoformat() != values[name]:
                raise ValueError("noncanonical date")
        except ValueError as error:
            raise SourceError(f"practicetitle {name} must be a date in YYYY-MM-DD form") from error
    if values["start"] > values["end"]:
        raise SourceError("practice start date must not follow its end date")
    return PracticeTitle(**{name.replace("-", "_"): value for name, value in values.items()})


def parse_practice_assignment(args: tuple[str, ...]) -> PracticeAssignment:
    values = [plain(value) for value in args]
    if not all(values):
        raise SourceError("practiceassignment requires nonempty competency, outcomes, and task")
    return PracticeAssignment(*values)
