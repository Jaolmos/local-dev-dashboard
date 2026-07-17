"""Vistas del panel: listado desde SQLite y operaciones bajo demanda vía HTMX."""

import subprocess

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import ListView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.base import View

from .models import Project
from .services import git, readme


class ProjectListView(ListView):
    """Carga instantánea del catálogo de proyectos desde SQLite."""

    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"


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
