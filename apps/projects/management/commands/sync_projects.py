"""Sincroniza el catálogo de proyectos en SQLite desde la carpeta raíz."""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.projects.services import catalog


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
        result = catalog.sync(root, prune=options["prune"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Sincronización completada: {result.created} creados, "
                f"{result.updated} actualizados, {result.pruned} eliminados (raíz: {root})."
            )
        )
