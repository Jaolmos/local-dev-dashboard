"""Tests de la detección de stack por ficheros marcadores."""

from apps.projects.services import stack


def _touch(path, *filenames):
    for name in filenames:
        (path / name).write_text("", encoding="utf-8")


def test_detect_without_markers_returns_empty(tmp_path):
    assert stack.detect(tmp_path) == []


def test_detect_django_by_manage_py(tmp_path):
    _touch(tmp_path, "manage.py")

    assert stack.detect(tmp_path) == ["Django"]


def test_detect_multiple_stacks_sorted_and_deduplicated(tmp_path):
    # pyproject.toml y requirements.txt mapean ambos a "Python": no debe duplicarse.
    _touch(tmp_path, "manage.py", "pyproject.toml", "requirements.txt", "Dockerfile")

    assert stack.detect(tmp_path) == ["Django", "Docker", "Python"]


def test_detect_docker_by_any_variant(tmp_path):
    _touch(tmp_path, "docker-compose.yaml")

    assert stack.detect(tmp_path) == ["Docker"]
