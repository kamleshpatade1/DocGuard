from docguard.extractors.markdown import ExtractedClaim
from docguard.extractors.python_ast import ExtractedFunction
from docguard.mapper import map_claims_to_facts
from docguard.rules.value_mismatch import find_value_mismatches


def _claim(
    function_name: str | None = "get_students",
    parameter_name: str | None = "limit",
    value: object | None = 30,
) -> ExtractedClaim:
    return {
        "text": "The default limit for get_students is 30.",
        "function_name": function_name,
        "parameter_name": parameter_name,
        "value": value,
        "file_path": "docs/api.md",
        "line_number": 4,
    }


def _function(
    name: str = "get_students",
    defaults: dict[str, object] | None = None,
) -> ExtractedFunction:
    return {
        "name": name,
        "line_number": 2,
        "file_path": "src/service.py",
        "defaults": defaults if defaults is not None else {"limit": 50},
    }


def test_maps_mismatching_default_into_a_finding():
    pairs = map_claims_to_facts([_claim()], [_function()])

    findings = find_value_mismatches(pairs)

    assert len(findings) == 1
    assert findings[0].rule_id == "VALUE_MISMATCH"
    assert "documented with default 30" in findings[0].message
    assert "Python uses 50" in findings[0].message


def test_equal_values_do_not_create_a_finding():
    pairs = map_claims_to_facts([_claim(value=50)], [_function()])

    assert find_value_mismatches(pairs) == []


def test_different_function_name_is_not_matched():
    pairs = map_claims_to_facts([_claim()], [_function(name="list_students")])

    assert pairs == []


def test_parameter_name_is_respected():
    pairs = map_claims_to_facts(
        [_claim(parameter_name="active")],
        [_function(defaults={"limit": 50, "active": True})],
    )

    assert len(pairs) == 1
    assert pairs[0]["parameter_name"] == "active"
    assert pairs[0]["fact"].value == "True"


def test_claim_without_confident_value_is_not_matched():
    pairs = map_claims_to_facts([_claim(value=None)], [_function()])

    assert pairs == []


def test_preserves_source_paths_and_line_numbers_in_finding():
    pairs = map_claims_to_facts([_claim()], [_function()])
    findings = find_value_mismatches(pairs)

    assert findings[0].documentation_file == "docs/api.md"
    assert findings[0].documentation_line == 4
    assert findings[0].evidence_file == "src/service.py"
    assert findings[0].evidence_line == 2


def test_duplicate_claims_do_not_create_duplicate_findings():
    pairs = map_claims_to_facts([_claim(), _claim()], [_function()])

    assert len(pairs) == 1
    assert len(find_value_mismatches(pairs)) == 1


def test_unqualified_method_name_matches_only_unique_method():
    claim = _claim(function_name="get_student", parameter_name="student_id")
    function = _function(name="StudentService.get_student", defaults={"student_id": 10})

    pairs = map_claims_to_facts([claim], [function])

    assert len(pairs) == 1
    assert pairs[0]["function_name"] == "StudentService.get_student"


def test_ambiguous_unqualified_method_name_is_not_matched():
    claim = _claim(function_name="get_student", parameter_name="student_id")
    functions = [
        _function(name="StudentService.get_student", defaults={"student_id": 10}),
        _function(name="OtherService.get_student", defaults={"student_id": 20}),
    ]

    assert map_claims_to_facts([claim], functions) == []


def test_skips_string_default_that_looks_like_python_expression():
    claim = _claim(value="factory()")
    function = _function(defaults={"limit": "factory()"})

    assert map_claims_to_facts([claim], [function]) == []


def test_maps_literal_string_default_that_is_a_valid_python_name():
    claim = _claim(parameter_name="name", value="hello")
    function = _function(defaults={"name": "hello"})

    pairs = map_claims_to_facts([claim], [function])

    assert len(pairs) == 1
    assert pairs[0]["claim"].value == "'hello'"
    assert pairs[0]["fact"].value == "'hello'"
    assert find_value_mismatches(pairs) == []


def test_detects_mismatching_string_default():
    claim = _claim(parameter_name="name", value="goodbye")
    function = _function(defaults={"name": "hello"})

    pairs = map_claims_to_facts([claim], [function])
    findings = find_value_mismatches(pairs)

    assert len(findings) == 1
    assert "'goodbye'" in findings[0].message
    assert "'hello'" in findings[0].message


def test_maps_actual_none_default_without_confusing_missing_parameter():
    claim = _claim(parameter_name="value", value=30)
    function = _function(defaults={"value": None})

    pairs = map_claims_to_facts([claim], [function])

    assert len(pairs) == 1
    assert pairs[0]["fact"].value == "None"
    assert len(find_value_mismatches(pairs)) == 1


def test_missing_default_is_not_treated_as_none():
    claim = _claim(parameter_name="value", value=30)
    function = _function(defaults={})

    assert map_claims_to_facts([claim], [function]) == []


def test_unknown_documented_value_does_not_match_actual_none():
    claim = _claim(parameter_name="value", value=None)
    function = _function(defaults={"value": None})

    assert map_claims_to_facts([claim], [function]) == []
