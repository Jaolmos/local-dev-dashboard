"""Radar de proyectos: escanea la carpeta raíz y detecta repositorios."""

from dataclasses import dataclass, field
from pathlib import Path

from . import stack

# Niveles de subcarpetas a explorar bajo la raíz (los repos suelen estar agrupados).
_MAX_DEPTH = 3


@dataclass(frozen=True)
class DiscoveredProject:
    name: str
    path: Path
    description: str = ""
    stack_tags: list[str] = field(default_factory=list)


def _read_description(project_path: Path) -> str:
    """Extrae la primera línea no vacía del README como descripción corta."""
    for filename in ("README.md", "README.MD", "readme.md"):
        readme = project_path / filename
        if not readme.is_file():
            continue
        try:
            with readme.open(encoding="utf-8", errors="ignore") as handle:
                for line in handle:
                    text = line.lstrip("#").strip()
                    if text:
                        return text[:500]
        except OSError:
            return ""
    return ""


def scan_projects(root: Path, max_depth: int = _MAX_DEPTH) -> list[DiscoveredProject]:
    """Recorre ``root`` hasta ``max_depth`` niveles y devuelve los repositorios Git.

    Al encontrar un repo (carpeta con ``.git``) lo registra y no sigue bajando dentro,
    así se soportan proyectos agrupados en subcarpetas sin escanear su árbol interno.
    """
    if not root.is_dir():
        return []

    discovered: list[DiscoveredProject] = []
    _walk(root, max_depth, discovered)
    return sorted(discovered, key=lambda project: str(project.path))


def _walk(directory: Path, depth_left: int, out: list[DiscoveredProject]) -> None:
    """Explora ``directory`` en profundidad acumulando repos en ``out``."""
    for entry in sorted(directory.iterdir()):
        # Se ignoran ficheros y carpetas ocultas (.git, .cache, etc.).
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        if (entry / ".git").exists():
            out.append(
                DiscoveredProject(
                    name=entry.name,
                    path=entry,
                    description=_read_description(entry),
                    stack_tags=stack.detect(entry),
                )
            )
            continue  # no se baja dentro de un repositorio ya detectado
        if depth_left > 1:
            _walk(entry, depth_left - 1, out)
