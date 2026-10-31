"""Detect documentation claims that disagree with Python defaults."""

import ast

from docguard.mapper import MappedDefault
from docguard.models import Finding


def find_value_mismatches(matches: list[MappedDefault]) -> list[Finding]:
    """Return a finding for each documented value that differs from Python."""
    findings: list[Finding] = []
    seen: set[tuple[str, int, str, int, str, str, str, str, str]] = set()

    for match in matches:
        claim = match["claim"]
        fact = match["fact"]
        documented = _parse_literal(claim.value)
        actual = _parse_literal(fact.value)
        if documented is _INVALID or actual is _INVALID:
            continue
        if _values_equal(documented, actual):
            continue

        key = (
            claim.file_path,
            claim.line_number,
            fact.file_path,
            fact.line_number,
            match["function_name"],
            match["parameter_name"],
            claim.text,
            claim.value or "",
            fact.value or "",
        )
        if key in seen:
            continue
        seen.add(key)

        findings.append(
            Finding(
                rule_id="VALUE_MISMATCH",
                title="Documented default does not match Python",
                message=(
                    f"{match['function_name']}.{match['parameter_name']} is documented "
                    f"with default {documented!r}, but Python uses {actual!r}."
                ),
                confidence="high",
                documentation_file=claim.file_path,
                documentation_line=claim.line_number,
                documented_text=claim.text,
                evidence_file=fact.file_path,
                evidence_line=fact.line_number,
                evidence_text=fact.text,
            )
        )

    return findings


_INVALID = object()


def _parse_literal(value: str | None) -> object:
    if value is None:
        return _INVALID
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return _INVALID


def _values_equal(left: object, right: object) -> bool:
    if type(left) is bool or type(right) is bool:
        return type(left) is bool and type(right) is bool and left == right
    if type(left) in (int, float) and type(right) in (int, float):
        return left == right
    return type(left) is type(right) and left == right
