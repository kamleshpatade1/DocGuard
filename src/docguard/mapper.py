"""Connect extracted Markdown claims with Python default-value facts."""

import ast
from typing import TypedDict

from docguard.extractors.markdown import ExtractedClaim
from docguard.extractors.python_ast import ExtractedFunction
from docguard.models import Claim, Fact


class MappedDefault(TypedDict):
    """A documentation claim paired with one Python default fact."""

    claim: Claim
    fact: Fact
    function_name: str
    parameter_name: str


def map_claims_to_facts(
    claims: list[ExtractedClaim],
    functions: list[ExtractedFunction],
) -> list[MappedDefault]:
    """Pair reliably valued claims with matching function parameter defaults.

    The shared models store values as strings, so literal values are serialized
    with ``repr``. The Python extractor does not preserve whether a string value
    came from a literal or a bare-name expression; bare names are treated as
    strings, while clearly expression-shaped values are skipped.
    """
    mapped: list[MappedDefault] = []
    seen: set[tuple[str, int, str, int, str, str, str, str, str]] = set()

    for extracted_claim in claims:
        documented_value = extracted_claim["value"]
        function_name = extracted_claim["function_name"]
        if documented_value is None or function_name is None:
            continue
        if type(documented_value) not in (bool, int, float, str):
            continue

        candidates = _matching_functions(function_name, functions)
        if len(candidates) != 1:
            continue

        function = candidates[0]
        defaults = function["defaults"]
        parameter_name = extracted_claim["parameter_name"]
        if parameter_name is None:
            if len(defaults) != 1:
                continue
            parameter_name = next(iter(defaults))
        if parameter_name not in defaults:
            continue

        actual_value = defaults[parameter_name]
        if actual_value is not None and type(actual_value) not in (bool, int, float, str):
            continue
        if isinstance(actual_value, str) and _looks_like_expression(actual_value):
            continue

        claim = Claim(
            text=extracted_claim["text"],
            file_path=extracted_claim["file_path"],
            line_number=extracted_claim["line_number"],
            value=repr(documented_value),
        )
        fact = Fact(
            text=f"{function['name']}.{parameter_name} default is {actual_value!r}",
            file_path=function["file_path"],
            line_number=function["line_number"],
            value=repr(actual_value),
        )
        pair_key = (
            claim.file_path,
            claim.line_number,
            fact.file_path,
            fact.line_number,
            function["name"],
            parameter_name,
            claim.text,
            claim.value or "",
            fact.value or "",
        )
        if pair_key in seen:
            continue
        seen.add(pair_key)
        mapped.append(
            {
                "claim": claim,
                "fact": fact,
                "function_name": function["name"],
                "parameter_name": parameter_name,
            }
        )

    return mapped


def _matching_functions(
    requested_name: str,
    functions: list[ExtractedFunction],
) -> list[ExtractedFunction]:
    exact_matches = [function for function in functions if function["name"] == requested_name]
    if exact_matches:
        return exact_matches

    return [
        function
        for function in functions
        if function["name"].rsplit(".", maxsplit=1)[-1] == requested_name
    ]


def _looks_like_expression(value: str) -> bool:
    try:
        expression = ast.parse(value, mode="eval").body
    except SyntaxError:
        return False
    return not isinstance(expression, ast.Name)
