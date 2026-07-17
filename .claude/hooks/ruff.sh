#!/usr/bin/env bash
# Hook PostToolUse: formatea y auto-corrige con ruff el fichero .py editado.
# No bloqueante: siempre termina con exit 0 (no interrumpe el flujo).
set -uo pipefail

input=$(cat)
file_path=$(printf '%s' "$input" | python3 -c \
  "import sys, json; print(json.load(sys.stdin).get('tool_input', {}).get('file_path', ''))" \
  2>/dev/null)

# Solo ficheros Python existentes.
[[ "$file_path" == *.py && -f "$file_path" ]] || exit 0

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

uv run ruff check --fix -q "$file_path" 2>/dev/null || true
uv run ruff format -q "$file_path" 2>/dev/null || true

exit 0
