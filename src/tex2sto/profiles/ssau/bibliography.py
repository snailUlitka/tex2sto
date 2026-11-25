"""Format structured and legacy source descriptions for the SSAU profile."""

from __future__ import annotations

import re

from tex2sto.model import BibliographyItem

_INITIAL = r"[^\W\d_]\.(?:-[^\W\d_]\.)*"
_INITIALS = rf"(?:{_INITIAL}\s*)+"
_SURNAME_FIRST = re.compile(rf"(?P<surname>.+?)(?:,\s*|\s+)(?P<initials>{_INITIALS})")
_INITIALS_FIRST = re.compile(rf"(?P<initials>{_INITIALS})\s+(?P<surname>.+)")
_ADDITIONAL_AUTHORS = re.compile(r"[\s;,]+(et al\.?|и др\.?)$", re.IGNORECASE)
_VOLUME_AT_END = re.compile(r"(.+?)[.,]\s+((?:Vol\.|Т\.)\s*\d+[a-zа-я]?)\.?", re.IGNORECASE)
_NUMBERED_PAGES = re.compile(
    r"(?:(?P<label>(?:С|P|pp)\.)\s*)?(?P<start>\d+)(?:\s*[-–—]\s*(?P<end>\d+))?",
    re.IGNORECASE,
)


def _normalize_text(value: str, separator: str) -> str:
    normalized = value.strip()
    while '"' in normalized:
        normalized = normalized.replace('"', "«", 1)
        if '"' not in normalized:
            break
        normalized = normalized.replace('"', "»", 1)
    normalized = re.sub(r" (?:(?:---)|[-–—]) ", f" {separator} ", normalized)
    if re.fullmatch(r"\d+\s*[-—–]\s*\d+", normalized):
        normalized = re.sub(r"\s*[-—–]\s*", "–", normalized)
    return normalized


def _medium(item: BibliographyItem) -> str:
    if item.medium:
        return item.medium.strip("[] ")
    if item.kind in {"dataset", "legal", "preprint", "web"}:
        return "Электронный ресурс"
    return "Текст"


def _publication(item: BibliographyItem, separator: str) -> str:
    place = _normalize_text(item.place, separator).rstrip(". ")
    publisher = _normalize_text(item.publisher, separator).rstrip(". ")
    year = _normalize_text(item.year, separator).rstrip(". ")
    publication = f"{place}: {publisher}" if place and publisher else place or publisher
    if year:
        publication = f"{publication}, {year}" if publication else year
    return publication


def _format_structured_source(item: BibliographyItem, separator: str) -> str:
    authors = _normalize_text(item.authors, separator).rstrip(". ")
    title = _normalize_text(item.title, separator).rstrip(". ")
    responsibility = _normalize_text(item.contributors or item.authors, separator).rstrip(". ")
    container = _normalize_text(item.container, separator).rstrip(". ")

    description = f"{title} [{_medium(item)}]"
    if responsibility:
        description += f"/{responsibility}"
    if container:
        description += f"//{container}"
    if authors:
        description = f"{authors}. {description}"

    parts = [description]
    publication = _publication(item, separator)
    if publication:
        parts.append(publication)
    if item.issue:
        issue = _normalize_text(item.issue, separator)
        parts.append(issue if issue.startswith("№") else f"№ {issue}")
    if item.pages:
        pages = _normalize_text(item.pages, separator).rstrip(".")
        if re.fullmatch(r"\d+–\d+", pages):
            pages = f"С. {pages}"
        elif pages.isdigit():
            pages = f"{pages} с."
        parts.append(pages)
    if item.url:
        parts.append(f"URL: {item.url.strip().rstrip('. ')}")
    if item.access_date:
        parts.append(f"(дата обращения: {item.access_date.strip()})")
    return f" {separator} ".join(parts).rstrip(". ") + "."


def _author_name(value: str) -> tuple[str, str]:
    match = _SURNAME_FIRST.fullmatch(value) or _INITIALS_FIRST.fullmatch(value)
    if match is None:
        return value, ""
    return match["surname"].strip(), "".join(match["initials"].split())


def _author_group(authors: str) -> tuple[str, str]:
    suffix = _ADDITIONAL_AUTHORS.search(authors)
    names = authors[:suffix.start()] if suffix else authors
    people = [_author_name(name.strip()) for name in names.split(";") if name.strip()]
    if not people:
        return "", ""
    surname, initials = people[0]
    heading = f"{surname}, {initials}" if initials else surname
    responsibility = ", ".join(f"{initials} {surname}".strip() for surname, initials in people)
    if suffix:
        responsibility += f" {suffix[1].rstrip('.')}."
    return heading, responsibility


def _page_information(item: BibliographyItem, separator: str) -> str:
    pages = _normalize_text(item.pages, separator)
    match = _NUMBERED_PAGES.fullmatch(pages.rstrip("."))
    if match is None:
        return pages
    if match["end"]:
        return f"{match['label'] or 'С.'} {match['start']}-{match['end']}"
    if match["label"] or item.kind in {"article", "chapter", "conference"}:
        return f"{match['label'] or 'С.'} {match['start']}"
    return f"{match['start']} с."


def _online_information(item: BibliographyItem) -> str:
    parts = []
    if item.url:
        url = item.url.strip()
        candidate = re.sub(r"\\([:#%&_])", r"\1", url)
        if re.fullmatch(r"https?://[^\s{}\\]+", candidate, re.IGNORECASE):
            url = rf"\url{{{candidate}}}"
        parts.append(f"URL: {url}")
    if item.access_date:
        parts.append(f"(дата обращения: {item.access_date.strip()})")
    return " ".join(parts)


def _sentence(value: str) -> str:
    return value if value.endswith((".", "!", "?")) else f"{value}."


def _format_nir_master_source(item: BibliographyItem, separator: str) -> str:
    heading, responsibility = _author_group(_normalize_text(item.authors, separator))
    if item.contributors:
        contributors = _normalize_text(item.contributors, separator)
        responsibility = re.sub(r"(?<!\w)([^\W\d_]\.)\s+(?=[^\W\d_]\.)", r"\1", contributors)

    title = _normalize_text(item.title, separator).rstrip(". ")
    title_parts = [title]
    if item.kind == "book":
        title_parts = re.split(r":\s+(?![^«»]*»)", title, maxsplit=1)
    description = f"{title_parts[0].rstrip()} [{_medium(item)}]"
    if len(title_parts) == 2:
        description += f": {title_parts[1]}"
    if heading:
        description = f"{_sentence(heading)} {description}"
    if responsibility:
        description += f" / {responsibility}"

    container = _normalize_text(item.container, separator)
    volume = ""
    if item.kind == "article" and (match := _VOLUME_AT_END.fullmatch(container)):
        container, volume = match.groups()
    if container:
        description += f" // {container}"

    issue = _normalize_text(item.issue, separator)
    if re.fullmatch(r"\d+(?:[-–]\d+)?\.?", issue):
        issue = f"№ {issue}"
    parts = (
        description,
        _publication(item, separator),
        volume,
        issue,
        _page_information(item, separator),
        _online_information(item),
    )
    return f" {separator} ".join(_sentence(part) for part in parts if part)


def format_source(item: BibliographyItem, separator: str = "-", *, nir_master: bool = False) -> str:
    if not item.details:
        if nir_master:
            return _format_nir_master_source(item, separator)
        return _format_structured_source(item, separator)

    title = _normalize_text(item.title, separator).rstrip(". ")
    if item.kind == "web" and "Электронный ресурс" not in title:
        title = f"{title} [Электронный ресурс]"
    parts = [
        _normalize_text(part, separator).rstrip(". ")
        for part in (item.authors, title, item.details)
        if part
    ]
    return ". ".join(parts) + "."
