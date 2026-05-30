#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_TAG="${1:-agentsgroup-sandbox:python3.11}"

docker build \
  -t "${IMAGE_TAG}" \
  -f "${ROOT_DIR}/docker/sandbox/Dockerfile" \
  "${ROOT_DIR}"
