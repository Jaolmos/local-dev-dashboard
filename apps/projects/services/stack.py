"""Reconocimiento de stack a partir de los ficheros marcadores del proyecto."""

import fnmatch
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
    "tsconfig.json": "TypeScript",
    "angular.json": "Angular",
    "next.config.js": "Next.js",
    "next.config.mjs": "Next.js",
    "next.config.ts": "Next.js",
    "mix.exs": "Elixir",
    "Package.swift": "Swift",
    "pubspec.yaml": "Flutter",
    "CMakeLists.txt": "C/C++",
}

# Patrón de nombre de fichero -> etiqueta. Cubre proyectos sin fichero de proyecto:
# scripts .py sueltos o agrupados en carpetas, notebooks, soluciones .NET…
# Makefile se descartó (aparece en repos de cualquier lenguaje).
GLOB_MARKERS: dict[str, str] = {
    "*.py": "Python",
    "*.ipynb": "Jupyter",
    "*.csproj": ".NET",
    "*.sln": ".NET",
}


# Niveles de subcarpetas donde buscar los globs, además de la raíz.
_GLOB_DEPTH = 2

# Carpetas de dependencias/artefactos: buscar ahí es lento y da falsos positivos
# (node_modules puede traer .py de node-gyp, un venv trae miles).
_IGNORED_DIRS = {"node_modules", "__pycache__", "venv", "env", "dist", "build", "target", "vendor"}


def _walk_filenames(path: Path, depth: int):
    """Genera los nombres de fichero de la raíz y hasta ``depth`` niveles.

    Ignora entradas ocultas y carpetas de dependencias (``_IGNORED_DIRS``).
    """
    for entry in path.iterdir():
        if entry.name.startswith("."):
            continue
        if entry.is_dir():
            if depth > 0 and entry.name not in _IGNORED_DIRS:
                yield from _walk_filenames(entry, depth - 1)
        else:
            yield entry.name


def detect(path: Path) -> list[str]:
    """Devuelve las etiquetas de stack ordenadas y sin duplicados del proyecto."""
    tags: set[str] = set()
    for marker, tag in STACK_MARKERS.items():
        if (path / marker).exists():
            tags.add(tag)

    # Una sola pasada del árbol para todos los patrones; los tags ya detectados
    # por marcador no se buscan, y se corta en cuanto no queda ninguno pendiente.
    pending = {pattern: tag for pattern, tag in GLOB_MARKERS.items() if tag not in tags}
    if pending:
        for filename in _walk_filenames(path, _GLOB_DEPTH):
            matched = [p for p in pending if fnmatch.fnmatch(filename, p)]
            for pattern in matched:
                tags.add(pending.pop(pattern))
            if not pending:
                break
    return sorted(tags)
