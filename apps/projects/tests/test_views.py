"""Tests de las vistas: status, partial correcto y acción de VSCode mockeada."""

from datetime import UTC, datetime, timedelta

import pytest
from django.urls import reverse

from apps.projects.models import Project

pytestmark = pytest.mark.django_db


def _template_names(response):
    return [t.name for t in response.templates if t.name]


@pytest.fixture
def project(settings, tmp_path):
    """Project cuya ruta vive bajo PROJECTS_ROOT (apuntado a tmp_path)."""
    settings.PROJECTS_ROOT = tmp_path
    path = tmp_path / "demo"
    path.mkdir()
    return Project.objects.create(name="demo", path=str(path))


def test_list_returns_200_and_template(client, project):
    response = client.get(reverse("projects:list"))

    assert response.status_code == 200
    assert "projects/project_list.html" in _template_names(response)
    assert b"demo" in response.content


def test_list_orders_by_recent_activity_first(client, settings, tmp_path):
    settings.PROJECTS_ROOT = tmp_path
    now = datetime.now(UTC)
    Project.objects.create(
        name="old", path=str(tmp_path / "old"), last_commit=now - timedelta(days=30)
    )
    Project.objects.create(name="recent", path=str(tmp_path / "recent"), last_commit=now)
    Project.objects.create(name="never", path=str(tmp_path / "never"), last_commit=None)

    names = [p.name for p in client.get(reverse("projects:list")).context["projects"]]

    # Lo más reciente arriba y los repos sin commits al final.
    assert names == ["recent", "old", "never"]


def test_git_status_returns_partial(client, project):
    response = client.get(reverse("projects:git-status", args=[project.pk]))

    assert response.status_code == 200
    assert "projects/partials/git_status.html" in _template_names(response)
    # tmp_path no es repo git -> "sin git"
    assert b"sin git" in response.content


def test_readme_returns_partial(client, project):
    response = client.get(reverse("projects:readme", args=[project.pk]))

    assert response.status_code == 200
    assert "projects/partials/readme_modal.html" in _template_names(response)


def test_open_vscode_valid_path_launches_code(client, project, monkeypatch):
    calls = []
    monkeypatch.setattr(
        "apps.projects.views.subprocess.Popen",
        lambda args, *a, **k: calls.append(args),
    )

    response = client.post(reverse("projects:open-vscode", args=[project.pk]))

    assert response.status_code == 200
    assert "projects/partials/open_result.html" in _template_names(response)
    assert b"Abriendo" in response.content
    assert calls and calls[0][0] == "code"


def test_open_vscode_path_outside_root_does_not_run(client, settings, tmp_path, monkeypatch):
    # Project cuya ruta NO vive bajo PROJECTS_ROOT: no debe ejecutarse nada.
    settings.PROJECTS_ROOT = tmp_path / "root"
    (tmp_path / "root").mkdir()
    outside = Project.objects.create(name="outside", path="/etc")

    called = []
    monkeypatch.setattr(
        "apps.projects.views.subprocess.Popen",
        lambda *a, **k: called.append(True),
    )

    response = client.post(reverse("projects:open-vscode", args=[outside.pk]))

    assert response.status_code == 200
    assert b"Error al abrir" in response.content
    assert called == []
