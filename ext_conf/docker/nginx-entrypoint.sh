#!/bin/sh
set -eu

if [ ! -f "${WLP_SSL_CERT_PATH}" ] || [ ! -f "${WLP_SSL_KEY_PATH}" ]; then
  echo "[nginx-entrypoint] TLS cert or key not found at configured paths. Generating temporary self-signed cert."

  if ! command -v openssl >/dev/null 2>&1; then
    apk add --no-cache openssl >/dev/null
  fi

  TMP_CERT_DIR="/tmp/wlp-certs"
  TMP_CERT_PATH="${TMP_CERT_DIR}/localhost.crt"
  TMP_KEY_PATH="${TMP_CERT_DIR}/localhost.key"

  mkdir -p "${TMP_CERT_DIR}"

  openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
    -keyout "${TMP_KEY_PATH}" \
    -out "${TMP_CERT_PATH}" \
    -subj "/CN=${WLP_SERVER_NAME:-localhost}" \
    -addext "subjectAltName=DNS:${WLP_SERVER_NAME:-localhost},DNS:${WLP_API_SERVER_NAME:-api.localhost},DNS:localhost,DNS:api.localhost"

  chmod 600 "${TMP_KEY_PATH}"

  export WLP_SSL_CERT_PATH="${TMP_CERT_PATH}"
  export WLP_SSL_KEY_PATH="${TMP_KEY_PATH}"
fi

envsubst '$WLP_SERVER_NAME $WLP_API_SERVER_NAME $WLP_WEB_UPSTREAM $WLP_API_UPSTREAM $WLP_SSL_CERT_PATH $WLP_SSL_KEY_PATH' \
  < /etc/nginx/templates/nginx.conf.template \
  > /etc/nginx/nginx.conf

exec nginx -g 'daemon off;'
