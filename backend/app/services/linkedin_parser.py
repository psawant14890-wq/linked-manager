"""
Parses LinkedIn's official "Download your data" export.

LinkedIn ships a zip containing many CSVs; the ones this app cares about
are typically named (export format has shifted slightly over the years,
so column lookups below are tolerant of common variants):

  Messages.csv     -- columns like: CONVERSATION ID, CONVERSATION TITLE,
                       FROM, TO, DATE, SUBJECT, CONTENT
  Shares.csv       -- columns like: Date, ShareLink, ShareCommentary,
                       SharedUrl, Visibility  (this is the user's own posts)
  Connections.csv  -- has a few preamble lines before the real header row,
                       columns like: First Name, Last Name, Company,
                       Position, Connected On

This module is defensive: real exports vary by region/date and sometimes
have different casing, extra preamble rows, or missing optional columns.
Every parse function returns (rows_parsed, errors) so the caller can build
an ImportLog entry that tells the user exactly what happened.
"""

import csv
import io
import zipfile
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ParsedMessage:
    sender_name: str
    content: str
    received_at: datetime | None


@dataclass
class ParsedPost:
    content: str
    posted_at: datetime | None


@dataclass
class ParsedConnection:
    name: str
    company: str | None
    title: str | None
    connected_at: datetime | None


@dataclass
class FileParseResult:
    filename: str
    status: str  # success | partial | failed
    rows_imported: int = 0
    errors: list[str] = field(default_factory=list)
    messages: list[ParsedMessage] = field(default_factory=list)
    posts: list[ParsedPost] = field(default_factory=list)
    connections: list[ParsedConnection] = field(default_factory=list)


# LinkedIn has used a few different date formats across export versions.
_DATE_FORMATS = [
    "%m/%d/%y, %H:%M %p",
    "%m/%d/%Y, %H:%M %p",
    "%Y-%m-%d %H:%M:%S",
    "%m/%d/%y",
    "%m/%d/%Y",
]


def _parse_date(value: str | None) -> datetime | None:
    if not value or not value.strip():
        return None
    value = value.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _get_field(row: dict, *candidates: str) -> str | None:
    """Case-insensitive, whitespace-tolerant lookup across known column-name variants."""
    normalized = {k.strip().lower(): v for k, v in row.items() if k}
    for candidate in candidates:
        val = normalized.get(candidate.strip().lower())
        if val is not None and val.strip() != "":
            return val.strip()
    return None


def parse_messages_csv(raw_bytes: bytes, filename: str = "Messages.csv") -> FileParseResult:
    result = FileParseResult(filename=filename, status="success")
    try:
        text = raw_bytes.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None:
            result.status = "failed"
            result.errors.append("File appears empty or has no header row.")
            return result

        for i, row in enumerate(reader, start=2):  # row 1 is header
            try:
                sender = _get_field(row, "FROM", "Sender")
                content = _get_field(row, "CONTENT", "Message")
                date_str = _get_field(row, "DATE", "Sent At")

                if not sender or not content:
                    result.errors.append(f"Row {i}: missing sender or content, skipped.")
                    continue

                result.messages.append(
                    ParsedMessage(sender_name=sender, content=content, received_at=_parse_date(date_str))
                )
                result.rows_imported += 1
            except Exception as exc:  # noqa: BLE001 -- intentionally broad, one bad row shouldn't kill the import
                result.errors.append(f"Row {i}: {exc}")

        if result.errors and result.rows_imported > 0:
            result.status = "partial"
        elif result.rows_imported == 0:
            result.status = "failed"

    except Exception as exc:  # noqa: BLE001
        result.status = "failed"
        result.errors.append(f"Could not read file: {exc}")

    return result


def parse_shares_csv(raw_bytes: bytes, filename: str = "Shares.csv") -> FileParseResult:
    result = FileParseResult(filename=filename, status="success")
    try:
        text = raw_bytes.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None:
            result.status = "failed"
            result.errors.append("File appears empty or has no header row.")
            return result

        for i, row in enumerate(reader, start=2):
            try:
                content = _get_field(row, "ShareCommentary", "Commentary", "Content")
                date_str = _get_field(row, "Date", "ShareDate")

                if not content:
                    result.errors.append(f"Row {i}: empty post content, skipped.")
                    continue

                result.posts.append(ParsedPost(content=content, posted_at=_parse_date(date_str)))
                result.rows_imported += 1
            except Exception as exc:  # noqa: BLE001
                result.errors.append(f"Row {i}: {exc}")

        if result.errors and result.rows_imported > 0:
            result.status = "partial"
        elif result.rows_imported == 0:
            result.status = "failed"

    except Exception as exc:  # noqa: BLE001
        result.status = "failed"
        result.errors.append(f"Could not read file: {exc}")

    return result


def parse_connections_csv(raw_bytes: bytes, filename: str = "Connections.csv") -> FileParseResult:
    """
    LinkedIn's Connections.csv has a few "Notes:" preamble lines before
    the real header. We scan for the first line that looks like a header
    (contains "First Name") rather than assuming a fixed offset.
    """
    result = FileParseResult(filename=filename, status="success")
    try:
        text = raw_bytes.decode("utf-8-sig", errors="replace")
        lines = text.splitlines()

        header_idx = None
        for idx, line in enumerate(lines):
            if "first name" in line.lower():
                header_idx = idx
                break

        if header_idx is None:
            result.status = "failed"
            result.errors.append("Could not locate header row (expected a 'First Name' column).")
            return result

        csv_body = "\n".join(lines[header_idx:])
        reader = csv.DictReader(io.StringIO(csv_body))

        for i, row in enumerate(reader, start=header_idx + 2):
            try:
                first = _get_field(row, "First Name") or ""
                last = _get_field(row, "Last Name") or ""
                name = f"{first} {last}".strip()
                company = _get_field(row, "Company")
                title = _get_field(row, "Position", "Title")
                date_str = _get_field(row, "Connected On")

                if not name:
                    result.errors.append(f"Row {i}: missing name, skipped.")
                    continue

                result.connections.append(
                    ParsedConnection(name=name, company=company, title=title, connected_at=_parse_date(date_str))
                )
                result.rows_imported += 1
            except Exception as exc:  # noqa: BLE001
                result.errors.append(f"Row {i}: {exc}")

        if result.errors and result.rows_imported > 0:
            result.status = "partial"
        elif result.rows_imported == 0:
            result.status = "failed"

    except Exception as exc:  # noqa: BLE001
        result.status = "failed"
        result.errors.append(f"Could not read file: {exc}")

    return result


# Filename patterns we recognize, mapped to their parser. Matching is
# case-insensitive substring matching since LinkedIn occasionally renames
# files slightly between export format versions.
_PARSERS = {
    "messages": parse_messages_csv,
    "shares": parse_shares_csv,
    "connections": parse_connections_csv,
}


def parse_upload(filename: str, raw_bytes: bytes) -> list[FileParseResult]:
    """
    Entry point for the /import endpoint. Accepts either a single CSV
    (filename tells us which parser to use) or a zip containing multiple
    LinkedIn export CSVs, and returns one FileParseResult per file found.
    """
    lower = filename.lower()

    if lower.endswith(".zip"):
        results: list[FileParseResult] = []
        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                matched_any = False
                for name in zf.namelist():
                    base = name.rsplit("/", 1)[-1].lower()
                    if not base.endswith(".csv"):
                        continue
                    for key, parser in _PARSERS.items():
                        if key in base:
                            matched_any = True
                            with zf.open(name) as f:
                                results.append(parser(f.read(), filename=base))
                            break
                if not matched_any:
                    results.append(
                        FileParseResult(
                            filename=filename,
                            status="failed",
                            errors=[
                                "Zip did not contain any recognized files "
                                "(expected Messages.csv, Shares.csv, or Connections.csv)."
                            ],
                        )
                    )
        except zipfile.BadZipFile:
            results.append(FileParseResult(filename=filename, status="failed", errors=["Not a valid zip file."]))
        return results

    # Single CSV upload -- infer type from filename
    for key, parser in _PARSERS.items():
        if key in lower:
            return [parser(raw_bytes, filename=filename)]

    return [
        FileParseResult(
            filename=filename,
            status="failed",
            errors=[
                "Could not determine file type from filename. "
                "Expected the name to contain 'Messages', 'Shares', or 'Connections'."
            ],
        )
    ]
