# Arquitectura

Arquitectura por capas. Cada capa tiene una responsabilidad y no salta a las de más abajo.

```
apps/<app>/
├── models.py            # datos persistidos (ORM). Sin lógica de negocio pesada.
├── services/            # lógica de negocio; NO importa vistas ni request/response.
│   ├── discovery.py     # escaneo de PROJECTS_ROOT (pathlib) + 1ª línea del README
│   ├── git.py           # estado git (subprocess, solo lectura) → dataclass GitStatus
│   ├── stack.py         # stack por ficheros marcadores y patrones → list[str]
│   ├── readme.py        # markdown → HTML sanitizado (nh3)
│   └── catalog.py       # vuelca lo descubierto en SQLite → dataclass SyncResult
├── views.py             # CBV finas: orquestan services y devuelven templates/partials
├── urls.py              # rutas de la app (namespace app_name)
├── management/commands/ # comandos (sync_projects) — envoltorio CLI de un service
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
- **La lógica compartida entre un comando y una vista vive en un service**, no en el comando:
  `sync_projects` es un envoltorio CLI de `catalog.sync`, que también usa `ProjectListView`.
- **`config/`** es el paquete del proyecto (settings, urls, wsgi/asgi), no una app de dominio.
- Las apps de dominio viven en **`apps/`** y se declaran como `apps.<nombre>` en `INSTALLED_APPS`
  (con `label` corto en su `AppConfig`).

## Qué se persiste y qué no

En la BD solo vive el **catálogo**, que es lo que permite pintar la lista al instante:
`name`, `path`, `description`, `stack_tags`, `last_commit`, timestamps.

El **estado vivo de Git** (rama, cambios sin confirmar, ahead/behind) y el **HTML del README**
se calculan al vuelo bajo demanda vía HTMX y **no** se guardan.

`last_commit` es la excepción deliberada: se toma en cada sincronización como instantánea,
no en vivo. Se persiste porque el orden por actividad lo hace la BD y no se puede ordenar por
un dato que se calcula al renderizar. Como el catálogo se sincroniza en cada carga de la
página, esa instantánea es siempre reciente; solo envejece si dejas la pestaña abierta.
