import ast
import json
import unittest
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parents[1] / "examples" / "demo-repo"
SOURCE_FILE = DEMO_DIR / "student_api.py"
README_FILE = DEMO_DIR / "README.md"
FIXTURE_FILE = DEMO_DIR / "expected_findings.json"


class DemoRepositoryTests(unittest.TestCase):
    def test_demo_files_exist(self):
        for path in (SOURCE_FILE, README_FILE, FIXTURE_FILE):
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file())

    def test_source_defines_get_students_with_default_limit_50(self):
        source = SOURCE_FILE.read_text(encoding="utf-8")
        module = ast.parse(source)
        function = next(
            node
            for node in ast.walk(module)
            if isinstance(node, ast.FunctionDef) and node.name == "get_students"
        )

        defaults = dict(
            zip(
                (argument.arg for argument in function.args.args[-len(function.args.defaults) :]),
                function.args.defaults,
            )
        )
        self.assertIn("limit", defaults)
        self.assertEqual(ast.literal_eval(defaults["limit"]), 50)

    def test_readme_documents_incorrect_default_30(self):
        readme = README_FILE.read_text(encoding="utf-8")
        self.assertIn("get_students(limit=30)", readme)

    def test_expected_findings_fixture_is_valid_json(self):
        fixture = json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))
        self.assertIsInstance(fixture, dict)

    def test_expected_finding_records_documentation_mismatch(self):
        fixture = json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))
        finding = fixture["expected_finding"]

        self.assertEqual(finding["rule_id"], "VALUE_MISMATCH")
        self.assertEqual(finding["symbol"], "get_students")
        self.assertEqual(finding["documented_value"], 30)
        self.assertEqual(finding["actual_value"], 50)
        self.assertEqual(finding["source_file"], "student_api.py")


if __name__ == "__main__":
    unittest.main()
