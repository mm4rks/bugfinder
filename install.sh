#!/bin/env bash

DEWOLF_REPO=./dewolf/repo

set -o pipefail
set -o errexit

display_help() {
    echo "Usage: install.sh [function]"
    echo "Functions:"
    echo "  dev : fetch dewolf and build images (development)"
    echo "  dev : fetch dewolf and build images (production)"
}

error() {
    local result=$?
    # cleanup
    echo "[-] ERROR"
    exit ${result}
}
trap error ERR

setup_dewolf_repo () {
    echo "[+] setup dewolf repo"
    if [ ! -d "$DEWOLF_REPO" ]; then
        echo "cloning into $(pwd)/${DEWOLF_REPO}"
        git clone https://github.com/fkie-cad/dewolf.git $DEWOLF_REPO
    fi
	pushd $DEWOLF_REPO
	git fetch --all 
	# TODO change to main
	git checkout issue-179-_Stability_create_tooling_to_find_minimal_crashing_examples_on_corpus_of_test_binaries
	git pull
	popd
}

dev() {
    echo "[+] building images"
    setup_dewolf_repo
	sudo docker compose build
	sudo docker compose run web python manage.py makemigrations
	sudo docker compose run web python manage.py migrate
}

prod() {
    local secret=$(cat /dev/urandom | tr -dc '[:print:]' | head -c 60)
    echo "[+] create env file"
    tee .env.prod <<EOF
DJANGO_DEBUG=False
SECRET_KEY=${secret}
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
EOF

    echo "[+] building images for PRODUCTION"
    setup_dewolf_repo
	sudo docker compose -f docker-compose.prod.yml build
	sudo docker compose -f docker-compose.prod.yml run web python manage.py makemigrations
	sudo docker compose -f docker-compose.prod.yml run web python manage.py migrate
}


# Check the number of arguments
if [[ $# -eq 0 ]]; then
    display_help
    exit 0
fi

# Execute the specified function
case "$1" in
    dev)
        dev
        ;;
    prod)
        prod
        ;;
    *)
        echo "Invalid function: $1"
        display_help
        exit 1
        ;;
esac
