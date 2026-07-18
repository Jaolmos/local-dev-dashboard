# Modelo de datos

Un único modelo, `Project` (`apps/projects/models.py`). Qué guarda cada campo, de dónde
sale y por qué está — o no está — persistido.

```python
class Project(models.Model):
    name = models.CharField(max_length=200)
    path = models.CharField(max_length=1000, unique=True)
    description = models.CharField(max_length=500, blank=True)
    stack_tags = models.JSONField(default=list, blank=True)
    last_commit = models.DateTimeField(null=True, blank=True)
    last_synced = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = [F("last_commit").desc(nulls_last=True), "name"]
```

| Campo | Origen | Cuándo se actualiza |
|---|---|---|
| `name` | nombre de la carpeta (`entry.name` en `discovery._walk`) | cada `sync_projects` |
| `path` | ruta absoluta de la carpeta, **clave única** | fijo tras la primera sync (es la clave del `update_or_create`) |
| `description` | primera línea no vacía del README, sin el `#` (`discovery._read_description`) | cada `sync_projects` |
| `stack_tags` | lista de tecnologías detectadas (`stack.detect`) | cada `sync_projects` |
| `last_commit` | `git log -1 --format=%cI` del repo, parseado a `datetime` (`git.get_last_commit`) | cada `sync_projects` — **es una foto fija**, no vive |
| `last_synced` | `auto_now=True`, lo pone Django solo | cada vez que el registro se toca (create o update) |
| `created_at` | `auto_now_add=True`, lo pone Django solo | una sola vez, al crearse el registro |

`path` como clave única es lo que hace que `sync_projects` sea idempotente: relanzarlo
sobre los mismos repos actualiza los mismos registros en vez de duplicarlos, porque
`update_or_create(path=path_str, defaults={...})` busca por esa columna.

## Por qué `last_commit` rompe la regla "estado de git no se persiste"

El resto del estado de git (rama, dirty, ahead/behind) se calcula al vuelo y nunca toca
la BD — ver [flujos HTMX](flujos-htmx.md). `last_commit` es la única excepción, y es
deliberada:
**el orden de la lista lo hace SQLite** (`Meta.ordering`), y SQLite no puede ordenar por
un valor que todavía no existe hasta que se renderiza la plantilla. Para poder hacer
"lo más reciente arriba" hace falta que la fecha ya esté en la fila antes del `SELECT`.

Contrapartida directa: la fecha que ves en cada tarjeta ("hace 3 días") es la que había
en el último `sync_projects`, no la real en este instante. Si hicieras un commit ahora
mismo en uno de tus proyectos, la tarjeta seguiría mostrando la fecha vieja —y el
proyecto seguiría en su posición vieja del orden— hasta el siguiente
`sync_projects`. Esto está avisado en el `README.md` del proyecto, no es un bug latente.

## `Meta.ordering` con `F(...).desc(nulls_last=True)`

```python
ordering = [F("last_commit").desc(nulls_last=True), "name"]
```

Dos detalles que no son obvios a simple vista:

- **`F()` en vez de un string** (`"-last_commit"`) es necesario específicamente por
  `nulls_last=True`. La sintaxis corta `"-campo"` de Django no tiene forma de expresar
  "nulos al final"; solo `F("campo").desc(nulls_last=True)` lo permite.
- **Por qué hacen falta nulos al final**: un proyecto recién detectado sin ningún commit
  (`git log` vacío) tiene `last_commit=None`. Sin `nulls_last=True`, SQLite pondría esos
  `NULL` **primero** en un `ORDER BY ... DESC`, así que los repos vacíos aparecerían
  arriba del todo, tapando a los proyectos realmente activos. `nulls_last=True` los
  manda al final, que es donde tiene sentido que estén.
- `"name"` como segundo criterio es el desempate para proyectos con la misma fecha (o
  varios sin commits) — orden alfabético, previsible.

## Lo que el modelo *no* tiene

- **No hay campo de "rama actual" ni "dirty"**: esos datos son `GitStatus`, una
  dataclass de `services/git.py` que ni siquiera es un modelo Django. Vive y muere
  dentro de una respuesta HTTP.
- **No hay relación con otros modelos**: es el único modelo de la app, sin
  `ForeignKey` a nada. No hay usuarios, no hay multi-tenencia — la app asume un único
  usuario local.
- **No hay soft-delete**: `--prune` en `sync_projects` hace un `.delete()` real. Si un
  proyecto desaparece de disco y se prunea, su fila se pierde sin rastro (no hay
  papelera ni historial).

Ver también: [arquitectura](arquitectura.md) para el resto de capas, y
[flujos HTMX](flujos-htmx.md) para cómo se sirve el estado que no está aquí.
