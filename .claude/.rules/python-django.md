# Python y Django

## Estilo

- Código e identificadores en **inglés**; comentarios y docstrings en **español**, mínimos.
- Type hints en funciones de services y firmas públicas. `from __future__` no hace falta (py3.12+).
- Comillas dobles, `line-length = 100` (config de ruff en `pyproject.toml`).
- Nada de lógica en `settings.py` más allá de configuración; secretos vía `django-environ`.

## Vistas

- **CBV por defecto** (`ListView`, `View` + `SingleObjectMixin`, etc.). FBV solo si simplifica.
- Vistas finas: obtienen el objeto, llaman a `services/`, renderizan template o partial.
- Endpoints HTMX devuelven **partials**, no páginas completas.

## Services

- Una responsabilidad por módulo. Funciones puras cuando se pueda (fáciles de testear).
- No acceden a `request`/`response`. Devuelven dataclasses o tipos simples.
- Subprocess: siempre lista de args (nunca `shell=True`), con `timeout`, y manejo de errores.

## Modelos

- `__str__` útil, `Meta.ordering` explícito.
- Migraciones siempre versionadas y aplicadas (`makemigrations` + `migrate`).

## Seguridad (aunque sea local)

- Acciones que ejecutan comandos del SO (abrir VSCode) validan que la ruta pertenece a un
  `Project` existente y vive bajo `PROJECTS_ROOT`. Nunca ejecutar rutas libres del cliente.
- **El contenido de los repos escaneados es de terceros**: lo que se lea del disco y se
  pinte con `|safe` va sanitizado antes (el README pasa por `nh3.clean`). "Es local" protege
  de atacantes de red, no de un repo clonado con HTML malicioso dentro.
- Las peticiones htmx que escriben (`hx-post`) necesitan el token CSRF; lo aporta el
  `hx-headers` del `<body>` en `base.html`, que se hereda a toda la página.
