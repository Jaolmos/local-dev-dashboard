"""Vistas del panel: listado desde SQLite y operaciones bajo demanda vía HTMX."""

import logging
import subprocess

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import ListView
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin

from .models import Project
from .services import catalog, git, readme

logger = logging.getLogger(__name__)


class ProjectListView(ListView):
    """Listado del catálogo, resincronizado con el disco en cada carga."""

    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"

    def get(self, request, *args, **kwargs) -> HttpResponse:
        # El escaneo cuesta décimas, así que cabe en la propia petición: abrir el
        # panel siempre muestra datos frescos. Sin --prune: borrar sigue siendo manual.
        try:
            catalog.sync(settings.PROJECTS_ROOT)
        except OSError:
            # Si el disco falla, mejor el catálogo viejo que una página rota.
            logger.exception("Falló la sincronización del catálogo")
        return super().get(request, *args, **kwargs)


class GitStatusView(SingleObjectMixin, View):
    """Estado de Git diferido para una tarjeta (partial HTMX)."""

    model = Project

    def get(self, request, *args, **kwargs) -> HttpResponse:
        project = self.get_object()
        status = git.get_status(project.location)
        return render(
            request,
            "projects/partials/git_status.html",
            {"project": project, "git": status},
        )


class ReadmeView(SingleObjectMixin, View):
    """Renderiza el README del proyecto en un modal (partial HTMX)."""

    model = Project

    def get(self, request, *args, **kwargs) -> HttpResponse:
        project = self.get_object()
        content = readme.render(project.location)
        return render(
            request,
            "projects/partials/readme_modal.html",
            {"project": project, "content": content},
        )


class OpenButtonView(SingleObjectMixin, View):
    """Devuelve el botón de abrir a su estado inicial tras el feedback."""

    model = Project

    def get(self, request, *args, **kwargs) -> HttpResponse:
        return render(
            request,
            "projects/partials/open_button.html",
            {"project": self.get_object()},
        )


class OpenVSCodeView(SingleObjectMixin, View):
    """Abre el proyecto en VSCode ejecutando ``code <ruta>``."""

    model = Project

    def post(self, request, *args, **kwargs) -> HttpResponse:
        project = self.get_object()
        ok = self._open(project.location)
        return render(
            request,
            "projects/partials/open_result.html",
            {"project": project, "ok": ok},
        )

    @staticmethod
    def _open(path) -> bool:
        # Solo se abren rutas que viven bajo PROJECTS_ROOT (evita ejecución arbitraria).
        try:
            path.resolve().relative_to(settings.PROJECTS_ROOT.resolve())
        except ValueError:
            return False
        try:
            subprocess.Popen(["code", str(path)])
            return True
        except (OSError, subprocess.SubprocessError):
            return False
