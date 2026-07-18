# Local Dev Dashboard

Panel de control web **local** para Linux que cataloga tus proyectos de código y muestra, de un
vistazo, cómo va cada uno: estado de Git, stack detectado, README y última actividad, con acciones
rápidas (abrir en VSCode, leer la documentación).

Es una herramienta **solo-local**: pensada para correr en `127.0.0.1` mientras trabajas, nunca para
desplegar a producción. Está pensada y probada **para Linux**.

## Qué hace

- **Escanea** la carpeta donde guardas tus proyectos (recursivamente, hasta 3 niveles) y detecta
  cualquier directorio que sea un repositorio Git.
- **Ordena por actividad**: lo más reciente arriba, los repos sin commits al final.
- **Detecta el stack** por ficheros marcadores (`pyproject.toml`, `package.json`, `go.mod`…) y lo
  muestra como etiquetas con color por tecnología.
- **Estado de Git en vivo**, cargado bajo demanda vía HTMX al aparecer cada tarjeta: rama, si hay
  cambios sin confirmar y cuántos commits llevas por delante/por detrás del remoto.
- **README en un modal**, renderizado de Markdown a HTML sin salir del panel.
- **Abrir en VSCode** con un clic.

## Requisitos

- **Linux** (es el único sistema en el que se ha probado; las rutas y la acción de abrir en VSCode
  asumen un entorno tipo Unix)
- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/)
- `git` disponible en el `PATH`
- Opcional: el comando `code` en el `PATH` para la acción "Abrir en VSCode"

## Puesta en marcha

```bash
# 1. Dependencias (uv crea el entorno en .venv)
uv sync

# 2. Configuración: copia la plantilla y ajústala
cp .env.example .env
```

Edita el `.env` y ajusta al menos **`PROJECTS_ROOT`**, la carpeta raíz donde viven tus proyectos.
Admite `~` para tu home, así que vale cualquiera de estas:

```ini
PROJECTS_ROOT=~/Proyectos
PROJECTS_ROOT=~/code
PROJECTS_ROOT=/home/tu-usuario/dev
```

Genera también tu propia `DJANGO_SECRET_KEY`:

```bash
uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Después:

```bash
# 3. Base de datos
uv run python manage.py migrate

# 4. IMPORTANTE: llena el catálogo escaneando PROJECTS_ROOT
uv run python manage.py sync_projects

# 5. Arranca (compila Tailwind y vigila cambios)
uv run python manage.py tailwind runserver
```

Abre <http://127.0.0.1:8000/>.

> **Ojo con el paso 4.** `migrate` solo crea las tablas, vacías. Si arrancas sin ejecutar
> `sync_projects` verás el panel sin ningún proyecto. Y como la fecha de último commit se toma
> durante la sincronización, vuelve a lanzarlo cada vez que quieras refrescar la actividad:
> mientras no lo hagas, las fechas mostradas envejecen.

## Comandos habituales

```bash
uv run python manage.py runserver             # servidor de desarrollo (sin watch de Tailwind)
uv run python manage.py tailwind runserver    # servidor + watch de Tailwind (recomendado en dev)
uv run python manage.py sync_projects         # escanea PROJECTS_ROOT y actualiza el catálogo
uv run python manage.py sync_projects --prune # además, borra del catálogo lo que ya no existe
uv run python manage.py sync_projects --root ~/otra-carpeta   # escanea otra raíz puntualmente
uv run pytest -x -v                           # tests
```

## Cómo está montado

Arquitectura por capas: `models` → `services` → `views` → `templates`/`partials` → `tests`.

```
apps/projects/
├── models.py            # catálogo persistido (nombre, ruta, stack, last_commit)
├── services/            # lógica de negocio, sin saber nada de HTTP
│   ├── discovery.py     # escaneo recursivo de PROJECTS_ROOT
│   ├── git.py           # estado y último commit (subprocess, solo lectura)
│   ├── stack.py         # detección de stack por ficheros marcadores
│   └── readme.py        # Markdown → HTML
├── views.py             # CBV finas: orquestan services y devuelven partials
└── templates/projects/  # plantillas y partials HTMX
```

En SQLite solo vive el **catálogo**, que es lo que permite pintar la lista al instante. El estado
vivo de Git y el HTML del README se calculan al vuelo bajo demanda y **no** se guardan. La única
excepción deliberada es `last_commit`: se persiste porque el orden por actividad lo hace la base de
datos, y no se puede ordenar por un dato que se calcula al renderizar.

Stack: Django 6 + HTMX + partials nativos de Django (`{% partialdef %}`), Tailwind v4 vía
`django-tailwind-cli` (binario standalone, sin Node) y SQLite.

Más detalle en [`.claude/.rules/`](.claude/.rules/): arquitectura, convenciones de Python/Django,
frontend, testing y git.

## Tests

```bash
uv run pytest -x -v
uv run pytest apps/projects/tests/test_git.py
```

Las acciones que lanzan procesos del sistema (abrir VSCode) se prueban siempre con `subprocess`
mockeado; los tests nunca abren ventanas reales.
