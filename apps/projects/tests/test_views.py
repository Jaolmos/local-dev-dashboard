"""Tests de las vistas: status, partial correcto y acción de VSCode mockeada."""

from datetime import UTC, datetime, timedelta

import pytest
from django.test import Client
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
    assert b"Abierto" in response.content
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


def test_open_result_restores_the_button(client, project, monkeypatch):
    # El feedback es transitorio: debe pedir la vuelta del botón, no quedarse fijo.
    monkeypatch.setattr("apps.projects.views.subprocess.Popen", lambda *a, **k: None)

    response = client.post(reverse("projects:open-vscode", args=[project.pk]))

    assert b"Abierto" in response.content
    assert reverse("projects:open-button", args=[project.pk]).encode() in response.content


def test_open_button_returns_a_usable_button(client, project):
    response = client.get(reverse("projects:open-button", args=[project.pk]))

    assert response.status_code == 200
    assert b"Abrir en VSCode" in response.content
    assert b"disabled" not in response.content


def test_list_syncs_catalog_on_load(client, settings, tmp_path, monkeypatch):
    # Abrir el panel debe reflejar lo que hay en disco sin pasar por el comando.
    settings.PROJECTS_ROOT = tmp_path
    monkeypatch.setattr(
        "apps.projects.views.catalog.sync",
        lambda root, **kw: Project.objects.create(name="recien-clonado", path=str(root / "new")),
    )

    response = client.get(reverse("projects:list"))

    assert b"recien-clonado" in response.content


def test_list_survives_a_failing_sync(client, settings, tmp_path, monkeypatch):
    # Si el escaneo peta, se muestra el catálogo viejo en vez de un 500.
    settings.PROJECTS_ROOT = tmp_path
    Project.objects.create(name="cacheado", path=str(tmp_path / "cacheado"))
    monkeypatch.setattr(
        "apps.projects.views.catalog.sync",
        lambda *a, **kw: (_ for _ in ()).throw(OSError("disco fallando")),
    )

    response = client.get(reverse("projects:list"))

    assert response.status_code == 200
    assert b"cacheado" in response.content


def test_list_sends_csrf_token_to_htmx(client, project):
    # Sin esta cabecera, todo hx-post se va en 403 (el client de tests no lo detecta).
    assert b"X-CSRFToken" in client.get(reverse("projects:list")).content


def test_open_vscode_with_csrf_enforced_succeeds(project, monkeypatch):
    # El client por defecto lleva CSRF desactivado; aquí se exige de verdad para
    # cubrir el 403 que sí ocurría en el navegador.
    csrf_client = Client(enforce_csrf_checks=True)
    monkeypatch.setattr("apps.projects.views.subprocess.Popen", lambda *a, **k: None)

    csrf_client.get(reverse("projects:list"))
    token = csrf_client.cookies["csrftoken"].value
    response = csrf_client.post(
        reverse("projects:open-vscode", args=[project.pk]),
        headers={"x-csrftoken": token},
    )

    assert response.status_code == 200
    assert b"Abierto" in response.content
