# Flujos HTMX

Cómo viaja cada interacción del navegador al servidor y de vuelta: qué la dispara, qué
vista la atiende y qué partial devuelve.

htmx se carga por CDN en `base.html` (`unpkg.com/htmx.org@2.0.4`) — no hay build de JS,
todo es atributos `hx-*` sobre HTML normal.

## 1. Carga de la página — sin HTMX, es Django puro

```
GET /  →  ProjectListView (ListView)  →  catalog.sync(PROJECTS_ROOT)   # refresca el catálogo
       →  Project.objects.all() (ya ordenado por Meta.ordering)
       →  project_list.html  →  incluye legend.html + un project_card.html por proyecto
```

El sync escanea el disco antes de renderizar, así que la lista sale siempre fresca —fechas,
orden por actividad y proyectos recién clonados— sin pasar por la terminal. Cuesta unas
décimas (la página entera se sirve en ~0,1 s con 16 repos), y va sin `prune`: borrar del
catálogo sigue siendo manual.

Aun así **no se ejecuta ningún `git status`** en esta petición: el sync solo lee `git log`
para la fecha del último commit. El estado vivo va aparte. Cada
tarjeta sale con un punto gris pulsante (`bg-ink-700 animate-pulse`,
`project_card.html:18`) en el hueco donde irá el estado de Git — ese hueco lleva
`hx-trigger="revealed"`, así que la petición real se dispara sola en cuanto el
navegador pinta esa tarjeta en pantalla:

```html
<div hx-get="{% url 'projects:git-status' project.pk %}"
     hx-trigger="revealed"
     hx-swap="innerHTML">
```

`revealed` es un evento propio de htmx: se dispara la primera vez que el elemento entra
en el viewport (scroll incluido). Con 16+ proyectos en el catálogo real, esto evita
lanzar 16 `git status` de golpe al cargar — solo se piden los que están a la vista.

## 2. Estado de Git de una tarjeta

```
GET /<pk>/git/  →  GitStatusView.get()
                →  git.get_status(project.location)   # ejecuta git de verdad, timeout=5s
                →  partials/git_status.html
```

`git.get_status` hace tres llamadas a `git` por repo (`rev-parse --abbrev-ref HEAD`,
`status --porcelain`, `rev-list --left-right --count @{u}...HEAD`) y punto — nunca
escribe. El resultado es un `GitStatus` (dataclass, no un modelo) que **no se guarda en
ningún sitio**; si vuelves a la página se vuelve a pedir desde cero.

El partial decide qué pintar según los campos:
- `is_repo=False` → "sin git" en gris (pasaría si `.git` desapareciera entre el sync y
  ahora, caso raro pero cubierto).
- `is_dirty` → badge ámbar "con cambios"; si no, badge verde "sin cambios"
  (`status_badge.html`, compartido con la leyenda para que el color signifique lo mismo
  en los dos sitios).
- `ahead`/`behind` → flechas `↑N`/`↓N`, solo si hay `has_upstream` y el número no es 0
  (la plantilla comprueba truthy, así que `ahead=0` no pinta nada).

## 3. Abrir el README (modal)

```
GET /<pk>/readme/  →  ReadmeView.get()
                   →  readme.render(project.location)   # lee README.md, markdown.markdown()
                   →  partials/readme_modal.html
```

Target especial: en vez de reemplazar algo dentro de la tarjeta, el botón "Docs" apunta
a un contenedor vacío que vive fuera del grid, al final de `base.html`:

```html
<div id="modal-root"></div>
```

```html
hx-get="{% url 'projects:readme' project.pk %}"
hx-target="#modal-root"
hx-swap="innerHTML"
```

El HTML que llega ya trae el overlay completo (fondo oscuro + tarjeta centrada) y se
cierra solo, sin JS de Django ni vista extra: el `onclick` del overlay comprueba
`event.target === this` (para no cerrar al clicar dentro de la tarjeta) y el botón ✕
hace `this.closest('.fixed').remove()`. Es el único sitio de la app con JS inline —
justificado porque abrir/cerrar un modal no merece una librería ni una vista de Django.

Si el README no existe, `readme.render()` devuelve `None` y el partial muestra el
mensaje "Este proyecto no tiene README.md" en vez de dejar el modal vacío.

## 4. Abrir en VSCode

```
POST /<pk>/open/  →  OpenVSCodeView.post()
                  →  valida que la ruta vive bajo PROJECTS_ROOT
                  →  subprocess.Popen(["code", str(path)])   # no bloqueante, no espera
                  →  partials/open_result.html
```

```html
hx-post="{% url 'projects:open-vscode' project.pk %}"
hx-swap="outerHTML"
```

`outerHTML` es la clave aquí: el botón **se sustituye a sí mismo** por el resultado
(`open_result.html`), un botón `disabled` con "Abierto ✓" o "Error al abrir" según si
`Popen` lanzó sin excepción.

Ese feedback es **transitorio**: el propio partial trae `hx-trigger="load delay:2s"`
apuntando a `open-button`, así que a los dos segundos el botón vuelve a su estado normal
y se puede reabrir sin recargar. Los dos segundos disabled hacen de paso el trabajo de
evitar el doble clic que abriría VSCode dos veces.

```
GET /<pk>/open/button/  →  OpenButtonView.get()  →  partials/open_button.html
```

El botón vive en su propio partial precisamente para esto: lo incluyen tanto
`project_card.html` como el endpoint de restauración, así que no pueden desincronizarse.

`Popen` (no `run`) porque no interesa esperar a que VSCode termine ni capturar su
salida; el proceso queda huérfano del servidor Django a propósito.

Ojo: sin token CSRF este POST se va en **403**. Lo cubre el `hx-headers` del `<body>` de
`base.html`, que htmx hereda a todos los descendientes.

## Resumen de las 5 rutas

| Ruta | Vista | Dispara | Devuelve |
|---|---|---|---|
| `GET /` | `ProjectListView` | carga de página (sincroniza el catálogo) | página completa |
| `GET /<pk>/git/` | `GitStatusView` | `hx-trigger="revealed"` de cada tarjeta | `git_status.html` |
| `GET /<pk>/readme/` | `ReadmeView` | clic en "Docs" | `readme_modal.html` (a `#modal-root`) |
| `POST /<pk>/open/` | `OpenVSCodeView` | clic en "Abrir en VSCode" | `open_result.html` (reemplaza el botón) |
| `GET /<pk>/open/button/` | `OpenButtonView` | `load delay:2s` desde `open_result.html` | `open_button.html` (restaura el botón) |

Ver también: [arquitectura](arquitectura.md) para el porqué de la separación
catálogo / estado-vivo.
