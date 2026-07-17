# Arquitectura

Arquitectura por capas. Cada capa tiene una responsabilidad y no salta a las de más abajo.

```
apps/<app>/
├── models.py            # datos persistidos (ORM). Sin lógica de negocio pesada.
├── services/            # lógica de negocio; NO importa vistas ni request/response.
│   ├── discovery.py     # escaneo de PROJECTS_ROOT (pathlib) + 1ª línea del README
│   ├── git.py           # estado git (subprocess, solo lectura) → dataclass GitStatus
│   ├── stack.py         # detección de stack por ficheros marcadores → list[str]
│   └── readme.py        # markdown → HTML
├── views.py             # CBV finas: orquestan services y devuelven templates/partials
├── urls.py              # rutas de la app (namespace app_name)
├── management/commands/ # comandos (sync_projects) — orquestan services + ORM
├── templates/<app>/     # plantillas y partials/ HTMX
└── tests/               # tests por capa
```

## Reglas

- **La lógica va en `services/`**, no en las vistas ni en los templates. Las vistas solo
  coordinan: obtienen el objeto, llaman al service, renderizan.
- **Los services no conocen HTTP**: reciben tipos simples (`Path`, `str`) y devuelven datos
  (dataclasses, listas, dicts). No importan `request`, `HttpResponse` ni modelos si no hace falta.
- **El catálogo (SQLite) es la fuente para la carga rápida**; las operaciones pesadas (git,
  readme) se calculan **bajo demanda** vía HTMX y **no** se persisten.
- **`config/`** es el paquete del proyecto (settings, urls, wsgi/asgi), no una app de dominio.
- Las apps de dominio viven en **`apps/`** y se declaran como `apps.<nombre>` en `INSTALLED_APPS`
  (con `label` corto en su `AppConfig`).

## Datos que NO se persisten

Estado de Git y HTML del README se calculan al vuelo. En la BD solo se guarda el catálogo:
`name`, `path`, `description`, `stack_tags`, timestamps.
