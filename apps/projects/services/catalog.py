"""Sincronización del catálogo: escaneo de disco -> filas de Project."""

from dataclasses import dataclass
from pathlib import Path

from apps.projects.models import Project

from . import discovery


@dataclass(frozen=True)
class SyncResult:
    """Recuento de lo que hizo una sincronización."""

    created: int = 0
    updated: int = 0
    pruned: int = 0


def sync(root: Path, *, prune: bool = False) -> SyncResult:
    """Escanea ``root`` y refleja lo encontrado en el catálogo.

    Idempotente: usa ``path`` como clave, así que relanzarlo actualiza en vez de duplicar.
    """
    seen_paths = set()
    created = updated = 0

    for item in discovery.scan_projects(root):
        path_str = str(item.path)
        seen_paths.add(path_str)
        _, was_created = Project.objects.update_or_create(
            path=path_str,
            defaults={
                "name": item.name,
                "description": item.description,
                "stack_tags": item.stack_tags,
                "last_commit": item.last_commit,
            },
        )
        created += was_created
        updated += not was_created

    pruned = 0
    if prune:
        stale = Project.objects.exclude(path__in=seen_paths)
        pruned = stale.count()
        stale.delete()

    return SyncResult(created=created, updated=updated, pruned=pruned)
