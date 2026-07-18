# Admin de Django

La app expone el admin estándar de Django en `/admin/` (ruta registrada en
`config/urls.py`). Es la vía manual para inspeccionar y editar el catálogo sin pasar por
`sync_projects` — útil para depurar, corregir un dato puntual o borrar una fila fantasma.

## Crear un superusuario

Hace falta un usuario con permisos para entrar. Se crea con el comando de Django:

```bash
uv run python manage.py createsuperuser
```

Pide usuario, email (opcional) y contraseña. Los usuarios viven en la misma base de datos
SQLite que el catálogo (`db.sqlite3`), así que basta con haber corrido `migrate` antes.

Luego, con el servidor arrancado (`uv run python manage.py runserver`), entra en
<http://127.0.0.1:8000/admin/> y accede con esas credenciales.

## Qué se puede hacer desde el admin

El `ProjectAdmin` (`apps/projects/admin.py`) está configurado así:

- **Listado** con `name`, `path`, `description` y `last_synced` a la vista.
- **Búsqueda** por `name`, `path` y `description` (caja de búsqueda arriba).
- **Solo lectura**: `created_at` y `last_synced` no se pueden editar a mano (los pone
  Django solo).

Desde ahí puedes crear, editar o borrar proyectos del catálogo directamente.

## Ojo: el admin escribe en el catálogo, `sync_projects` manda

`sync_projects` usa `path` como clave de `update_or_create`. Consecuencias de tocar cosas
a mano:

- Si **editas un dato** (nombre, descripción, stack) desde el admin, el siguiente
  `sync_projects` lo **sobrescribe** con lo que haya en disco. Los cambios manuales solo
  duran hasta la próxima sincronización.
- Si **borras** un proyecto desde el admin pero la carpeta sigue en disco, el siguiente
  `sync_projects` lo **vuelve a crear**.
- El único cambio manual que "sobrevive" es borrar la fila de un proyecto que ya no está
  en disco — que es justo lo que hace `sync_projects --prune` de forma automática.

En la práctica: el admin es para mirar y para arreglos puntuales, no una segunda fuente de
verdad. La fuente real del catálogo es el escaneo de `PROJECTS_ROOT`.

Ver también: [modelo de datos](modelo-datos.md) para qué significa cada campo, y
[arquitectura](arquitectura.md) para por qué `sync_projects` es el único que escribe por
diseño.
