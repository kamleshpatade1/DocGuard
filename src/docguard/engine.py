"""Orchestrate documentation drift extraction and detection."""

from pathlib import Path

from docguard.extractors.markdown import extract_function_references, extract_markdown
from docguard.extractors.python_ast import extract_python
from docguard.mapper import map_claims_to_facts
from docguard.models import Finding
from docguard.rules.function_not_found import find_missing_functions
from docguard.rules.value_mismatch import find_value_mismatches
from docguard.scoring import score_findings


def run_engine(
    documentation_path: str | Path,
    python_source_path: str | Path,
) -> list[Finding]:
    """Find documented defaults that differ from Python defaults.

    File and syntax errors are raised by the extractors with their source path;
    Python source and Markdown code examples are parsed, never executed.
    """
    claims = extract_markdown(documentation_path)
    function_references = extract_function_references(documentation_path)
    functions = extract_python(python_source_path)
    mapped_defaults = map_claims_to_facts(claims, functions)
    findings = [
        *find_value_mismatches(mapped_defaults),
        *find_missing_functions(function_references, functions, python_source_path),
    ]
    return score_findings(findings)
