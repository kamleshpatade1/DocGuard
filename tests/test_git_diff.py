import subprocess

import pytest

from docguard.git import InvalidRepositoryError, InvalidRevisionError, get_changed_files


def _run_git(repo_path, *args):
    subprocess.run(
        ["git", "-C", str(repo_path), *args],
        check=True,
        capture_output=True,
    )


def _create_repository(repo_path):
    repo_path.mkdir()
    _run_git(repo_path, "init", "-q")
    _run_git(repo_path, "config", "user.name", "DocGuard Test")
    _run_git(repo_path, "config", "user.email", "docguard-test@example.com")
    (repo_path / "baseline.txt").write_text("baseline")


def _commit_all(repo_path, message):
    _run_git(repo_path, "add", "-A")
    _run_git(repo_path, "commit", "-m", message, "-q")
    return subprocess.run(
        ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_detects_added_file(tmp_path):
    repo = tmp_path / "repo"
    _create_repository(repo)
    base = _commit_all(repo, "initial")

    (repo / "added.txt").write_text("new file")
    head = _commit_all(repo, "add file")

    assert get_changed_files(repo, base, head) == ["added.txt"]


def test_detects_modified_file(tmp_path):
    repo = tmp_path / "repo"
    _create_repository(repo)
    (repo / "existing.txt").write_text("before")
    base = _commit_all(repo, "initial")

    (repo / "existing.txt").write_text("after")
    head = _commit_all(repo, "modify file")

    assert get_changed_files(repo, base, head) == ["existing.txt"]


def test_returns_empty_list_when_there_are_no_changes(tmp_path):
    repo = tmp_path / "repo"
    _create_repository(repo)
    commit = _commit_all(repo, "initial")

    assert get_changed_files(repo, commit, commit) == []


def test_rejects_invalid_revision(tmp_path):
    repo = tmp_path / "repo"
    _create_repository(repo)
    commit = _commit_all(repo, "initial")

    with pytest.raises(InvalidRevisionError, match="Invalid Git revision"):
        get_changed_files(repo, commit, "not-a-valid-revision")


def test_rejects_invalid_repository_directory(tmp_path):
    not_a_repository = tmp_path / "not-a-repository"
    not_a_repository.mkdir()

    with pytest.raises(InvalidRepositoryError):
        get_changed_files(not_a_repository, "HEAD", "HEAD")


def test_handles_filename_with_spaces(tmp_path):
    repo = tmp_path / "repo"
    _create_repository(repo)
    base = _commit_all(repo, "initial")

    (repo / "file with spaces.txt").write_text("content")
    head = _commit_all(repo, "add spaced filename")

    assert get_changed_files(repo, base, head) == ["file with spaces.txt"]
