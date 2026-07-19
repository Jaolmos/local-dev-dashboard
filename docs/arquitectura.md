# Arquitectura

Cómo está montada la app y por qué. No es referencia normativa (las reglas obligatorias
viven en `.claude/.rules/`); esto es la explicación con contexto y ejemplos concretos.

## La idea central

Hay **dos velocidades** de datos, y toda la arquitectura gira en torno a esa distinción:

1. **Catálogo (SQLite, rápido)**: lo que hace falta para pintar la lista al instante.
   Nombre, ruta, descripción, stack, fecha del último commit. Se refresca **en cada carga
   de la página** (el escaneo cuesta décimas) y también desde el comando `sync_projects`.
2. **Estado vivo (bajo demanda, más lento)**: lo que puede cambiar en cualquier momento
   mientras trabajas — rama actual, si hay cambios sin commitear, ahead/behind del
   remoto. Se calcula **en cada petición**, vía HTMX, y **nunca se guarda**.

Si algo tarda (ejecutar `git`, leer y parsear un README completo), no bloquea la carga
inicial de la página: se pide aparte cuando la tarjeta ya está en pantalla.

## Las capas, de abajo arriba

```
apps/projects/
├── models.py            # Project: lo que vive en SQLite
├── services/             # lógica pura, sin saber nada de HTTP
│   ├── discovery.py       # escanea PROJECTS_ROOT, encuentra repos
│   ├── git.py              # ejecuta `git` y parsea la salida
│   ├── stack.py             # detecta tecnologías (ficheros marcadores + patrones)
│   ├── readme.py             # Markdown -> HTML sanitizado
│   └── catalog.py             # vuelca lo descubierto en SQLite (update_or_create)
├── management/commands/
│   └── sync_projects.py    # envoltorio CLI de catalog.sync (permite --prune)
├── views.py              # CBV finas: leen Project, llaman a un service, renderizan
├── urls.py               # 5 rutas
└── templates/projects/
    ├── project_list.html          # página completa (extiende base.html)
    └── partials/                    # fragmentos que devuelven las vistas HTMX
```

**Regla de oro de este proyecto:** los `services/` no saben qué es una request ni una
response. Reciben `Path` o `str`, devuelven dataclasses o listas. Eso es lo que permite
testearlos sin levantar Django ni el cliente HTTP — se ve en `tests/test_git.py`,
que llama a `git.get_status(tmp_path)` directamente.

Las vistas (`views.py`) son deliberadamente finas. Mira `GitStatusView`:

```python
class GitStatusView(SingleObjectMixin, View):
    model = Project

    def get(self, request, *args, **kwargs) -> HttpResponse:
        project = self.get_object()
        status = git.get_status(project.location)          # 1. llama al service
        return render(request, "projects/partials/git_status.html",  # 2. renderiza
                      {"project": project, "git": status})
```

Tres líneas: obtener el objeto, llamar al service, renderizar el partial. Ese patrón se
repite en `ReadmeView` y `OpenVSCodeView`. Si algún día una vista crece más que esto,
es señal de que se está colando lógica que debería vivir en `services/`.

## El escaneo (`discovery.py`) — cómo se encuentran los repos

`sync_projects` no sabe de antemano qué carpetas son proyectos. Recorre `PROJECTS_ROOT`
recursivamente hasta 3 niveles de profundidad (`_MAX_DEPTH`), y en cada carpeta:

1. Si es oculta (empieza por `.`) o no es un directorio, se ignora.
2. Si tiene `.git`, **es un proyecto**: se registra y **no se sigue bajando dentro**
   (`continue` tras el `append`, `discovery.py:69`). Así un repo no reporta como
   proyectos aparte las carpetas que tiene dentro.
3. Si no tiene `.git` y aún queda profundidad, se sigue bajando — esto es lo que permite
   que `~/Proyectos/reto_apps_2026/` (carpeta contenedora, sin `.git` propio) deje ver
   los repos que tiene dentro, como este mismo dashboard.

Por cada repo encontrado se calculan a la vez `stack.detect()` y
`git.get_last_commit()` (para poder ordenar por actividad más tarde). Ambos se guardan
ya en el `DiscoveredProject`, listos para que `sync_projects` los escriba en el catálogo.

`_MAX_DEPTH = 3` es una constante fija, no configurable desde `.env` — si algún día una
estructura de carpetas más profunda queda fuera del escaneo, ese es el primer sitio
donde tocar.

## La detección de stack (`stack.py`) — dos mecanismos

El primero es un diccionario de **ficheros marcadores** en la raíz del repo
(`STACK_MARKERS`): `manage.py` → Django, `package.json` → Node.js, `tsconfig.json` →
TypeScript, etc. Ampliarlo es añadir una línea.

El segundo son **patrones de nombre de fichero** (`GLOB_MARKERS`: `*.py`, `*.ipynb`,
`*.csproj`, `*.sln`), y existe porque muchos repos reales no tienen fichero de proyecto:
una carpeta de katas o de ejercicios es solo `.py` sueltos, y con marcadores se quedaba
sin etiqueta. Se buscan en la raíz y **hasta 2 niveles** (`_GLOB_DEPTH`), porque esos
scripts suelen estar agrupados en subcarpetas temáticas.

Dos decisiones que evitan que esto se dispare:

- Se ignoran carpetas ocultas y las de dependencias (`_IGNORED_DIRS`: `node_modules`,
  `venv`, `__pycache__`…). Sin eso, un `.venv` con miles de `.py` o el `node-gyp` de
  `node_modules` darían falsos positivos, además de ser lento.
- El árbol se recorre **una sola vez** para todos los patrones, saltando los que ya tienen
  su etiqueta puesta por marcador y cortando en cuanto no queda ninguno pendiente. Un repo
  con `pyproject.toml` ya es Python, así que no hace falta buscar ningún `*.py`.

Efecto colateral asumido: un proyecto Django reporta ahora **Django y Python**, porque
`manage.py` casa con `*.py`. Y `Makefile` se descartó como marcador por ambiguo (aparece
en repos de cualquier lenguaje).

## La sincronización del catálogo

El puente entre `discovery` (que solo lee disco) y el catálogo (SQLite) es
`services/catalog.py`. Por cada `DiscoveredProject` encontrado hace un
`update_or_create` usando `path` como clave única — así relanzarlo no duplica
proyectos, solo actualiza sus datos.

Ese service tiene **dos llamadores**:

1. **`ProjectListView`**, en cada carga de la página. El escaneo de ~16 repos cuesta
   unas décimas (la página entera se sirve en ~0,1 s), así que cabe dentro de la propia
   petición: abrir el panel muestra siempre datos frescos —fechas, orden por actividad,
   proyectos recién clonados— sin tener que ir a la terminal. Va **sin `prune`** a
   propósito, y envuelto en un `try/except OSError`: si el disco falla, se muestra el
   catálogo viejo en vez de romper la página con un 500.
2. **El comando `sync_projects`**, que sigue existiendo para sincronizar desde la
   terminal y es el único que puede pasar `--prune`.

Borrar es la única operación destructiva de la app, y por eso se ha dejado como acto
deliberado: un `--prune` automático en cada carga de página podría cargarse filas por
un fallo transitorio de disco o un `PROJECTS_ROOT` mal montado.

Con `--prune` además borra del catálogo los que ya no aparecieron en el escaneo (se
movieron o se borraron del disco). Sin `--prune`, un proyecto borrado se queda "fantasma"
en el panel hasta que se pase esa opción.

`last_synced` (`auto_now=True` en el modelo) se actualiza solo en cada
`update_or_create`, aunque hoy no se muestra en ningún sitio de la UI — quedó como dato
disponible por si hiciera falta mostrar "sincronizado hace X".

## Seguridad (aun siendo una app local)

"Local" protege de atacantes de red, **no del contenido que tú mismo te traes al disco**.
El dashboard escanea `~/Proyectos`, que es exactamente donde clonas repos de terceros, así
que hay dos superficies que cuidar.

### 1. El README es contenido no confiable

`readme.render()` pasa el Markdown por `markdown.markdown()` y **después por
`nh3.clean()`**, y el modal lo pinta con `{{ content|safe }}`. La sanitización no es
decorativa: la librería `markdown` deja pasar el HTML crudo tal cual, así que sin ella un
README con `<script>` o `<img onerror=...>` ejecutaría JS en tu navegador nada más abrir
el modal — en el mismo origen donde vive la sesión del admin de Django.

Se sanitiza **en el service**, no en la plantilla, porque es donde la arquitectura pone la
lógica: el `|safe` del template es seguro precisamente porque el HTML ya llega limpio.
Si algún día se pinta otro contenido leído del disco, debe pasar por el mismo filtro.

### 2. Ejecutar procesos del SO

La única acción que ejecuta algo del sistema operativo es "Abrir en VSCode"
(`OpenVSCodeView._open`). Antes de lanzar el proceso comprueba que la
ruta resuelta vive **dentro de `PROJECTS_ROOT`**:

```python
try:
    path.resolve().relative_to(settings.PROJECTS_ROOT.resolve())
except ValueError:
    return False
```

Esto importa porque `path` viene de `project.location`, que a su vez viene de un campo
de BD (`Project.path`) — en teoría inyectable si alguna vez se expusiera una vía para
crear/editar proyectos desde fuera de `sync_projects`. Hoy no existe esa vía (solo el
comando escribe en el catálogo), pero la comprobación queda como cinturón de seguridad
barato. Si se añadiera algún día una segunda acción del SO (abrir terminal, abrir
explorador…), debería repetir esta misma validación.

## Qué NO hace la app (por diseño)

- No vigila los repos en tiempo real (sin watcher de filesystem) ni refresca la página
  sola: lo que ves se congela hasta que recargas. Recargar sí lo actualiza todo, porque
  el sync va en la propia petición.
- No borra solo: un proyecto que desaparece del disco se queda de fantasma en el catálogo
  hasta un `sync_projects --prune` manual. Es la única operación destructiva de la app y
  se ha dejado deliberadamente fuera del camino automático.
- No escribe en los repos: todo el uso de `git` es de solo lectura (`status`,
  `rev-parse`, `rev-list`, `log`) — ver `services/git.py`.
- No tiene autenticación ni pretende exponerse fuera de `127.0.0.1`.

Ver también: [flujos HTMX](flujos-htmx.md) para el detalle petición a petición, y
[modelo de datos](modelo-datos.md) para qué guarda cada campo de `Project` y por qué.
