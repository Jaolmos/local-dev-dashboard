"""Tests del service de catálogo: sincronización disco -> BD."""

import subprocess

import pytest

from apps.projects.models import Project
from apps.projects.services import catalog

pytestmark = pytest.mark.django_db


def _make_repo(root, name):
    """Crea un repo git real con un commit (para que tenga last_commit)."""
    path = root / name
    path.mkdir(parents=True)
    (path / "README.md").write_text(f"# {name}\n\nDescripción de {name}.\n")
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t.t", "-c", "user.name=t", "commit", "-qm", "init"],
        cwd=path,
        check=True,
    )
    return path


def test_sync_creates_projects_from_disk(tmp_path):
    _make_repo(tmp_path, "alpha")

    result = catalog.sync(tmp_path)

    assert result.created == 1
    # La descripción es la 1ª línea no vacía del README (el título, sin el '#').
    assert Project.objects.get(name="alpha").description == "alpha"


def test_sync_is_idempotent(tmp_path):
    _make_repo(tmp_path, "alpha")

    catalog.sync(tmp_path)
    result = catalog.sync(tmp_path)

    assert (result.created, result.updated) == (0, 1)
    assert Project.objects.count() == 1


def test_sync_without_prune_keeps_missing_projects(tmp_path):
    ghost = Project.objects.create(name="ghost", path=str(tmp_path / "ghost"))

    result = catalog.sync(tmp_path)

    assert result.pruned == 0
    assert Project.objects.filter(pk=ghost.pk).exists()


def test_sync_with_prune_removes_missing_projects(tmp_path):
    Project.objects.create(name="ghost", path=str(tmp_path / "ghost"))

    result = catalog.sync(tmp_path, prune=True)

    assert result.pruned == 1
    assert not Project.objects.exists()


def test_sync_on_missing_root_does_nothing(tmp_path):
    result = catalog.sync(tmp_path / "no-existe")

    assert (result.created, result.updated, result.pruned) == (0, 0, 0)
