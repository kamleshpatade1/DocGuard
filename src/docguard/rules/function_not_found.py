"""Detect documented function calls that are absent from Python source."""

from pathlib import Path

from docguard.extractors.markdown import FunctionReference
from docguard.extractors.python_ast import ExtractedFunction
from docguard.models import Finding


def find_missing_functions(
    references: list[FunctionReference],
    functions: list[ExtractedFunction],
    python_source_path: str | Path,
) -> list[Finding]:
    """Report each uniquely referenced function not found in extracted source."""
    findings: list[Finding] = []
    seen: set[tuple[str, str, int]] = set()
    source_path = str(python_source_path)

    for reference in references:
        if _is_defined(reference["name"], functions):
            continue

        key = (reference["file_path"], reference["line_number"], reference["name"])
        if key in seen:
            continue
        seen.add(key)

        findings.append(
            Finding(
                rule_id="FUNCTION_NOT_FOUND",
                title="Documented function is not defined",
                message=(
                    f"Documentation references `{reference['name']}()`, "
                    "but no matching function was found in the Python source."
                ),
                confidence="medium",
                documentation_file=reference["file_path"],
                documentation_line=reference["line_number"],
                documented_text=reference["text"],
                evidence_file=source_path,
                evidence_text="No matching function definition was found in this source file.",
            )
        )

    return findings


def _is_defined(name: str, functions: list[ExtractedFunction]) -> bool:
    if any(function["name"] == name for function in functions):
        return True

    return any(function["name"].rsplit(".", maxsplit=1)[-1] == name for function in functions)
