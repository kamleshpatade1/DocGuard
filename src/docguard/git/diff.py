import os
import subprocess
from pathlib import Path


class GitDiffError(Exception):
    """Raised when a Git diff operation fails."""


class InvalidRepositoryError(GitDiffError):
    """Raised when the provided path is not a Git repository."""


class InvalidRevisionError(GitDiffError):
    """Raised when a base or head revision cannot be resolved."""


def _run_git(repo_path: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ["git", "-C", str(repo_path), *args],
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise GitDiffError(f"Unable to run Git: {error}") from error


def get_changed_files(
    repo_path: str | os.PathLike[str], base_ref: str, head_ref: str
) -> list[str]:
    """Return file paths changed between two commits, relative to the repo root."""
    path = Path(repo_path)
    if not path.is_dir():
        raise InvalidRepositoryError(f"Not a Git repository directory: {path}")

    repository_result = _run_git(path, "rev-parse", "--show-toplevel")
    if repository_result.returncode != 0:
        details = os.fsdecode(repository_result.stderr).strip()
        raise InvalidRepositoryError(
            f"Not a Git repository directory: {path}"
            + (f" ({details})" if details else "")
        )
    repository_root = Path(os.fsdecode(repository_result.stdout).rstrip("\n"))

    resolved_revisions = []
    for revision in (base_ref, head_ref):
        if not isinstance(revision, str) or "\0" in revision:
            raise InvalidRevisionError(f"Invalid Git revision: {revision!r}")
        result = _run_git(
            repository_root,
            "rev-parse",
            "--verify",
            "--quiet",
            "--end-of-options",
            f"{revision}^{{commit}}",
        )
        if result.returncode != 0:
            raise InvalidRevisionError(f"Invalid Git revision: {revision!r}")
        resolved_revisions.append(os.fsdecode(result.stdout).strip())

    diff_result = _run_git(
        repository_root,
        "diff",
        "--name-only",
        "-z",
        "--find-renames",
        resolved_revisions[0],
        resolved_revisions[1],
    )
    if diff_result.returncode != 0:
        details = os.fsdecode(diff_result.stderr).strip()
        raise GitDiffError(f"Git diff failed: {details or 'unknown error'}")

    return [
        os.fsdecode(file_path)
        for file_path in diff_result.stdout.split(b"\0")
        if file_path
    ]
