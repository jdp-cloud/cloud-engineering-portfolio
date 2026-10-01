#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(
  cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
  pwd
)"

LAB_DIR="$(
  cd -- "${SCRIPT_DIR}/.."
  pwd
)"

REQUIREMENTS_FILE="${LAB_DIR}/layers/reportlab/requirements.txt"
BUILD_ROOT="${TMPDIR:-/tmp}/lab-12b-reportlab-layer"
PYTHON_DIR="${BUILD_ROOT}/python"
OUTPUT_ZIP="${LAB_DIR}/terraform/reportlab-python312-x86_64.zip"

for required_command in python3 zip; do
  if ! command -v "${required_command}" >/dev/null 2>&1; then
    echo "ERROR: Required command not found: ${required_command}" >&2
    exit 1
  fi
done

if [[ ! -f "${REQUIREMENTS_FILE}" ]]; then
  echo "ERROR: Requirements file not found: ${REQUIREMENTS_FILE}" >&2
  exit 1
fi

echo "Building ReportLab Lambda layer"
echo "Target runtime:      Python 3.12"
echo "Target architecture: x86_64"
echo "Target platform:     manylinux2014_x86_64"
echo "Requirements:        ${REQUIREMENTS_FILE}"
echo "Output:              ${OUTPUT_ZIP}"
echo

mkdir -p "${BUILD_ROOT}"
find "${BUILD_ROOT}" -mindepth 1 -delete
mkdir -p "${PYTHON_DIR}"

python3 -m pip install \
  --disable-pip-version-check \
  --no-compile \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.12 \
  --only-binary=:all: \
  --requirement "${REQUIREMENTS_FILE}" \
  --target "${PYTHON_DIR}"

find "${PYTHON_DIR}" \
  -type d \
  -name '__pycache__' \
  -prune \
  -exec rm -rf {} +

find "${PYTHON_DIR}" \
  -type f \
  \( -name '*.pyc' -o -name '*.pyo' \) \
  -delete

rm -f "${OUTPUT_ZIP}"

(
  cd "${BUILD_ROOT}"
  zip -q -r "${OUTPUT_ZIP}" python
)

python3 - "${OUTPUT_ZIP}" <<'PY'
from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

archive = Path(sys.argv[1])

required_entries = {
    "python/reportlab/__init__.py",
}

with zipfile.ZipFile(archive) as layer_zip:
    names = set(layer_zip.namelist())

missing = sorted(required_entries - names)

if missing:
    print("ERROR: Layer archive is missing required entries:")
    for entry in missing:
        print(f"  {entry}")
    raise SystemExit(1)

digest = hashlib.sha256(archive.read_bytes()).hexdigest()

print()
print("PASS: ReportLab layer archive created.")
print(f"Archive: {archive}")
print(f"Size:    {archive.stat().st_size} bytes")
print(f"SHA256:  {digest}")
print("Root:    python/")
PY
