#!/bin/sh
# Container entrypoint: apply migrations, seed the catalogue, then serve.
# Kept as a script because platforms that override the container command
# mangle a multi-command shell string.
set -e

python -m app.cli init

exec python -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --proxy-headers \
  --forwarded-allow-ips='*'
