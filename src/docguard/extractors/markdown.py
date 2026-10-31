"""Extract explicit function-default claims from Markdown paragraphs."""

import ast
import re
from pathlib import Path
from typing import TypedDict

from markdown_it import MarkdownIt
from markdown_it.token import Token


class ExtractedClaim(TypedDict):
    """A Markdown claim with any reliably identified default details."""

    text: str
    function_name: str | None
    parameter_name: str | None
    value: object | None
    file_path: str
    line_number: int


_VALUE = r"""(?:-?\d+(?:\.\d+)?|true|false|'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")"""
_DEFAULT_CLAIM = re.compile(
    rf"\bdefault\s+(?P<parameter>[A-Za-z_]\w*)"
    rf"(?:\s+for\s+`?(?P<function>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)`?)?"
    rf"\s+is\s+(?P<value>{_VALUE})",
    re.IGNORECASE,
)
_DEFAULT_CONTEXT = re.compile(
    r"\bdefault\s+(?P<parameter>[A-Za-z_]\w*)"
    r"(?:\s+for\s+`?(?P<function>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)`?)?",
    re.IGNORECASE,
)
_FUNCTION_CALL = re.compile(
    r"(?P<function>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*\((?P<arguments>[^()]*)\)"
)
_KEYWORD_ARGUMENT = re.compile(
    r"(?P<parameter>[A-Za-z_]\w*)\s*=\s*"
    r"(?P<value>'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|[^,]+)"
)
_FUNCTION_REFERENCE = re.compile(
    r"(?<![\w.])(?P<function>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*\("
)


def extract_markdown(source_path: str | Path) -> list[ExtractedClaim]:
    """Extract default claims from Markdown paragraphs without executing examples.

    Supported forms include ``the default limit for NAME is VALUE`` and
    inline-code calls such as ``NAME(limit=VALUE)``. Other prose is ignored.
    """
    path = Path(source_path)
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise OSError(f"Could not read Markdown file {path}: {exc}") from exc

    claims: list[ExtractedClaim] = []
    current_line: int | None = None

    for token in MarkdownIt().parse(source):
        if token.type == "paragraph_open" and token.map is not None:
            current_line = token.map[0] + 1
        elif token.type == "inline" and current_line is not None:
            _extract_paragraph_claims(token, path, current_line, claims)
        elif token.type == "paragraph_close":
            current_line = None

    return claims


class FunctionReference(TypedDict):
    """A function call mentioned in Markdown."""

    name: str
    text: str
    file_path: str
    line_number: int


def extract_function_references(source_path: str | Path) -> list[FunctionReference]:
    """Extract simple function-call references from Markdown prose and inline code.

    Fenced code blocks are ignored. This intentionally recognizes call-shaped
    names such as ``subtract()`` rather than attempting general language parsing.
    """
    path = Path(source_path)
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise OSError(f"Could not read Markdown file {path}: {exc}") from exc

    references: list[FunctionReference] = []
    seen: set[tuple[str, int, str]] = set()
    source_lines = source.splitlines()

    for token in MarkdownIt().parse(source):
        if token.type in {"paragraph_open", "heading_open"} and token.map is not None:
            for line_index in range(token.map[0], token.map[1]):
                text = source_lines[line_index].strip()
                line_number = line_index + 1
                for match in _FUNCTION_REFERENCE.finditer(text):
                    reference = {
                        "name": match.group("function"),
                        "text": text,
                        "file_path": str(path),
                        "line_number": line_number,
                    }
                    key = (reference["name"], line_number, text)
                    if key not in seen:
                        references.append(reference)
                        seen.add(key)

    return references


def _extract_paragraph_claims(
    token: Token,
    path: Path,
    line_number: int,
    claims: list[ExtractedClaim],
) -> None:
    content = token.content
    paragraph_claims: list[ExtractedClaim] = []

    for match in _DEFAULT_CLAIM.finditer(content):
        paragraph_claims.append(
            _make_claim(
                content,
                path,
                line_number,
                match.group("function"),
                match.group("parameter"),
                _parse_value(match.group("value")),
            )
        )

    if not paragraph_claims:
        match = _DEFAULT_CONTEXT.search(content)
        if match:
            paragraph_claims.append(
                _make_claim(
                    content,
                    path,
                    line_number,
                    match.group("function"),
                    match.group("parameter"),
                    None,
                )
            )

    for child in token.children or []:
        if child.type != "code_inline":
            continue
        for call in _FUNCTION_CALL.finditer(child.content):
            for argument in _KEYWORD_ARGUMENT.finditer(call.group("arguments")):
                raw_value = argument.group("value").strip()
                value = _parse_value(raw_value)
                paragraph_claims.append(
                    _make_claim(
                        content,
                        path,
                        line_number,
                        call.group("function"),
                        argument.group("parameter"),
                        value,
                    )
                )

    seen: set[tuple[str | None, str | None, str]] = set()
    for claim in paragraph_claims:
        key = (
            claim["function_name"],
            claim["parameter_name"],
            repr(claim["value"]),
        )
        if key not in seen:
            claims.append(claim)
            seen.add(key)


def _make_claim(
    text: str,
    path: Path,
    line_number: int,
    function_name: str | None,
    parameter_name: str | None,
    value: object | None,
) -> ExtractedClaim:
    return {
        "text": text,
        "function_name": function_name,
        "parameter_name": parameter_name,
        "value": value,
        "file_path": str(path),
        "line_number": line_number,
    }


def _parse_value(raw_value: str) -> object | None:
    normalized = raw_value.strip()
    if normalized.casefold() == "true":
        return True
    if normalized.casefold() == "false":
        return False

    try:
        return ast.literal_eval(normalized)
    except (ValueError, SyntaxError):
        return None
