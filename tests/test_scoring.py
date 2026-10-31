from docguard.models import Finding
from docguard.scoring import score_finding, score_findings


def _finding(**overrides) -> Finding:
    fields = {
        "rule_id": "VALUE_MISMATCH",
        "title": "Default differs",
        "message": "The documented default differs from Python.",
        "documentation_file": "docs/api.md",
        "documentation_line": 4,
        "documented_text": "The default limit is 30.",
        "evidence_file": "src/service.py",
        "evidence_line": 2,
        "evidence_text": "get_students.limit default is 50",
    }
    fields.update(overrides)
    return Finding(**fields)


def test_complete_documentation_and_source_evidence_is_high():
    assert score_finding(_finding()) == "high"


def test_partial_source_evidence_is_medium():
    finding = _finding(evidence_line=None)

    assert score_finding(finding) == "medium"


def test_no_source_evidence_is_low():
    finding = _finding(
        evidence_file=None,
        evidence_line=None,
        evidence_text=None,
    )

    assert score_finding(finding) == "low"


def test_missing_documented_text_is_low_even_with_source_evidence():
    assert score_finding(_finding(documented_text="  ")) == "low"


def test_score_findings_returns_scored_copies_without_mutating_inputs():
    original = _finding(confidence="low")

    scored = score_findings([original])

    assert scored[0].confidence == "high"
    assert scored[0] is not original
    assert original.confidence == "low"


def test_score_findings_handles_empty_list():
    assert score_findings([]) == []
