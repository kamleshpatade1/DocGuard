"""Flask API for scanning pasted Python and Markdown source."""

import logging
import re
import tempfile
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request
from werkzeug.exceptions import RequestEntityTooLarge

from docguard.engine import run_engine
from docguard.models import Finding

_FUNCTION_FROM_MISSING_MESSAGE = re.compile(r"`([^`]+)\(\)`")
_FUNCTION_FROM_MISMATCH_MESSAGE = re.compile(r"^(.+)\.[^. ]+ is documented")
_SEVERITY_BY_RULE = {
    "FUNCTION_NOT_FOUND": "high",
    "VALUE_MISMATCH": "medium",
}


def create_app() -> Flask:
    """Create the web API application."""
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

    @app.errorhandler(RequestEntityTooLarge)
    def request_too_large(_error: RequestEntityTooLarge):
        return jsonify(error="Request is too large; the maximum size is 2 MB."), 413

    @app.post("/api/scan")
    def scan():
        if not request.is_json:
            return jsonify(error="Send a JSON request with documentation and python_source fields."), 400

        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="Request body must be a JSON object."), 400

        documentation = payload.get("documentation")
        python_source = payload.get("python_source")
        if not isinstance(documentation, str) or not isinstance(python_source, str):
            return jsonify(
                error="Both documentation and python_source must be strings."
            ), 400
        if not documentation.strip() or not python_source.strip():
            return jsonify(
                error="Documentation and Python source must both contain non-empty text."
            ), 400
        documentation_filename = payload.get("documentation_filename", "documentation.md")
        python_filename = payload.get("python_filename", "source.py")
        if not isinstance(documentation_filename, str) or not isinstance(python_filename, str):
            return jsonify(error="Input filenames must be strings."), 400
        documentation_filename = _safe_display_name(documentation_filename, "documentation.md")
        python_filename = _safe_display_name(python_filename, "source.py")

        try:
            findings = _scan_text(documentation, python_source)
        except SyntaxError as exc:
            syntax_error = exc.__cause__
            if isinstance(syntax_error, SyntaxError):
                line_number = syntax_error.lineno
                message = syntax_error.msg
            else:
                line_number = exc.lineno
                message = exc.msg or "Syntax could not be parsed."
            line = f" at line {line_number}" if line_number is not None else ""
            return jsonify(error=f"Python source has invalid syntax{line}: {message}"), 422
        except (OSError, UnicodeError):
            app.logger.exception("Could not read temporary scan input")
            return jsonify(error="The scan inputs could not be read."), 500
        except Exception:
            app.logger.exception("Unexpected error while scanning submitted source")
            return jsonify(error="The scan failed unexpectedly. Please try again."), 500

        return jsonify(
            findings=[
                _serialize_finding(
                    finding,
                    locations,
                    documentation_filename,
                    python_filename,
                )
                for finding, locations in _group_findings(findings)
            ]
        )

    return app


def _scan_text(documentation: str, python_source: str) -> list[Finding]:
    """Adapt the engine's existing path-based interface to submitted text."""
    with tempfile.TemporaryDirectory(prefix="docguard-scan-") as directory:
        documentation_path = Path(directory) / "documentation.md"
        python_source_path = Path(directory) / "source.py"
        documentation_path.write_text(documentation, encoding="utf-8")
        python_source_path.write_text(python_source, encoding="utf-8")
        return run_engine(documentation_path, python_source_path)


def _group_findings(
    findings: list[Finding],
) -> list[tuple[Finding, list[dict[str, Any]]]]:
    """Group repeated semantic findings while keeping each documentation location."""
    grouped: dict[
        tuple[str, str, str, str | None, int | None, str | None, str],
        tuple[Finding, list[dict[str, Any]]],
    ] = {}

    for finding in findings:
        key = (
            finding.rule_id,
            finding.title,
            finding.message,
            finding.evidence_file,
            finding.evidence_line,
            finding.evidence_text,
            finding.confidence,
        )
        if key not in grouped:
            grouped[key] = (finding, [])

        locations = grouped[key][1]
        location = {
            "file": Path(finding.documentation_file).name,
            "line": finding.documentation_line,
            "text": finding.documented_text,
        }
        if location not in locations:
            locations.append(location)

    return list(grouped.values())


def _serialize_finding(
    finding: Finding,
    documentation_locations: list[dict[str, Any]],
    documentation_filename: str,
    python_filename: str,
) -> dict[str, Any]:
    function_name = _extract_function_name(finding)
    return {
        "rule_id": finding.rule_id,
        "title": finding.title,
        "message": finding.message,
        "severity": _SEVERITY_BY_RULE.get(finding.rule_id, "low"),
        "function_name": function_name,
        "confidence": finding.confidence,
        "documentation_file": documentation_filename,
        "documentation_line": finding.documentation_line,
        "documented_text": finding.documented_text,
        "documentation_locations": [
            {**location, "file": documentation_filename}
            for location in documentation_locations
        ],
        "evidence_file": python_filename if finding.evidence_file else None,
        "evidence_line": finding.evidence_line,
        "evidence_text": finding.evidence_text,
    }


def _safe_display_name(filename: str, fallback: str) -> str:
    name = Path(filename.replace("\\", "/")).name
    return name or fallback


def _extract_function_name(finding: Finding) -> str | None:
    if finding.rule_id == "FUNCTION_NOT_FOUND":
        match = _FUNCTION_FROM_MISSING_MESSAGE.search(finding.message)
        return match.group(1) if match else None
    if finding.rule_id == "VALUE_MISMATCH":
        match = _FUNCTION_FROM_MISMATCH_MESSAGE.match(finding.message)
        return match.group(1) if match else None
    return None


app = create_app()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host="127.0.0.1", port=5000, debug=False)
