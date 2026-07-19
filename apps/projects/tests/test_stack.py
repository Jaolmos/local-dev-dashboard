"""Tests de la detección de stack por ficheros marcadores."""

from apps.projects.services import stack


def _touch(path, *filenames):
    for name in filenames:
        (path / name).write_text("", encoding="utf-8")


def test_detect_without_markers_returns_empty(tmp_path):
    assert stack.detect(tmp_path) == []


def test_detect_django_by_manage_py(tmp_path):
    # manage.py marca Django y, como es un .py, también Python (vía glob).
    _touch(tmp_path, "manage.py")

    assert stack.detect(tmp_path) == ["Django", "Python"]


def test_detect_multiple_stacks_sorted_and_deduplicated(tmp_path):
    # pyproject.toml y requirements.txt mapean ambos a "Python": no debe duplicarse.
    _touch(tmp_path, "manage.py", "pyproject.toml", "requirements.txt", "Dockerfile")

    assert stack.detect(tmp_path) == ["Django", "Docker", "Python"]


def test_detect_docker_by_any_variant(tmp_path):
    _touch(tmp_path, "docker-compose.yaml")

    assert stack.detect(tmp_path) == ["Docker"]


def test_detect_python_from_loose_scripts(tmp_path):
    # Repo sin pyproject/requirements pero con scripts sueltos: debe detectar Python.
    _touch(tmp_path, "script.py", "notas.txt")

    assert stack.detect(tmp_path) == ["Python"]


def test_detect_python_in_nested_dirs(tmp_path):
    # Scripts agrupados en carpetas (p. ej. patrones/creacionales/singleton.py) cuentan
    # hasta 2 niveles bajo la raíz.
    (tmp_path / "creacionales" / "singleton").mkdir(parents=True)
    _touch(tmp_path / "creacionales" / "singleton", "singleton.py")

    assert stack.detect(tmp_path) == ["Python"]


def test_detect_glob_ignores_hidden_vendor_and_deeper_dirs(tmp_path):
    # Ni ocultas (.venv), ni vendor (node_modules), ni más allá de _GLOB_DEPTH.
    (tmp_path / ".venv").mkdir()
    _touch(tmp_path / ".venv", "activate.py")
    (tmp_path / "node_modules" / "gyp").mkdir(parents=True)
    _touch(tmp_path / "node_modules" / "gyp", "input.py")
    (tmp_path / "a" / "b" / "c").mkdir(parents=True)
    _touch(tmp_path / "a" / "b" / "c", "deep.py")

    assert stack.detect(tmp_path) == []


def test_detect_dotnet_by_solution_or_project(tmp_path):
    _touch(tmp_path, "MyApp.sln", "MyApp.csproj")

    assert stack.detect(tmp_path) == [".NET"]


def test_detect_new_marker_files(tmp_path):
    _touch(tmp_path, "tsconfig.json", "angular.json", "pubspec.yaml")

    assert stack.detect(tmp_path) == ["Angular", "Flutter", "TypeScript"]


def test_detect_jupyter_notebooks(tmp_path):
    _touch(tmp_path, "analisis.ipynb")

    assert stack.detect(tmp_path) == ["Jupyter"]
