"""Extract function definitions and their default parameter values."""

import ast
from pathlib import Path
from typing import TypedDict


class ExtractedFunction(TypedDict):
    """A function or method and its source-level default values."""

    name: str
    line_number: int
    file_path: str
    defaults: dict[str, object]


def extract_python(source_path: str | Path) -> list[ExtractedFunction]:
    """Extract top-level functions and class methods from a Python source file.

    Literal defaults retain their Python values. Non-literal defaults are stored
    as source expressions using ``ast.unparse``; the source is never executed.
    """
    path = Path(source_path)
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Could not read Python source file {path}: {exc}") from exc

    try:
        module = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        raise SyntaxError(f"Invalid Python syntax in {path}: {exc}") from exc

    extracted: list[ExtractedFunction] = []
    _extract_scope(module.body, path, "", extracted)
    return extracted


def _extract_scope(
    statements: list[ast.stmt],
    path: Path,
    class_prefix: str,
    extracted: list[ExtractedFunction],
) -> None:
    for statement in statements:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defaults = _extract_defaults(statement.args)
            extracted.append(
                {
                    "name": f"{class_prefix}.{statement.name}" if class_prefix else statement.name,
                    "line_number": statement.lineno,
                    "file_path": str(path),
                    "defaults": defaults,
                }
            )
        elif isinstance(statement, ast.ClassDef):
            qualified_name = (
                f"{class_prefix}.{statement.name}" if class_prefix else statement.name
            )
            _extract_scope(statement.body, path, qualified_name, extracted)


def _extract_defaults(arguments: ast.arguments) -> dict[str, object]:
    defaults: dict[str, object] = {}
    positional = [*arguments.posonlyargs, *arguments.args]
    first_default = len(positional) - len(arguments.defaults)

    for argument, default in zip(positional[first_default:], arguments.defaults):
        defaults[argument.arg] = _default_value(default)

    for argument, default in zip(arguments.kwonlyargs, arguments.kw_defaults):
        if default is not None:
            defaults[argument.arg] = _default_value(default)

    return defaults


def _default_value(expression: ast.expr) -> object:
    try:
        return ast.literal_eval(expression)
    except (ValueError, TypeError):
        return ast.unparse(expression)
