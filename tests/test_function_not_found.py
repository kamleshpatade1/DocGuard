from docguard.engine import run_engine
from docguard.extractors.markdown import extract_function_references
from docguard.extractors.python_ast import extract_python
from docguard.models import Finding
from docguard.rules.function_not_found import find_missing_functions


def test_reports_documented_function_missing_from_python(tmp_path):
    documentation = tmp_path / "guide.md"
    python_source = tmp_path / "service.py"
    documentation.write_text("Call `subtract()` to calculate the difference.\n", encoding="utf-8")
    python_source.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

    findings = find_missing_functions(
        extract_function_references(documentation),
        extract_python(python_source),
        python_source,
    )

    assert len(findings) == 1
    assert isinstance(findings[0], Finding)
    assert findings[0].rule_id == "FUNCTION_NOT_FOUND"
    assert "subtract" in findings[0].message
    assert findings[0].documentation_line == 1


def test_does_not_report_function_that_exists(tmp_path):
    documentation = tmp_path / "guide.md"
    python_source = tmp_path / "service.py"
    documentation.write_text("Call `add()` for the sum.\n", encoding="utf-8")
    python_source.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

    assert find_missing_functions(
        extract_function_references(documentation),
        extract_python(python_source),
        python_source,
    ) == []


def test_engine_includes_function_not_found_rule(tmp_path):
    documentation = tmp_path / "guide.md"
    python_source = tmp_path / "service.py"
    documentation.write_text("Call `subtract()` for the difference.\n", encoding="utf-8")
    python_source.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

    findings = run_engine(documentation, python_source)

    assert [finding.rule_id for finding in findings] == ["FUNCTION_NOT_FOUND"]


def test_deduplicates_repeated_function_reference_on_same_line(tmp_path):
    documentation = tmp_path / "guide.md"
    python_source = tmp_path / "service.py"
    documentation.write_text("Use `subtract()`; `subtract()` is convenient.\n", encoding="utf-8")
    python_source.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

    references = extract_function_references(documentation)
    findings = find_missing_functions(references, extract_python(python_source), python_source)

    assert len(references) == 1
    assert len(findings) == 1


def test_extracts_plain_prose_reference_with_its_source_line(tmp_path):
    documentation = tmp_path / "guide.md"
    documentation.write_text(
        "This page describes the service.\n\n"
        "Calling subtract() returns the difference.\n",
        encoding="utf-8",
    )

    references = extract_function_references(documentation)

    assert len(references) == 1
    assert references[0]["name"] == "subtract"
    assert references[0]["line_number"] == 3
    assert references[0]["file_path"] == str(documentation)


def test_ignores_call_shapes_inside_fenced_code_blocks(tmp_path):
    documentation = tmp_path / "guide.md"
    documentation.write_text("```python\nsubtract()\n```\n", encoding="utf-8")

    assert extract_function_references(documentation) == []
