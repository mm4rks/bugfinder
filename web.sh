#!/bin/env bash

# Check the number of arguments
if [[ $# -eq 0 ]]; then
    echo "./processor.sh [dev|prod]"
    exit 0
fi

case "$1" in
    dev)
        echo "[+] running in development"
        ;;
    prod)
        echo "[+] running in production"
        compose_opt="-f docker-compose.prod.yml --env-file .env.prod"
        ;;
    *)
        echo "Invalid option: $1"
        display_help
        exit 1
        ;;
esac

# finish() {
#     local result=$?
#     echo
#     echo "[+] exit"
#     docker compose ${compose_opt} down
#     exit ${result}
# }
# trap finish EXIT ERR

docker compose ${compose_opt} up web -d
docker compose ${compose_opt} up nginx -d
