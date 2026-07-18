# Tests de `apps/projects`

Suite con **pytest** + **pytest-django**. La configuración vive en `pyproject.toml`
(`[tool.pytest.ini_options]`): `DJANGO_SETTINGS_MODULE = "config.settings"` y
`testpaths = ["apps"]`, así que no hace falta pasar rutas para descubrirlos.

## Cómo ejecutarlos

```bash
uv run pytest                              # toda la suite
uv run pytest -x -v                        # para en el primer fallo, salida detallada
uv run pytest apps/projects/tests/test_git.py          # un fichero
uv run pytest apps/projects/tests/test_git.py::test_status_clean_repo   # un test suelto
uv run pytest -k last_commit               # los que casen con la expresión
```

No hay `conftest.py`: cada fichero define las fixtures que necesita.

## Qué cubre cada fichero

Un fichero por área, siguiendo las capas de la app:

| Fichero | Qué prueba | Nº |
|---|---|---|
| `test_discovery.py` | escaneo recursivo de `PROJECTS_ROOT`, detección de repos anidados, lectura de descripción | 10 |
| `test_git.py` | estado git y fecha del último commit sobre **repos reales** | 9 |
| `test_stack.py` | detección de stack por ficheros marcadores | 4 |
| `test_readme.py` | renderizado de Markdown a HTML | 3 |
| `test_templatetags.py` | el filtro `stack_color` (color por tecnología) | 3 |
| `test_views.py` | vistas CBV: status, partial correcto, orden por actividad, acción de VSCode | 6 |

## Enfoque por capa

**Services** (el núcleo, máxima prioridad de cobertura). Son funciones puras que reciben
`Path`/`str` y devuelven datos, así que se prueban **sin levantar Django ni el cliente
HTTP**: se les pasa un `tmp_path` directamente.

- `discovery`, `stack`, `readme` → se montan directorios temporales con `tmp_path` y sus
  ficheros marcadores / README de ejemplo.
- `git` → se inicializa un **repo git de verdad** en `tmp_path`. La fixture `repo` de
  `test_git.py` hace `git init -b main`, configura un usuario de prueba y deja un commit
  inicial. Los casos límite (repo sin commits, timeout, salida no-fecha) se cubren con
  `monkeypatch` sobre `subprocess`.

**Vistas.** Usan el `client` de pytest-django y llevan `pytestmark = pytest.mark.django_db`
(marca todo el módulo, porque tocan la BD). Verifican dos cosas: el `status_code` y que se
devuelve el **partial correcto** (`_template_names(response)` compara contra
`response.templates`). La fixture `project` apunta `settings.PROJECTS_ROOT` a `tmp_path`
para que la ruta del proyecto pase la validación de seguridad.

## Efectos del sistema operativo — nunca reales

La acción "Abrir en VSCode" lanza un proceso (`subprocess.Popen(["code", ...])`). En los
tests **siempre se mockea** con `monkeypatch`; jamás se abre VSCode de verdad. Se cubren
los dos caminos:

- ruta **bajo** `PROJECTS_ROOT` → se llama a `Popen` con `code` (se comprueba
  inspeccionando los args capturados).
- ruta **fuera** de `PROJECTS_ROOT` (p. ej. `/etc`) → **no se ejecuta nada** y la vista
  responde "Error al abrir".

Esta es la garantía de seguridad descrita en
[`.claude/.rules/python-django.md`](../../../.claude/.rules/python-django.md): las
acciones del SO solo corren sobre rutas que viven bajo `PROJECTS_ROOT`.

## Convenciones

- **Nombres en inglés** (funciones y variables), como todo el código; solo los comentarios
  y docstrings van en español.
- Nombres descriptivos con el patrón `test_<qué>_<condición>_<resultado>`, p. ej.
  `test_open_vscode_path_outside_root_does_not_run`.

Ver también: [`docs/arquitectura.md`](../../../docs/arquitectura.md) para las capas que se
prueban aquí, y [`.claude/.rules/testing.md`](../../../.claude/.rules/testing.md) para las
reglas de testing del proyecto.
