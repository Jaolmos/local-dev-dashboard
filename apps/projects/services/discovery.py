"""Radar de proyectos: escanea la carpeta raíz y detecta repositorios."""

from dataclasses import dataclass, field
from pathlib import Path

from . import stack


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


def scan_projects(root: Path) -> list[DiscoveredProject]:
    """Devuelve los subdirectorios de ``root`` que son repositorios Git."""
    if not root.is_dir():
        return []

    discovered: list[DiscoveredProject] = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or not (entry / ".git").exists():
            continue
        discovered.append(
            DiscoveredProject(
                name=entry.name,
                path=entry,
                description=_read_description(entry),
                stack_tags=stack.detect(entry),
            )
        )
    return discovered
