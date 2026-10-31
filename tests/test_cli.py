from docguard.cli import main


def test_cli_displays_findings_and_returns_nonzero(tmp_path, capsys):
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

    exit_code = main([str(documentation), str(python_source)])

    output = capsys.readouterr()
    assert exit_code == 1
    assert "VALUE_MISMATCH" in output.out
    assert "default 30" in output.out
    assert f"Documentation: {documentation}:1" in output.out
    assert f"Evidence: {python_source}:1" in output.out
    assert "Confidence: HIGH" in output.out


def test_cli_returns_zero_when_no_findings(tmp_path, capsys):
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

    exit_code = main([str(documentation), str(python_source)])

    output = capsys.readouterr()
    assert exit_code == 0
    assert "No documentation drift found." in output.out


def test_cli_reports_missing_input_file(tmp_path, capsys):
    python_source = tmp_path / "service.py"
    python_source.write_text("def get_students(limit=30):\n    return []\n", encoding="utf-8")
    missing_documentation = tmp_path / "missing.md"

    exit_code = main([str(missing_documentation), str(python_source)])

    output = capsys.readouterr()
    assert exit_code == 2
    assert str(missing_documentation) in output.err
    assert "not found or not a file" in output.err


def test_cli_reports_python_syntax_error(tmp_path, capsys):
    documentation = tmp_path / "api.md"
    python_source = tmp_path / "invalid.py"
    documentation.write_text("The default limit for `get_students` is 30.\n", encoding="utf-8")
    python_source.write_text("def broken(:\n    pass\n", encoding="utf-8")

    exit_code = main([str(documentation), str(python_source)])

    output = capsys.readouterr()
    assert exit_code == 2
    assert "Invalid Python syntax" in output.err
