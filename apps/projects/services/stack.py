"""Reconocimiento de stack a partir de los ficheros marcadores del proyecto."""

from pathlib import Path

# Fichero marcador -> etiqueta de stack visible.
STACK_MARKERS: dict[str, str] = {
    "manage.py": "Django",
    "package.json": "Node.js",
    "docker-compose.yml": "Docker",
    "docker-compose.yaml": "Docker",
    "Dockerfile": "Docker",
    "pyproject.toml": "Python",
    "requirements.txt": "Python",
    "Cargo.toml": "Rust",
    "go.mod": "Go",
    "composer.json": "PHP",
    "Gemfile": "Ruby",
    "pom.xml": "Java",
    "build.gradle": "Java",
}


def detect(path: Path) -> list[str]:
    """Devuelve las etiquetas de stack ordenadas y sin duplicados del proyecto."""
    tags: set[str] = set()
    for marker, tag in STACK_MARKERS.items():
        if (path / marker).exists():
            tags.add(tag)
    return sorted(tags)
