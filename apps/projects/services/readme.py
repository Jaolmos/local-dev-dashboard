"""Lectura y renderizado del README de un proyecto a HTML."""

import re
from pathlib import Path

import markdown
import nh3

_EXTENSIONS = ["fenced_code", "tables", "toc", "sane_lists"]

# Extensiones servibles como imagen del README (ver ReadmeAssetView).
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif"}

# src="..." de un <img>, para reescribir las rutas relativas.
_IMG_SRC = re.compile(r'(<img\b[^>]*?\bsrc=")([^"]+)(")', re.IGNORECASE)


def _is_external(src: str) -> bool:
    """URLs absolutas o data: se dejan como están; solo se reescribe lo relativo."""
    return src.startswith(("http://", "https://", "//", "data:", "/"))


def _rewrite_image_sources(html: str, asset_base: str) -> str:
    """Prefija las rutas relativas de <img> con ``asset_base``.

    El navegador resolvería ``screenshots/foo.png`` contra la raíz del dashboard,
    donde no hay nada; hay que apuntarlas a la vista que sirve ficheros del proyecto.
    """

    def replace(match: re.Match[str]) -> str:
        prefix, src, suffix = match.groups()
        if _is_external(src):
            return match.group(0)
        return f"{prefix}{asset_base}{src.lstrip('./')}{suffix}"

    return _IMG_SRC.sub(replace, html)


def render(path: Path, asset_base: str = "") -> str | None:
    """Renderiza el README.md del proyecto a HTML sanitizado, o None si no existe.

    La librería markdown deja pasar HTML crudo tal cual, y los README vienen de
    repos clonados (terceros): sin sanitizar, un ``<script>`` en un README se
    ejecutaría al abrir el modal.

    ``asset_base`` es el prefijo de URL desde el que se sirven las imágenes locales
    del proyecto; vacío deja las rutas tal cual (útil en tests).
    """
    for filename in ("README.md", "README.MD", "readme.md"):
        readme = path / filename
        if readme.is_file():
            text = readme.read_text(encoding="utf-8", errors="ignore")
            html = nh3.clean(markdown.markdown(text, extensions=_EXTENSIONS))
            # Reescribir después de sanitizar: nh3 no debe ver ya nuestras URLs.
            return _rewrite_image_sources(html, asset_base) if asset_base else html
    return None
