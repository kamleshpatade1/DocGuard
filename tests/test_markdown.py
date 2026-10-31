import pytest

from docguard.extractors.markdown import extract_markdown


def test_extracts_prose_default_claim_and_source_details(tmp_path):
    source = tmp_path / "guide.md"
    text = "# Student API\n\nThe default limit for `get_students` is 30.\n"
    source.write_text(text, encoding="utf-8")

    claims = extract_markdown(source)

    assert claims == [
        {
            "text": "The default limit for `get_students` is 30.",
            "function_name": "get_students",
            "parameter_name": "limit",
            "value": 30,
            "file_path": str(source),
            "line_number": 3,
        }
    ]


def test_extracts_inline_function_call_default(tmp_path):
    source = tmp_path / "guide.md"
    source.write_text(
        "`get_students(limit=30)` returns the first 30 students.\n",
        encoding="utf-8",
    )

    claims = extract_markdown(source)

    assert len(claims) == 1
    assert claims[0]["function_name"] == "get_students"
    assert claims[0]["parameter_name"] == "limit"
    assert claims[0]["value"] == 30


@pytest.mark.parametrize(
    ("documented_value", "expected_value"),
    [
        ("5", 5),
        ("true", True),
        ("false", False),
        ('"Hello"', "Hello"),
        ('"Hello, students"', "Hello, students"),
        ("'Hello'", "Hello"),
    ],
)
def test_extracts_supported_value_types(tmp_path, documented_value, expected_value):
    source = tmp_path / "guide.md"
    source.write_text(
        f"The default message for `greet` is {documented_value}.\n",
        encoding="utf-8",
    )

    claims = extract_markdown(source)

    assert len(claims) == 1
    assert claims[0]["value"] == expected_value


def test_preserves_claim_when_value_is_not_recognized(tmp_path):
    source = tmp_path / "guide.md"
    text = "The default limit for `get_students` is chosen dynamically.\n"
    source.write_text(text, encoding="utf-8")

    claims = extract_markdown(source)

    assert len(claims) == 1
    assert claims[0]["text"] == text.strip()
    assert claims[0]["function_name"] == "get_students"
    assert claims[0]["parameter_name"] == "limit"
    assert claims[0]["value"] is None


def test_leaves_unknown_function_as_none(tmp_path):
    source = tmp_path / "guide.md"
    source.write_text("The default limit is 30.\n", encoding="utf-8")

    claims = extract_markdown(source)

    assert len(claims) == 1
    assert claims[0]["function_name"] is None
    assert claims[0]["parameter_name"] == "limit"
    assert claims[0]["value"] == 30


def test_ignores_markdown_without_recognizable_claims(tmp_path):
    source = tmp_path / "guide.md"
    source.write_text("# Overview\n\nWelcome to the student guide.\n", encoding="utf-8")

    assert extract_markdown(source) == []


def test_deduplicates_prose_and_inline_code_for_same_default(tmp_path):
    source = tmp_path / "guide.md"
    source.write_text(
        "The default limit for `get_students` is 30, "
        "so call `get_students(limit=30)` for the first page.\n",
        encoding="utf-8",
    )

    claims = extract_markdown(source)

    assert len(claims) == 1
    assert claims[0]["value"] == 30


def test_raises_clear_error_for_missing_file(tmp_path):
    missing = tmp_path / "missing.md"

    with pytest.raises(OSError, match="Could not read Markdown file"):
        extract_markdown(missing)


def test_raises_clear_error_for_unreadable_text(tmp_path):
    source = tmp_path / "invalid.md"
    source.write_bytes(b"\xff")

    with pytest.raises(OSError, match="Could not read Markdown file"):
        extract_markdown(source)
