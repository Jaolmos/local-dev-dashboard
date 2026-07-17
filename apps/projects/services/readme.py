"""Lectura y renderizado del README de un proyecto a HTML."""

from pathlib import Path

import markdown

_EXTENSIONS = ["fenced_code", "tables", "toc", "sane_lists"]


def render(path: Path) -> str | None:
    """Renderiza el README.md del proyecto a HTML, o None si no existe."""
    for filename in ("README.md", "README.MD", "readme.md"):
        readme = path / filename
        if readme.is_file():
            text = readme.read_text(encoding="utf-8", errors="ignore")
            return markdown.markdown(text, extensions=_EXTENSIONS)
    return None
