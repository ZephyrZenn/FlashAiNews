#!/bin/sh
set -eu

TEMPLATE_PATH="/etc/nginx/conf.d/default.conf"
TMP_PATH="${TEMPLATE_PATH}.tmp"

# Provide a sensible default when no environment variable is passed at runtime.
: "${BACKEND_URL:=http://backend:8000}"

echo "Configuring nginx proxy to use BACKEND_URL=${BACKEND_URL}" >&2

envsubst '${BACKEND_URL}' < "${TEMPLATE_PATH}" > "${TMP_PATH}"
mv "${TMP_PATH}" "${TEMPLATE_PATH}"
