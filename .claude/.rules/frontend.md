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

- Fragmentos reutilizables en `partials/`. Usar `django-template-partials` (`{% partialdef %}`)
  cuando el fragmento vive junto a su template; ficheros sueltos cuando se reutilizan.
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
