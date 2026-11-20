#!/bin/bash
# ==============================================================================
# Pocket Mechanic - macOS Desktop Application Launcher
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

export PATH="/Library/Frameworks/Python.framework/Versions/3.11/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

PYTHON_EXEC=""
for candidate in "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3" "/usr/local/bin/python3" "/opt/homebrew/bin/python3" "$(which python3 2>/dev/null)"; do
  if [ -x "$candidate" ] && "$candidate" -c "import webview" >/dev/null 2>&1; then
    PYTHON_EXEC="$candidate"
    break
  fi
done

if [ -z "$PYTHON_EXEC" ]; then
  echo "Error: Python with pywebview not found."
  exit 1
fi

echo "Checking local MySQL service..."
if ! nc -z 127.0.0.1 3306 2>/dev/null; then
  echo "Starting local MySQL via Homebrew..."
  brew services start mysql 2>/dev/null || true
  sleep 1
fi

echo "Starting Pocket Mechanic Native Desktop App with $PYTHON_EXEC..."
exec "$PYTHON_EXEC" desktop/desktop_main.py "$@"
