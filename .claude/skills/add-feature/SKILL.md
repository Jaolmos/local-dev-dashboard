---
name: add-feature
description: Añadir una nueva funcionalidad al dashboard siguiendo la arquitectura por capas de Django (models → services → views → templates/partials → tests).
---

# Skill: Añadir feature (Django por capas)

Sigue este orden. Respeta las convenciones: código en inglés, comentarios/docstrings en español
(los justos), CBV por defecto, commits `tipo:` EN + descripción ES (sin `Co-Authored-By`).

Pasos:

1. **Modelo** (si hace falta persistir): editar `apps/<app>/models.py`. Mantener el modelo
   simple; la lógica pesada va en services. Registrar en `admin.py` si aporta.
2. **Migración**: `uv run python manage.py makemigrations` y revisar el fichero generado.
3. **Service**: crear/editar `apps/<app>/services/<nombre>.py` con la lógica de negocio.
   Funciones puras cuando se pueda; sin `request`/`response`; devolver dataclasses o tipos simples.
   Subprocess siempre con lista de args, `timeout` y manejo de errores (nunca `shell=True`).
4. **Vista** (CBV): editar `apps/<app>/views.py`. La vista es fina: obtiene el objeto, llama al
   service, renderiza. Los endpoints HTMX devuelven un **partial**, no la página completa.
5. **URL**: añadir la ruta en `apps/<app>/urls.py` (namespace `app_name`).
6. **Template / partial**: crear el partial en `apps/<app>/templates/<app>/partials/` y cablearlo
   con atributos `hx-*` (ver `.claude/.rules/frontend.md` para los patrones: `revealed`, modal, `outerHTML`).
   Estilar con Tailwind.
7. **Tailwind**: si añades clases nuevas, `uv run python manage.py tailwind build` (o `watch`).
8. **Tests**: en `apps/<app>/tests/` cubrir el service (prioritario) y la vista (status + partial
   correcto). Mockear efectos del SO. Ver `.claude/.rules/testing.md`.
9. **Verificar**: `uv run pytest -x -v` y probar en el navegador (`tailwind runserver`).
10. **Revisar**: pasar `/code-review` o el subagente `code-reviewer` sobre el diff (revisión en el
    límite de la feature).
11. **Commit**: `feat: <descripción en español>` (en `main`; este proyecto no usa ramas por feature).
