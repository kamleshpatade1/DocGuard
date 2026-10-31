import web.backend.app as backend
from web.backend.app import create_app


def test_scan_returns_value_mismatch_finding():
    client = create_app().test_client()

    response = client.post(
        "/api/scan",
        json={
            "documentation": "The default limit for `get_students` is 30.\n",
            "python_source": "def get_students(limit=50):\n    return []\n",
        },
    )

    assert response.status_code == 200
    finding = response.get_json()["findings"][0]
    assert finding["rule_id"] == "VALUE_MISMATCH"
    assert finding["function_name"] == "get_students"
    assert finding["severity"] == "medium"
    assert finding["documentation_file"] == "documentation.md"
    assert finding["evidence_file"] == "source.py"
    assert finding["documentation_locations"] == [
        {
            "file": "documentation.md",
            "line": 1,
            "text": "The default limit for `get_students` is 30.",
        }
    ]


def test_scan_groups_repeated_default_mismatch_and_preserves_locations():
    client = create_app().test_client()

    response = client.post(
        "/api/scan",
        json={
            "documentation": (
                "The default limit for `get_students` is 30.\n\n"
                "The default limit for `get_students` is 30.\n"
            ),
            "python_source": "def get_students(limit=50):\n    return []\n",
        },
    )

    assert response.status_code == 200
    findings = response.get_json()["findings"]
    assert len(findings) == 1
    assert findings[0]["documentation_locations"] == [
        {
            "file": "documentation.md",
            "line": 1,
            "text": "The default limit for `get_students` is 30.",
        },
        {
            "file": "documentation.md",
            "line": 3,
            "text": "The default limit for `get_students` is 30.",
        },
    ]


def test_scan_keeps_distinct_mismatch_issues_and_reports_input_filenames():
    client = create_app().test_client()

    response = client.post(
        "/api/scan",
        json={
            "documentation": (
                "The default limit for `get_students` is 30.\n"
                "The default active for `get_students` is false.\n"
            ),
            "python_source": "def get_students(limit=50, active=True):\n    return []\n",
            "documentation_filename": "docs/students.markdown",
            "python_filename": "src/students.py",
        },
    )

    assert response.status_code == 200
    findings = response.get_json()["findings"]
    assert len(findings) == 2
    assert {finding["documentation_file"] for finding in findings} == {"students.markdown"}
    assert {finding["evidence_file"] for finding in findings} == {"students.py"}


def test_scan_sanitizes_display_filenames():
    client = create_app().test_client()

    response = client.post(
        "/api/scan",
        json={
            "documentation": "The default limit for `get_students` is 30.\n",
            "python_source": "def get_students(limit=50):\n    return []\n",
            "documentation_filename": "../../private/docs.md",
            "python_filename": "../../private/source.py",
        },
    )

    assert response.status_code == 200
    finding = response.get_json()["findings"][0]
    assert finding["documentation_file"] == "docs.md"
    assert finding["evidence_file"] == "source.py"


def test_scan_reports_documented_function_missing_from_source():
    client = create_app().test_client()

    response = client.post(
        "/api/scan",
        json={
            "documentation": "Call `subtract()` to find the difference.\n",
            "python_source": "def add(a, b):\n    return a + b\n",
        },
    )

    assert response.status_code == 200
    finding = response.get_json()["findings"][0]
    assert finding["rule_id"] == "FUNCTION_NOT_FOUND"
    assert finding["function_name"] == "subtract"
    assert finding["severity"] == "high"


def test_scan_returns_empty_findings_when_values_match():
    client = create_app().test_client()

    response = client.post(
        "/api/scan",
        json={
            "documentation": "The default limit for `get_students` is 30.\n",
            "python_source": "def get_students(limit=30):\n    return []\n",
        },
    )

    assert response.status_code == 200
    assert response.get_json() == {"findings": []}


def test_scan_rejects_empty_inputs_with_clear_error():
    client = create_app().test_client()

    response = client.post(
        "/api/scan",
        json={"documentation": "", "python_source": ""},
    )

    assert response.status_code == 400
    assert "must both contain non-empty text" in response.get_json()["error"]


def test_scan_rejects_whitespace_only_inputs():
    client = create_app().test_client()

    response = client.post(
        "/api/scan",
        json={"documentation": " \n ", "python_source": "\t"},
    )

    assert response.status_code == 400
    assert "must both contain non-empty text" in response.get_json()["error"]


def test_scan_rejects_missing_or_invalid_fields():
    client = create_app().test_client()

    response = client.post("/api/scan", json={"documentation": ""})

    assert response.status_code == 400
    assert "must be strings" in response.get_json()["error"]


def test_scan_reports_invalid_python_syntax():
    client = create_app().test_client()

    response = client.post(
        "/api/scan",
        json={"documentation": "API docs", "python_source": "def broken(:\n    pass\n"},
    )

    assert response.status_code == 422
    error = response.get_json()["error"]
    assert "invalid syntax at line 1" in error
    assert "docguard-scan-" not in error


def test_scan_rejects_non_json_request():
    client = create_app().test_client()

    response = client.post("/api/scan", data="not json")

    assert response.status_code == 400
    assert "JSON request" in response.get_json()["error"]


def test_scan_returns_clear_error_for_unexpected_backend_failure(monkeypatch):
    def fail_scan(_documentation, _python_source):
        raise RuntimeError("internal detail")

    monkeypatch.setattr(backend, "_scan_text", fail_scan)
    client = create_app().test_client()

    response = client.post(
        "/api/scan",
        json={"documentation": "API docs", "python_source": "def add(a, b): return a + b"},
    )

    assert response.status_code == 500
    assert response.get_json()["error"] == "The scan failed unexpectedly. Please try again."
