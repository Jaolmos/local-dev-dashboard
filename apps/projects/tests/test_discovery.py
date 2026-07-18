"""Tests del radar de proyectos (discovery)."""

from pathlib import Path

from apps.projects.services import discovery


def _make_repo(path: Path, readme: str | None = None) -> Path:
    """Crea una carpeta con un ``.git`` (repo simulado) y opcionalmente un README."""
    path.mkdir(parents=True, exist_ok=True)
    (path / ".git").mkdir()
    if readme is not None:
        (path / "README.md").write_text(readme, encoding="utf-8")
    return path


def test_scan_nonexistent_root_returns_empty(tmp_path):
    assert discovery.scan_projects(tmp_path / "no-existe") == []


def test_scan_finds_top_level_repo(tmp_path):
    _make_repo(tmp_path / "proj")

    result = discovery.scan_projects(tmp_path)

    assert [p.name for p in result] == ["proj"]


def test_scan_finds_nested_repos(tmp_path):
    # Estructura tipo carpetas-grupo: los repos viven un nivel más abajo.
    _make_repo(tmp_path / "grupo" / "api")
    _make_repo(tmp_path / "grupo" / "web")
    _make_repo(tmp_path / "suelto")

    names = [p.name for p in discovery.scan_projects(tmp_path)]

    assert sorted(names) == ["api", "suelto", "web"]


def test_scan_does_not_descend_into_detected_repo(tmp_path):
    # Un repo que contiene otro .git anidado no debe contarse dos veces.
    outer = _make_repo(tmp_path / "outer")
    _make_repo(outer / "vendor" / "inner")

    names = [p.name for p in discovery.scan_projects(tmp_path)]

    assert names == ["outer"]


def test_scan_respects_max_depth(tmp_path):
    # Repo a 3 niveles: con max_depth=2 no se alcanza.
    _make_repo(tmp_path / "a" / "b" / "deep")

    assert discovery.scan_projects(tmp_path, max_depth=2) == []
    assert [p.name for p in discovery.scan_projects(tmp_path, max_depth=3)] == ["deep"]


def test_scan_ignores_hidden_dirs_and_files(tmp_path):
    _make_repo(tmp_path / ".oculto")  # empieza por punto -> ignorada
    (tmp_path / "fichero.txt").write_text("x", encoding="utf-8")

    assert discovery.scan_projects(tmp_path) == []


def test_scan_sorts_by_path(tmp_path):
    _make_repo(tmp_path / "zeta")
    _make_repo(tmp_path / "alfa")

    result = discovery.scan_projects(tmp_path)

    assert [p.name for p in result] == ["alfa", "zeta"]


def test_description_uses_first_nonempty_readme_line(tmp_path):
    _make_repo(tmp_path / "proj", readme="# Título\n\nCuerpo del readme.\n")

    [project] = discovery.scan_projects(tmp_path)

    # Se quitan las almohadillas y espacios del encabezado.
    assert project.description == "Título"


def test_description_empty_without_readme(tmp_path):
    _make_repo(tmp_path / "proj")

    [project] = discovery.scan_projects(tmp_path)

    assert project.description == ""
