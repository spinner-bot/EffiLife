#!/bin/bash
cd "$(dirname "$0")/.."
if [ -n "${EFFILIFE_PYTHON:-}" ]; then
  if [ ! -x "$EFFILIFE_PYTHON" ]; then
    echo "EFFILIFE_PYTHON is not executable: $EFFILIFE_PYTHON" >&2
    exit 127
  fi
  PYTHON_BIN="$EFFILIFE_PYTHON"
else
  PYTHON_BIN="python3"
fi
exec "$PYTHON_BIN" launcher/start.py --unified "$@"
