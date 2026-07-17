# Testing

`pytest` + `pytest-django`. Config en `pyproject.toml` (`[tool.pytest.ini_options]`,
`DJANGO_SETTINGS_MODULE = "config.settings"`, `testpaths = ["apps"]`).

## Estructura

- Tests por app en `apps/<app>/tests/`, un fichero por área: `test_discovery.py`, `test_git.py`,
  `test_stack.py`, `test_readme.py`, `test_views.py`.
- Nombres descriptivos: `test_<qué>_<condición>_<resultado>`.

## Enfoque

- **Services**: son el núcleo, priorizar su cobertura. Para `discovery`/`stack`/`readme` crear
  directorios temporales (`tmp_path`) con ficheros marcadores y README de ejemplo.
- **git**: inicializar un repo real en `tmp_path` (`git init`, commits) o mockear `subprocess`.
  Cubrir: repo limpio, dirty, sin remoto, carpeta sin `.git`.
- **Vistas**: usar el `client` de Django/pytest. Marcar con `@pytest.mark.django_db` lo que toque BD.
  Verificar status y que se devuelve el **partial** correcto.
- Acciones con efectos del SO (abrir VSCode): mockear `subprocess` — nunca lanzar procesos reales.

## Ejecutar

```bash
uv run pytest -x -v
uv run pytest apps/projects/tests/test_git.py
```
