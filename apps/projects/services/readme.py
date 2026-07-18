"""Lectura y renderizado del README de un proyecto a HTML."""

from pathlib import Path

import markdown
import nh3

_EXTENSIONS = ["fenced_code", "tables", "toc", "sane_lists"]


def render(path: Path) -> str | None:
    """Renderiza el README.md del proyecto a HTML sanitizado, o None si no existe.

    La librería markdown deja pasar HTML crudo tal cual, y los README vienen de
    repos clonados (terceros): sin sanitizar, un ``<script>`` en un README se
    ejecutaría al abrir el modal.
    """
    for filename in ("README.md", "README.MD", "readme.md"):
        readme = path / filename
        if readme.is_file():
            text = readme.read_text(encoding="utf-8", errors="ignore")
            html = markdown.markdown(text, extensions=_EXTENSIONS)
            return nh3.clean(html)
    return None
