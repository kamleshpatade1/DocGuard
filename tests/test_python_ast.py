import pytest

from docguard.extractors.python_ast import extract_python


def test_extracts_function_without_defaults(tmp_path):
    source = tmp_path / "source.py"
    source.write_text("def greet(name):\n    return name\n", encoding="utf-8")

    assert extract_python(source) == [
        {
            "name": "greet",
            "line_number": 1,
            "file_path": str(source),
            "defaults": {},
        }
    ]


def test_extracts_one_or_multiple_defaults(tmp_path):
    source = tmp_path / "source.py"
    source.write_text(
        "def get_students(limit=50, active=True):\n    return []\n",
        encoding="utf-8",
    )

    result = extract_python(source)

    assert result[0]["defaults"] == {"limit": 50, "active": True}


def test_aligns_positional_defaults_with_final_parameters(tmp_path):
    source = tmp_path / "source.py"
    source.write_text("def example(a, b, c=10, d=20):\n    pass\n", encoding="utf-8")

    result = extract_python(source)

    assert result[0]["defaults"] == {"c": 10, "d": 20}


def test_preserves_boolean_and_string_defaults(tmp_path):
    source = tmp_path / "source.py"
    source.write_text(
        'def greet(name, active=True, message="Hello"):\n    return message\n',
        encoding="utf-8",
    )

    result = extract_python(source)

    assert result[0]["defaults"] == {"active": True, "message": "Hello"}


def test_extracts_methods_with_qualified_name(tmp_path):
    source = tmp_path / "source.py"
    source.write_text(
        "class StudentService:\n"
        "    def get_student(self, student_id=10):\n"
        "        return None\n",
        encoding="utf-8",
    )

    result = extract_python(source)

    assert result[0]["name"] == "StudentService.get_student"
    assert result[0]["line_number"] == 2
    assert result[0]["defaults"] == {"student_id": 10}


def test_extracts_keyword_only_defaults(tmp_path):
    source = tmp_path / "source.py"
    source.write_text(
        "def search(query, *, limit=10, active=False):\n    pass\n",
        encoding="utf-8",
    )

    result = extract_python(source)

    assert result[0]["defaults"] == {"limit": 10, "active": False}


def test_raises_clear_error_for_missing_file(tmp_path):
    missing = tmp_path / "missing.py"

    with pytest.raises(OSError, match="Could not read Python source file"):
        extract_python(missing)


def test_raises_clear_error_for_invalid_syntax(tmp_path):
    source = tmp_path / "invalid.py"
    source.write_text("def broken(:\n    pass\n", encoding="utf-8")

    with pytest.raises(SyntaxError, match="Invalid Python syntax"):
        extract_python(source)


def test_non_literal_default_is_preserved_as_source(tmp_path):
    source = tmp_path / "source.py"
    source.write_text("def build(value=make_value()):\n    pass\n", encoding="utf-8")

    result = extract_python(source)

    assert result[0]["defaults"] == {"value": "make_value()"}
