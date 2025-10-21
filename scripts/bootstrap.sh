#!/usr/bin/env bash
# Bootstrap a virtual environment for asciiwaves.
# Usage:
#   ./bootstrap.sh            # auto: full on glibc, minimal on Alpine/iSH
#   ./bootstrap.sh full       # force full
#   ./bootstrap.sh min        # force minimal
# Env:
#   INSTALL_UV=0              # skip trying to install uv if missing
#   PYTHON=python3            # override python interpreter
set -euo pipefail

MODE="${1:-auto}"
PY="${PYTHON:-python3}"
VENV_DIR=".venv"

echo "[asciiwaves] bootstrap starting (mode=$MODE)"

# Detect Alpine (iSH typically)
if command -v apk >/dev/null 2>&1; then
  ALPINE=1
  echo "[asciiwaves] Alpine detected"
  # Essentials for building some wheels & terminal capabilities
  sudo apk add --no-cache python3 py3-pip build-base libffi-dev musl-dev ncurses openssl-dev || true
else
  ALPINE=0
fi

# Try uv
if command -v uv >/dev/null 2>&1; then
  HAVE_UV=1
  echo "[asciiwaves] uv found: $(uv --version)"
else
  HAVE_UV=0
  if [ "${INSTALL_UV:-1}" -eq 1 ]; then
    echo "[asciiwaves] attempting uv install (optional)…"
    if command -v curl >/dev/null 2>&1; then
      (curl -LsSf https://astral.sh/uv/install.sh | sh) || true
      export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
      if command -v uv >/dev/null 2>&1; then HAVE_UV=1; fi
    else
      echo "[asciiwaves] curl not available; skipping uv install"
    fi
  fi
fi

# Create venv
if [ "$HAVE_UV" -eq 1 ]; then
  echo "[asciiwaves] creating venv with uv"
  uv venv "$VENV_DIR"
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  INSTALL_CMD="uv pip install -r"
else
  echo "[asciiwaves] creating venv with $PY -m venv"
  "$PY" -m venv "$VENV_DIR"
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  python -m pip install --upgrade pip wheel setuptools
  INSTALL_CMD="pip install -r"
fi

# Decide mode
if [ "$MODE" = "auto" ]; then
  if [ "$ALPINE" -eq 1 ]; then MODE="min"; else MODE="full"; fi
fi
echo "[asciiwaves] install mode resolved to: $MODE"

# Install
set +e
if [ "$MODE" = "full" ]; then
  echo "[asciiwaves] installing requirements-full.txt"
  $INSTALL_CMD requirements-full.txt
  STATUS=$?
  if [ $STATUS -ne 0 ]; then
    echo "[asciiwaves] full install failed (likely heavy wheels). Falling back to minimal."
    MODE="min"
  fi
fi
set -e

if [ "$MODE" = "min" ]; then
  echo "[asciiwaves] installing requirements-min.txt"
  $INSTALL_CMD requirements-min.txt
fi

# Write an env report
python scripts/env_report.py

echo
echo "[asciiwaves] done. Activate with:"
echo "  source .venv/bin/activate"
echo "Run a demo:"
echo "  python ascii_waves.py --rows 200 --style heavy --bg-set dots --color-scheme triad --blend oklab"
