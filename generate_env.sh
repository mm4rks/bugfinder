#!/bin/env bash

cert_file="${CERT_FILE:-/etc/ssl/certs/sr-se-bugfinder.pem}"
cert_key="${CERT_KEY:-/etc/ssl/private/sr-se-bugfinder.pem}"
allowed_hosts=bugfinder.seclab-bonn.de
env_file=".env.prod"

if [[ -e "${env_file}" ]]; then
    read -p "The file ${env_file} already exists. Overwrite? [Y/n]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ ! -z $REPLY ]]; then
        echo "File not overwritten. Exiting..."
        exit 0
    fi
fi

secret=$(cat /dev/urandom | tr -dc '[:alnum:]' | head -c 70)
echo "[+] writing ${env_file}"
tee ${env_file} <<EOF
DJANGO_DEBUG=False
SECRET_KEY='${secret}'
DJANGO_ALLOWED_HOSTS=${allowed_hosts}
CERT_FILE=${cert_file}
CERT_KEY=${cert_key}
UID=$(id -u)
GID=$(id -g)
EOF
