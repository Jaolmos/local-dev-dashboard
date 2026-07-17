"""Sincroniza el catálogo de proyectos en SQLite desde la carpeta raíz."""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.projects.models import Project
from apps.projects.services import discovery


class Command(BaseCommand):
    help = "Escanea PROJECTS_ROOT y actualiza el catálogo de proyectos en la base de datos."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--root",
            type=Path,
            default=settings.PROJECTS_ROOT,
            help="Carpeta raíz a escanear (por defecto settings.PROJECTS_ROOT).",
        )
        parser.add_argument(
            "--prune",
            action="store_true",
            help="Elimina del catálogo los proyectos que ya no existen en disco.",
        )

    def handle(self, *args, **options) -> None:
        root: Path = options["root"]
        found = discovery.scan_projects(root)
        seen_paths = set()
        created = updated = 0

        for item in found:
            path_str = str(item.path)
            seen_paths.add(path_str)
            _, was_created = Project.objects.update_or_create(
                path=path_str,
                defaults={
                    "name": item.name,
                    "description": item.description,
                    "stack_tags": item.stack_tags,
                },
            )
            created += was_created
            updated += not was_created

        pruned = 0
        if options["prune"]:
            stale = Project.objects.exclude(path__in=seen_paths)
            pruned = stale.count()
            stale.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Sincronización completada: {created} creados, {updated} actualizados, "
                f"{pruned} eliminados (raíz: {root})."
            )
        )
