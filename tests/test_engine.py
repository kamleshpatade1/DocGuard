from docguard.engine import run_engine
from docguard.models import Finding


def test_engine_finds_mismatching_documented_default(tmp_path):
    documentation = tmp_path / "api.md"
    python_source = tmp_path / "service.py"
    documentation.write_text(
        "The default limit for `get_students` is 30.\n",
        encoding="utf-8",
    )
    python_source.write_text(
        "def get_students(limit=50):\n    return []\n",
        encoding="utf-8",
    )

    findings = run_engine(documentation, python_source)

    assert len(findings) == 1
    assert isinstance(findings[0], Finding)
    assert findings[0].rule_id == "VALUE_MISMATCH"
    assert findings[0].documentation_file == str(documentation)
    assert findings[0].evidence_file == str(python_source)


def test_engine_returns_no_findings_for_matching_default(tmp_path):
    documentation = tmp_path / "api.md"
    python_source = tmp_path / "service.py"
    documentation.write_text(
        "The default limit for `get_students` is 30.\n",
        encoding="utf-8",
    )
    python_source.write_text(
        "def get_students(limit=30):\n    return []\n",
        encoding="utf-8",
    )

    assert run_engine(documentation, python_source) == []


def test_engine_returns_no_findings_for_empty_inputs(tmp_path):
    documentation = tmp_path / "api.md"
    python_source = tmp_path / "service.py"
    documentation.write_text("", encoding="utf-8")
    python_source.write_text("", encoding="utf-8")

    assert run_engine(documentation, python_source) == []
