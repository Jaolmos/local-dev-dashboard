"""Tests del estado de Git (repos reales creados en tmp_path)."""

import subprocess

import pytest

from apps.projects.services import git


def _git(path, *args):
    subprocess.run(["git", *args], cwd=path, check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    """Crea un repo git real con un commit inicial en la rama ``main``."""
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "file.txt").write_text("hola", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "init")
    return tmp_path


def test_status_dir_without_git_is_not_repo(tmp_path):
    status = git.get_status(tmp_path)

    assert status.is_repo is False
    assert status.branch == ""


def test_status_clean_repo(repo):
    status = git.get_status(repo)

    assert status.is_repo is True
    assert status.branch == "main"
    assert status.is_dirty is False


def test_status_dirty_repo(repo):
    (repo / "file.txt").write_text("cambiado", encoding="utf-8")

    status = git.get_status(repo)

    assert status.is_dirty is True


def test_status_repo_without_upstream(repo):
    # Repo local sin remoto: no hay rama de seguimiento.
    status = git.get_status(repo)

    assert status.has_upstream is False
    assert status.ahead == 0
    assert status.behind == 0
