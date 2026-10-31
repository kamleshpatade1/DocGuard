# DocGuard

DocGuard is a small Python tool that checks whether selected documentation
claims still match Python source code. Its checks compare documented function
parameter defaults with Python defaults and flag call-shaped function references
that are missing from the analyzed source.

## The problem

Documentation can drift as code changes. A guide may say that a function uses a
default limit of `30`, while the implementation now defaults to `50`. DocGuard
detects this supported type of mismatch and reports the documentation and source
locations so a developer can review it.

## Implemented features

- **Python AST extraction:** reads Python source with the built-in `ast` module
  and extracts top-level functions, class methods, source line numbers, and
  positional or keyword-only default values. Source code is not executed.
- **Markdown claim extraction:** recognizes a limited set of explicit default
  statements and inline-code calls. For example:
  - `The default limit for \`get_students\` is 30.`
  - `` `get_students(limit=30)` ``
- **Mapping:** matches claims to extracted function defaults by function name
  and, when available, parameter name. Ambiguous function matches and claims
  without a recognized value are skipped.
- **`VALUE_MISMATCH` detection:** compares supported literal values and reports
  when the documented and Python defaults differ.
- **`FUNCTION_NOT_FOUND` detection:** reports simple function-call references
  found in Markdown when no matching top-level function or class method is
  present in the Python source.
- **Confidence scoring:** assigns `high`, `medium`, or `low` from the
  completeness of documentation and source evidence already on a finding. It
  does not invoke an external verifier.
- **Command-line interface:** compares one Markdown file with one Python source
  file, prints findings with locations and confidence, and returns a non-zero
  status when drift is found.
- **Web dashboard:** provides editable Python and Markdown inputs backed by a
  Flask API that reuses the same detection engine.

## How it works

```text
Markdown file ──> Markdown extractors ──┐
                                        ├─> Mapper ─> VALUE_MISMATCH rule ──┐
Python file ───> Python AST extractor ──┘                                   ├─> Confidence scoring
                             └────────────> FUNCTION_NOT_FOUND rule ─────────┘          │
                                                                                       v
                                                                        CLI / web API findings
```

The engine connects these steps for a single documentation/Python file pair.
Python and Markdown code examples are parsed, not executed.

## Requirements

- Python 3.10 or newer
- `pip`
- macOS or Linux shell for the commands below

## Installation

From the repository root, create and activate a virtual environment, then
install DocGuard in editable mode with its development tools:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The project uses setuptools and a `src/` package layout. The `docguard`
console command is registered by the project configuration.

## Try the example

The example documentation says the default is `30`; the Python implementation
uses `50`:

- [`examples/students.md`](examples/students.md)
- [`examples/students.py`](examples/students.py)

With the virtual environment active, run:

```bash
docguard examples/students.md examples/students.py
```

Expected output:

```text
VALUE_MISMATCH: get_students.limit is documented with default 30, but Python uses 50.
  Documentation: examples/students.md:3
  Evidence: examples/students.py:1
  Confidence: HIGH
```

DocGuard returns exit status `1` when it finds drift, `0` when it finds none,
and `2` for invalid input or analysis errors. The non-zero status for findings
is intentional and can be used by scripts or CI checks.

## Run the tests

Install the development extra as described above, then run:

```bash
python -m pytest -q
```

To run Ruff over the project:

```bash
python -m ruff check
```

## Current limitations and possible next steps

### Implemented today

- The engine accepts one Markdown file and one Python file per run.
- Default comparison is limited to recognizable function default-value claims.
- Missing-function detection recognizes simple call-shaped references in
  Markdown prose and inline code; it does not resolve imports or understand
  arbitrary natural-language descriptions.
- Python extraction uses syntax-tree information and does not import or execute
  the analyzed module.
- Findings show the source locations and evidence available from the extractors.

### Not implemented yet

- General API, configuration, or semantic documentation comparison.
- Directory-wide or repository-wide documentation analysis through the CLI.
- Full natural-language understanding or support for every Markdown/code syntax.
- AI-generated explanations or correction suggestions.
- Automatic documentation edits.

The repository includes a Git changed-file helper, but the current DocGuard
engine and CLI do not use it to scope detection.

## Web dashboard

The optional dashboard is a React/Vite frontend with a Flask API. The API writes
the submitted text to temporary files for the existing path-based engine,
returns findings as JSON, and removes those temporary files after the scan.
Python input is parsed with the AST and is never executed.

The workspace provides line-numbered editable editors, Python/Markdown uploads,
sample scans for clean input and both supported rules, searchable and sortable
findings, editor navigation, and JSON export. Repeated equivalent findings are
grouped while retaining each documentation location.

Install the Python and Flask requirements from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pip install -r web/backend/requirements.txt
```

In one terminal, start the Flask API from the repository root:

```bash
PYTHONPATH=src python web/backend/app.py
```

In another terminal, install frontend packages and start Vite:

```bash
cd web/frontend
npm install
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`). Vite
proxies `/api` requests to the local Flask server on port `5000`.

## Project information

The hackathon brief names the team as **Team Async**: Kamlesh Patade, Amit Pal,
and Shivans Gupta. DocGuard is licensed under the MIT License; see
[`LICENSE`](LICENSE) for the full text.
