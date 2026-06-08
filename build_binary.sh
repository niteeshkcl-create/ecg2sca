#!/usr/bin/env bash
# -------------------------------------------------
# build_binary.sh – create a self‑contained ECG2SCA executable
# -------------------------------------------------
set -euo pipefail

# Ensure we are in a virtual environment that already has ECG2SCA installed
if [ -z "${VIRTUAL_ENV:-}" ]; then
    echo "[ERROR] Activate the ecg2sca_env virtual environment first."
    exit 1
fi

# Install PyInstaller if not present
if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "[INFO] Installing PyInstaller..."
    pip install --upgrade pyinstaller
fi

# Build the binary from the package's entry point
pyinstaller --onefile -n ecg2sca ecg2sca/__main__.py

echo "[OK] Binary created at ./dist/ecg2sca"
