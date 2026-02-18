#!/bin/sh
set -eu

envsubst '$WLP_SERVER_NAME $WLP_API_SERVER_NAME $WLP_WEB_UPSTREAM $WLP_API_UPSTREAM $WLP_SSL_CERT_PATH $WLP_SSL_KEY_PATH' \
  < /etc/nginx/templates/nginx.conf.template \
  > /etc/nginx/nginx.conf

exec nginx -g 'daemon off;'
