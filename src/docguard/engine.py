"""Orchestrate documentation drift extraction and detection."""

from pathlib import Path

from docguard.extractors.markdown import extract_markdown
from docguard.extractors.python_ast import extract_python
from docguard.mapper import map_claims_to_facts
from docguard.models import Finding
from docguard.rules.value_mismatch import find_value_mismatches


def run_engine(
    documentation_path: str | Path,
    python_source_path: str | Path,
) -> list[Finding]:
    """Find documented defaults that differ from Python defaults.

    File and syntax errors are raised by the extractors with their source path;
    Python source and Markdown code examples are parsed, never executed.
    """
    claims = extract_markdown(documentation_path)
    functions = extract_python(python_source_path)
    mapped_defaults = map_claims_to_facts(claims, functions)
    return find_value_mismatches(mapped_defaults)
