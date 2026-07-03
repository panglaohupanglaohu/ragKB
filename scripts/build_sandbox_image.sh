#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_TAG="agentsgroup-sandbox:python3.11"
RUN_SELF_CHECK=0

for arg in "$@"; do
  case "$arg" in
    --self-check)
      RUN_SELF_CHECK=1
      ;;
    *)
      IMAGE_TAG="$arg"
      ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "docker executable not found" >&2
  exit 1
fi

docker build \
  -t "${IMAGE_TAG}" \
  -f "${ROOT_DIR}/docker/sandbox/Dockerfile" \
  "${ROOT_DIR}"

if [[ "${RUN_SELF_CHECK}" != "1" ]]; then
  exit 0
fi

docker run \
  --rm \
  --read-only \
  --tmpfs /tmp:size=32m,noexec,nosuid,nodev \
  --tmpfs /run:size=16m,noexec,nosuid,nodev \
  --network none \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --user 65534:65534 \
  -e HOME=/tmp \
  -e PYTHONUNBUFFERED=1 \
  "${IMAGE_TAG}" \
  python3 -c "print('sandbox-ok')"

docker run \
  --rm \
  --read-only \
  --tmpfs /tmp:size=32m,noexec,nosuid,nodev \
  --tmpfs /run:size=16m,noexec,nosuid,nodev \
  --network none \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --user 65534:65534 \
  -e HOME=/tmp \
  -e PYTHONUNBUFFERED=1 \
  -e PYTHONPATH=/workspace \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONNOUSERSITE=1 \
  -e PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  -v "${ROOT_DIR}:/workspace:ro" \
  -w /workspace \
  "${IMAGE_TAG}" \
  python3 -m pytest -q --tb=short --maxfail=1 -p no:cacheprovider src/backend/tests/test_sandbox_smoke.py
