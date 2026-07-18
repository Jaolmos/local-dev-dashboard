# Local Dev Dashboard

Panel de control web **local** (Linux) que cataloga tus proyectos de código y muestra, de un
vistazo, cómo va cada uno: estado de Git, stack detectado, README y última actividad, con
acciones rápidas (abrir en VSCode, leer docs). Es una herramienta **solo-local, nunca a
producción**: prioriza simplicidad y DX sobre hardening.

## Stack

- **Backend:** Django 6.0.x. Paquete de proyecto: `config`. Apps de dominio bajo `apps/`.
- **Gestor:** `uv` + `pyproject.toml` (entorno en `.venv`, usar `uv run <cmd>`).
- **Frontend:** plantillas Django + HTMX (`django-htmx`) + partials nativos de Django 6
  (`{% partialdef %}` / `{% partial %}`, sin librería aparte).
- **CSS:** Tailwind vía `django-tailwind-cli` (binario standalone, sin Node). htmx por CDN.
- **BD:** SQLite (catálogo de proyectos).
- **Git:** comandos nativos vía `subprocess` (sin GitPython). Requiere `git` en el sistema.
- **Markdown:** librería `markdown` para renderizar README.
- **Config:** `django-environ` (`.env`: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `PROJECTS_ROOT`).
- **Tests:** `pytest` + `pytest-django`.

## Convenciones (obligatorias)

- **Idioma:** código e identificadores en **inglés**; comentarios y docstrings en **español**,
  solo los justos y necesarios.
- **Commits:** conventional commits con **tipo en inglés** (`feat:`, `fix:`, `chore:`, `docs:`,
  `refactor:`, `test:`, `style:`) y **descripción en español**. **Sin** trailer `Co-Authored-By`.
- **Vistas:** basadas en clases (CBV) por defecto; FBV solo si aporta claridad.
- **Arquitectura por capas:** `models` → `services` → `views` → `templates`/`partials` → `tests`.
  La lógica de negocio (git, discovery, stack, readme) vive en `apps/<app>/services/`, no en las vistas.

Detalle por área en `.claude/.rules/`:
- @.claude/.rules/architecture.md
- @.claude/.rules/python-django.md
- @.claude/.rules/frontend.md
- @.claude/.rules/testing.md
- @.claude/.rules/git-conventions.md

## Documentación de la app

Cómo funciona por dentro (las reglas de arriba dicen *cómo escribir*; esto explica *qué
hay ya construido y por qué*):
- @docs/arquitectura.md
- @docs/flujos-htmx.md
- @docs/modelo-datos.md
- @docs/admin.md

## Comandos habituales

```bash
uv run python manage.py runserver             # servidor de desarrollo
uv run python manage.py tailwind runserver    # server + watch de Tailwind (dev)
uv run python manage.py makemigrations        # tras cambiar modelos
uv run python manage.py migrate               # aplicar migraciones
uv run python manage.py sync_projects         # escanear PROJECTS_ROOT → catálogo
uv run pytest -x -v                           # tests
```

## Añadir una feature

Sigue la skill `add-feature` (flujo por capas). Para trabajo de UI, la skill `frontend-design`.
