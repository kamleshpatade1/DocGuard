"""Assign confidence levels from evidence already stored in findings."""

from typing import Literal

from docguard.models import Finding

Confidence = Literal["high", "medium", "low"]


def score_finding(finding: Finding) -> Confidence:
    """Choose confidence based on documentation and source evidence completeness."""
    documentation_is_complete = (
        bool(finding.documentation_file.strip())
        and finding.documentation_line > 0
        and bool(finding.documented_text.strip())
    )
    evidence_parts = (
        bool(finding.evidence_file and finding.evidence_file.strip())
        + (finding.evidence_line is not None)
        + bool(finding.evidence_text and finding.evidence_text.strip())
    )

    if documentation_is_complete and evidence_parts == 3:
        return "high"
    if documentation_is_complete and evidence_parts > 0:
        return "medium"
    return "low"


def score_findings(findings: list[Finding]) -> list[Finding]:
    """Return copies of findings with confidence set from available evidence."""
    return [
        finding.model_copy(update={"confidence": score_finding(finding)})
        for finding in findings
    ]
