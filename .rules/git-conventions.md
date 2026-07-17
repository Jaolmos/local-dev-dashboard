# Convenciones de Git

## Conventional commits

Formato: `tipo: descripción`

- **Tipo en inglés**, uno de: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`, `perf`.
- **Descripción en español**, en imperativo y minúscula: `feat: añadir estado git diferido vía htmx`.
- Cuerpo opcional en español para el "por qué" cuando el cambio no es obvio.
- **Nunca** incluir el trailer `Co-Authored-By`.

Ejemplos:

```
feat: añadir modal de readme y acción abrir en vscode
fix: manejar repositorios sin rama upstream
chore: ignorar config local de claude y ficheros privados
docs: documentar arquitectura por capas
```

## Reglas

- Commits pequeños y con una intención clara (una capa/feature por commit cuando sea posible).
- No commitear: `.env`, `db.sqlite3`, `.venv/`, CSS compilado, config local de Claude, `.private/`.
- Trabajar en `main` para este proyecto local está bien; ramas si se quiere aislar algo grande.
