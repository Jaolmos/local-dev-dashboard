from pathlib import Path

from django.db import models
from django.db.models import F


class Project(models.Model):
    """Proyecto de código detectado bajo la carpeta raíz configurada."""

    name = models.CharField(max_length=200)
    path = models.CharField(max_length=1000, unique=True)
    description = models.CharField(max_length=500, blank=True)
    stack_tags = models.JSONField(default=list, blank=True)
    # Fecha del último commit: se toma en cada sync para poder ordenar por actividad.
    last_commit = models.DateTimeField(null=True, blank=True)
    last_synced = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Lo más reciente arriba; los repos sin commits, al final.
        ordering = [F("last_commit").desc(nulls_last=True), "name"]

    def __str__(self) -> str:
        return self.name

    @property
    def location(self) -> Path:
        return Path(self.path)
