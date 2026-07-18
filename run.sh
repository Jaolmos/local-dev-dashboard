#!/usr/bin/env bash
# Arranca el dashboard en el puerto configurado (segunda instancia local).
# Puerto: argumento CLI > DASHBOARD_PORT del .env > 8765 por defecto.
set -euo pipefail

# Situarse en la raíz del repo para que funcione desde cualquier directorio.
cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
    echo "No existe .env. Cópialo primero:  cp .env.example .env" >&2
    exit 1
fi

# Se lee solo la variable concreta (no 'source .env') para no romper con
# caracteres raros de DJANGO_SECRET_KEY.
# El '|| true' evita que 'set -e' aborte si la variable no está en el .env.
PORT="${1:-$(grep -E '^DASHBOARD_PORT=' .env | cut -d= -f2 || true)}"
PORT="${PORT:-8765}"

# Compilar el CSS antes de servir: garantiza que la página sale con estilos
# en el primer arranque. Para desarrollo con CSS en vivo, usar 'tailwind runserver'.
uv run python manage.py tailwind build

echo "Dashboard en http://127.0.0.1:${PORT}/"
uv run python manage.py runserver "127.0.0.1:${PORT}"
