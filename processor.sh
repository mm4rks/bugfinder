#!/bin/env bash

INFOLDER=./infolder
MAX_SIZE=50000000
DEWOLF_CONTAINER_NAME=dewolf_container

if [ "${EUID}" -ne 0 ]; then 
  echo "Please run as root (for running docker commands)"
  exit 1
fi

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
        compose_opt="-f docker-compose.prod.yml"
        ;;
    *)
        echo "Invalid option: $1"
        display_help
        exit 1
        ;;
esac

finish() {
    local result=$?
    echo
    echo "[+] exit"
    docker compose ${compose_opt} down
    exit ${result}
}
trap finish EXIT ERR

# lock infolder/.gitignore
chattr +i $INFOLDER/.gitignore


docker compose ${compose_opt} up -d
sleep 5

filter () {
    local file=$1
    local size=$(wc -c < "${file}")
    if (( ${size} > $MAX_SIZE )); then
        echo "[-] file too big (${size} bytes)"
        rm ${file}
        return 0
    fi

    local file_info=$(file ${file})
    if ! echo "${file_info}" | grep -q -E "ELF|Mach-O|PE32|COFF|DOS exe|COM exe"; then
        echo "[-] file type not allowed: ${file_info}"
        rm ${file}
        return 0
    fi

    return 1 # file was not filtered
}

set -o pipefail

while [[ true ]]; do
    for f in $(find $INFOLDER -maxdepth 1 -type f ! -name '.gitignore')
    do
        echo "[+] processing $f"
        if filter $f; then
            continue # file was filtered
        fi
        hash=$(sha256sum $f | awk '{ print $1 }')
        status=$?
        if [[ ${status} -ne 0 ]]; then
            echo "[-] ERROR: hashing failed (${status})"
            continue
        fi
        mv "${f}" "./data/samples/${hash}"
        docker exec ${DEWOLF_CONTAINER_NAME} python decompiler/util/bugfinder/bugfinder.py /data/samples/${hash} --sqlite-file /data/samples.sqlite3
        status=$?
        if [[ $status -ne 0 ]]; then
            echo "[-] ERROR: dewolf failed (${hash})"
            continue
        fi
    done
    sleep 1
done
