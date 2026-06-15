#!/bin/sh
set -eu

envsubst '${API_URL} ${APP_ENV}' \
  < /etc/nginx/templates/config.template.js \
  > /usr/share/nginx/html/config.js
