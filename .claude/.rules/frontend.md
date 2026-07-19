# Frontend

Plantillas Django + HTMX + partials. Cero JavaScript propio salvo que sea imprescindible.

## HTMX

- Interactividad con atributos `hx-*`. Patrones usados:
  - **Carga diferida** de datos pesados: `hx-get` + `hx-trigger="revealed"` (el estado git de
    cada tarjeta se pide al aparecer en pantalla).
  - **Modal** sin recargar: `hx-get` con `hx-target="#modal-root"` (README).
  - **Acción** con feedback: `hx-post` + `hx-swap="outerHTML"` (abrir en VSCode).
- Cada endpoint HTMX devuelve un **partial** de `templates/<app>/partials/`.
- `django-htmx` está activo (middleware); usar `request.htmx` si se necesita distinguir.

## Partials

- **Todo partial que sirva un endpoint HTMX va en un fichero suelto** en `partials/`, y la vista
  lo renderiza con `render(request, "app/partials/x.html", ...)`. No es una preferencia: Django 6
  trae `{% partialdef %}`/`{% partial %}` en el core, pero **no** soporta renderizar
  `plantilla.html#fragmento` desde una vista (da `TemplateDoesNotExist`), así que un `partialdef`
  no se puede devolver por HTTP.
- `{% partialdef %}` queda para fragmentos que solo se repiten **dentro de una misma plantilla**.
  Hoy el proyecto no usa ninguno; todos sus partials los sirve una vista o los incluye otra
  plantilla con `{% include %}`.
- **Nombrado:** los partials NO llevan prefijo `_`; la carpeta `partials/` ya indica que lo son.

## Tailwind

- `django-tailwind-cli` (sin Node). CSS de entrada: `assets/css/source.css` (Tailwind v4,
  `@import "tailwindcss"` + `@source`). Salida compilada: `assets/css/tailwind.css` (gitignored).
- En dev usar `manage.py tailwind runserver` (compila y vigila). Cargar el CSS con
  `{% tailwind_css %}` (tras `{% load tailwind_cli %}`).
- Clases utilitarias en las plantillas; evitar CSS suelto salvo casos justificados.

## Objetivo de diseño

La UI debe ser **atractiva y profesional** (no el maquetado básico). Para trabajo de diseño
serio, usar la skill `frontend-design`. El `<head>` se queda en `base.html`; el `<header>`
visible (barra superior) va en un partial aparte (`partials/header.html`).
