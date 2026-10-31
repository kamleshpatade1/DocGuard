from docguard.mapper import MappedDefault
from docguard.models import Claim, Fact
from docguard.rules.value_mismatch import find_value_mismatches


def _match(documented: object, actual: object) -> MappedDefault:
    return {
        "claim": Claim(
            text="The default limit for get_students is documented.",
            file_path="docs/api.md",
            line_number=4,
            value=repr(documented),
        ),
        "fact": Fact(
            text="get_students.limit default",
            file_path="src/service.py",
            line_number=2,
            value=repr(actual),
        ),
        "function_name": "get_students",
        "parameter_name": "limit",
    }


def test_different_numeric_values_create_value_mismatch():
    findings = find_value_mismatches([_match(30, 50)])

    assert len(findings) == 1
    assert findings[0].rule_id == "VALUE_MISMATCH"
    assert "30" in findings[0].message
    assert "50" in findings[0].message


def test_equal_values_do_not_create_value_mismatch():
    assert find_value_mismatches([_match(30, 30)]) == []


def test_boolean_true_and_integer_one_are_not_equal():
    findings = find_value_mismatches([_match(True, 1)])

    assert len(findings) == 1


def test_boolean_false_and_integer_zero_are_not_equal():
    findings = find_value_mismatches([_match(False, 0)])

    assert len(findings) == 1


def test_integer_and_equivalent_float_are_equal():
    assert find_value_mismatches([_match(1, 1.0)]) == []


def test_equal_string_values_do_not_create_mismatch():
    assert find_value_mismatches([_match("hello", "hello")]) == []


def test_different_string_values_create_mismatch():
    findings = find_value_mismatches([_match("hello", "goodbye")])

    assert len(findings) == 1
    assert "'hello'" in findings[0].message
    assert "'goodbye'" in findings[0].message


def test_equal_none_values_do_not_create_mismatch():
    assert find_value_mismatches([_match(None, None)]) == []


def test_none_and_non_none_values_create_mismatch():
    findings = find_value_mismatches([_match(None, 0)])

    assert len(findings) == 1


def test_duplicate_claim_fact_pairs_create_one_finding():
    match = _match(30, 50)

    assert len(find_value_mismatches([match, match])) == 1


def test_values_that_are_not_literals_are_ignored():
    match = _match(30, 50)
    match["fact"].value = "make_value()"

    assert find_value_mismatches([match]) == []
