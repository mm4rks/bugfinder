#!/bin/env bash

infolder=./infolder
max_size=50000000
image_name="bugfinder-dewolf"
max_workers=12
max_time=600


if [ "${EUID}" -ne 0 ]; then 
  echo "Please run as root (for running docker commands)"
  exit 1
fi

# lock infolder/.gitignore
chattr +i ${infolder}/.gitignore

get_timestamp () {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo ${timestamp}
}

docker_stop_image () {
    # stop all containers for $image_name
    echo "[+] INFO stop containers for ${image_name}..."
    local container_ids=$(docker ps -q --filter ancestor="${image_name}")
    if [[ -z "${container_ids}" ]]; then
        echo "[+] INFO no containers running for image: ${image_name}"
    else
        docker stop ${container_ids}
    fi
}

finish() {
    local result=$?
    echo "[+] - $(get_timestamp) - exit worker.sh"
    docker_stop_image ${image_name}
    exit ${result}
}
trap finish EXIT ERR


filter_sample_file () {
    local file=$1
    local size=$(wc -c < "${file}")
    if (( ${size} > ${max_size} )); then
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

run_task () {
    # docker run task in background
    local sample_hash=$1
    local command="python decompiler/util/bugfinder/bugfinder.py /data/samples/${sample_hash} --sqlite-file /data/samples.sqlite3"
    docker run -d --mount type=bind,source="$(pwd)/data",target=/data \
        ${image_name} timeout ${max_time} ${command}
}

set -o pipefail

while [[ true ]]; do
    for f in $(find ${infolder} -maxdepth 1 -type f ! -name '.gitignore'); do
        echo "[+] - $(get_timestamp) - processing $f"
        if filter_sample_file $f; then
            continue # file was filtered
        fi
        hash=$(sha256sum $f | awk '{ print $1 }')
        status=$?
        if [[ ${status} -ne 0 ]]; then
            echo "[-] ERROR: hashing failed (${status})"
            exit 1
        fi
        echo "[+] - $(get_timestamp) - sample hash: ${hash}"
        mv "${f}" "./data/samples/${hash}"

        # Wait for a free worker to process the sample
        running_containers=$(sudo docker ps --filter ancestor="${image_name}" -q | wc -l)
        while [ ${running_containers} -ge ${max_workers} ]; do
          sleep 1
          running_containers=$(sudo docker ps --filter ancestor="${image_name}" -q | wc -l)
        done
        # Start a new worker/container
        echo "[+] - $(get_timestamp) - starting worker"
        run_task ${hash}
        sleep 1
    done
    sleep 1
done