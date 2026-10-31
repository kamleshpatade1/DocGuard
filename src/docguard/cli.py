"""Command-line interface for DocGuard."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from docguard.engine import run_engine
from docguard.models import Finding


def main(argv: Sequence[str] | None = None) -> int:
    """Run DocGuard for one Markdown file and one Python source file."""
    parser = argparse.ArgumentParser(
        prog="docguard",
        description="Check documentation claims against Python defaults.",
    )
    parser.add_argument("documentation", help="path to the Markdown documentation file")
    parser.add_argument("python_source", help="path to the Python source file")
    arguments = parser.parse_args(argv)

    documentation_path = Path(arguments.documentation)
    python_source_path = Path(arguments.python_source)
    if not documentation_path.is_file():
        print(
            f"docguard: documentation file not found or not a file: {documentation_path}",
            file=sys.stderr,
        )
        return 2
    if not python_source_path.is_file():
        print(
            f"docguard: Python source file not found or not a file: {python_source_path}",
            file=sys.stderr,
        )
        return 2

    try:
        findings = run_engine(documentation_path, python_source_path)
    except (OSError, SyntaxError) as exc:
        print(f"docguard: error: {exc}", file=sys.stderr)
        return 2

    if not findings:
        print("No documentation drift found.")
        return 0

    for finding in findings:
        _print_finding(finding)
    return 1


def _print_finding(finding: Finding) -> None:
    evidence_file = finding.evidence_file or "unknown"
    evidence_line = str(finding.evidence_line) if finding.evidence_line is not None else "?"
    print(f"{finding.rule_id}: {finding.message}")
    print(f"  Documentation: {finding.documentation_file}:{finding.documentation_line}")
    print(f"  Evidence: {evidence_file}:{evidence_line}")
    print(f"  Confidence: {finding.confidence.upper()}")
