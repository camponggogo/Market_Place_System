#!/bin/sh
# If DOMAIN is set: use Certbot template, create dummy cert if needed, then start nginx.
# If DOMAIN is not set: use static nginx-default.conf (no HTTPS).

set -e
if [ -z "$DOMAIN" ]; then
  cp /etc/nginx/nginx-default.conf /etc/nginx/nginx.conf
  exec nginx -g "daemon off;"
fi

CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"
mkdir -p "$CERT_DIR"
if [ ! -f "${CERT_DIR}/fullchain.pem" ] || [ ! -f "${CERT_DIR}/privkey.pem" ]; then
  echo "No certs at ${CERT_DIR}; creating self-signed placeholder. Run certbot to get Let's Encrypt certs."
  openssl req -x509 -nodes -days 1 -newkey rsa:2048 \
    -keyout "${CERT_DIR}/privkey.pem" \
    -out "${CERT_DIR}/fullchain.pem" \
    -subj "/CN=${DOMAIN}"
fi

envsubst '${DOMAIN}' < /etc/nginx/templates/nginx.conf.template > /etc/nginx/nginx.conf
exec nginx -g "daemon off;"
