"""Filtros de presentación para las plantillas del catálogo."""

from django import template

register = template.Library()

# Clases Tailwind por tecnología: dan color propio a cada tag de stack.
_STACK_CLASSES: dict[str, str] = {
    "Django": "bg-emerald-500/10 text-emerald-300 ring-emerald-500/20",
    "Python": "bg-amber-500/10 text-amber-300 ring-amber-500/20",
    "Docker": "bg-sky-500/10 text-sky-300 ring-sky-500/20",
    "Node.js": "bg-lime-500/10 text-lime-300 ring-lime-500/20",
    "Go": "bg-cyan-500/10 text-cyan-300 ring-cyan-500/20",
    "Rust": "bg-orange-500/10 text-orange-300 ring-orange-500/20",
    "Java": "bg-red-500/10 text-red-300 ring-red-500/20",
    "PHP": "bg-indigo-500/10 text-indigo-300 ring-indigo-500/20",
    "Ruby": "bg-rose-500/10 text-rose-300 ring-rose-500/20",
}

_DEFAULT_CLASSES = "bg-ink-800/80 text-ink-300 ring-ink-700"


@register.filter
def stack_color(tag: str) -> str:
    """Devuelve las clases de color del tag de stack indicado."""
    return _STACK_CLASSES.get(tag, _DEFAULT_CLASSES)
