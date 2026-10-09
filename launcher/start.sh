#!/bin/bash
cd "$(dirname "$0")/.."
if [ -n "${EFFILIFE_PYTHON:-}" ]; then
  if [ ! -x "$EFFILIFE_PYTHON" ]; then
    echo "EFFILIFE_PYTHON is not executable: $EFFILIFE_PYTHON" >&2
    exit 127
  fi
  PYTHON_BIN="$EFFILIFE_PYTHON"
else
  if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys' >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1 && python -c 'import sys' >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "EffiLife requires a usable python3 or python interpreter" >&2
    exit 127
  fi
fi
exec "$PYTHON_BIN" launcher/start.py --unified "$@"
