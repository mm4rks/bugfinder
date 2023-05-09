#!/bin/env bash

DEWOLF_REPO=$(pwd)/dewolf/repo

# systemd service unit files
worker_service_content="[Unit]
Description=Bugfinder dewolf worker
StartLimitIntervalSec=30
StartLimitBurst=2

[Service]
ExecStart=$(pwd)/worker.sh
WorkingDirectory=$(pwd)
Restart=on-failure
User=root

[Install]
WantedBy=multi-user.target"

web_service_content="[Unit]
Description=Bugfinder webapp
After=network.target
StartLimitIntervalSec=30
StartLimitBurst=2

[Service]
ExecStart=$(pwd)/web.sh
WorkingDirectory=$(pwd)
Restart=on-failure

[Install]
WantedBy=multi-user.target"

install_service () {
    echo "$worker_service_content" | sudo tee "/etc/systemd/system/bugfinder_worker.service" > /dev/null
    # echo "$web_service_content" | sudo tee "/etc/systemd/system/bugfinder_web.service" > /dev/null
    sudo systemctl daemon-reload
    sudo systemctl enable "bugfinder_worker"
    sudo systemctl start "bugfinder_worker"
    sudo systemctl status "bugfinder_worker"
    # sudo systemctl enable "bugfinder_web"
    # sudo systemctl start "bugfinder_web"
    # sudo systemctl status "bugfinder_web"
}


set -o pipefail
set -o errexit

display_help() {
    echo "Usage: install.sh [function]"
    echo "Functions:"
    echo "  dev : fetch dewolf and build images (development)"
    echo " prod : fetch dewolf and build images (production)"
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
    cp dewolf/license.txt ${DEWOLF_REPO}
    cp dewolf/BinaryNinja.zip ${DEWOLF_REPO}
}

dev() {
    echo "[+] building images"
    setup_dewolf_repo
	sudo docker compose build
	sudo docker compose run web python manage.py makemigrations
	sudo docker compose run web python manage.py migrate
}

prod() {
    ./generate_env.sh
    setup_dewolf_repo
    echo "[+] building images for PRODUCTION"
	sudo docker compose -f docker-compose.prod.yml --env-file .env.prod build
	sudo docker compose -f docker-compose.prod.yml --env-file .env.prod run web python manage.py makemigrations
	sudo docker compose -f docker-compose.prod.yml --env-file .env.prod run web python manage.py migrate
	sudo docker compose -f docker-compose.prod.yml --env-file .env.prod run web python manage.py collectstatic
    echo "[+] install services"
    install_service
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
