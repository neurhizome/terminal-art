#!/usr/bin/env zsh
# Robust zsh bootstrap with TLS/cert sanity checks for Alpine/iSH
set -euo pipefail

MODE="${1:-auto}"
PY="${PYTHON:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"

echo "[asciiwaves] bootstrap (zsh) — mode=$MODE"

is_cmd() { command -v "$1" >/dev/null 2>&1 }

# --- Detect Alpine/iSH and prep certs ---
ALPINE=0
if is_cmd apk; then
  ALPINE=1
  echo "[asciiwaves] Alpine detected — ensuring certificates & openssl…"
  if [ "$(id -u)" -eq 0 ]; then
    apk add --no-cache ca-certificates openssl || true
    update-ca-certificates || true
  else
    echo "[asciiwaves] (info) not root; can't apk add. If TLS fails, run as root: 'apk add ca-certificates openssl && update-ca-certificates'"
  fi
fi

# --- Clock sanity (TLS requires correct time) ---
# If clock skew is large inside container, TLS can fail. We just display helpful info.
echo "[asciiwaves] system time: $(date -u) (UTC)"
# On iSH, if skewed, suggest: 'date -s "YYYY-MM-DD HH:MM:SS"' (requires root)

# --- Determine installer (uv preferred) ---
HAVE_UV=0
if is_cmd uv; then
  HAVE_UV=1
  echo "[asciiwaves] uv: $(uv --version)"
else
  if [ "${INSTALL_UV:-1}" -eq 1 ] && is_cmd curl; then
    echo "[asciiwaves] attempting to install uv…"
    (curl -LsSf https://astral.sh/uv/install.sh | sh) || true
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    if is_cmd uv; then HAVE_UV=1; echo "[asciiwaves] uv installed."; fi
  fi
fi

# --- Create venv ---
if [ $HAVE_UV -eq 1 ]; then
  echo "[asciiwaves] creating venv with uv → $VENV_DIR"
  uv venv "$VENV_DIR"
  source "$VENV_DIR/bin/activate"
  INSTALL_CMD=(uv pip install -r)
  # helpful env for uv
  export UV_HTTP_TIMEOUT=${UV_HTTP_TIMEOUT:-60}
  export UV_NO_INDEX_CACHE=1
else
  echo "[asciiwaves] creating venv with $PY -m venv → $VENV_DIR"
  "$PY" -m venv "$VENV_DIR"
  source "$VENV_DIR/bin/activate"
  python -m pip install --upgrade pip wheel setuptools
  INSTALL_CMD=(pip install -r)
fi

# --- TLS sanity env (helps requests/pip find certs) ---
if [ -f /etc/ssl/certs/ca-certificates.crt ]; then
  export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
  export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
fi

# Quick TLS probe to pypi (non-fatal)
python - <<'PY' || true
import ssl, socket
ctx = ssl.create_default_context()
try:
    with ctx.wrap_socket(socket.socket(), server_hostname="pypi.org") as s:
        s.settimeout(5)
        s.connect(("pypi.org", 443))
        print("[probe] TLS ok → pypi.org")
except Exception as e:
    print("[probe] TLS problem with pypi.org:", e)
PY

# --- Choose mode ---
if [ "$MODE" = "auto" ]; then
  if [ $ALPINE -eq 1 ]; then MODE="min"; else MODE="full"; fi
fi
echo "[asciiwaves] install mode: $MODE"

# --- Install requirements (with fallback and pip workarounds) ---
set +e
if [ "$MODE" = "full" ]; then
  echo "[asciiwaves] installing requirements-full.txt"
  "${INSTALL_CMD[@]}" requirements-full.txt
  STATUS=$?
  if [ $STATUS -ne 0 ]; then
    echo "[asciiwaves] full install failed — falling back to minimal."
    MODE="min"
  fi
fi
set -e

if [ "$MODE" = "min" ]; then
  echo "[asciiwaves] installing requirements-min.txt"
  # Try regular install
  if ! "${INSTALL_CMD[@]}" requirements-min.txt; then
    echo "[asciiwaves] minimal install failed — trying pip with trusted-host (TLS relax)"
    pip install --retries 0 --timeout 120 \
        --trusted-host pypi.org --trusted-host files.pythonhosted.org \
        -r requirements-min.txt || true
  fi
fi

# --- Environment report ---
if [ -f scripts/env_report.py ]; then
  python scripts/env_report.py || true
else
  python - <<'PY' || true
from importlib import metadata
print("\\nInstalled packages:")
for d in sorted(metadata.distributions(), key=lambda d: d.metadata['Name'].lower()):
    print(f"{d.metadata['Name']}=={d.version}")
PY
fi

echo
echo "[asciiwaves] bootstrap complete."
echo "  source $VENV_DIR/bin/activate"
echo "  python ascii_waves.py --rows 200 --style rounded --bg-set dots --color-scheme triad --blend oklab"
