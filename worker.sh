#!/bin/env bash

infolder=./infolder
max_size=90000
image_name="bugfinder-dewolf"
dewolf_repo="$(pwd)/dewolf/repo"
dewolf_branch="main"
max_workers=8
max_time=600

# globals for rate limiting GitHub queries
last_commit_check=0
rate_limit_duration=600


if [ "${EUID}" -ne 0 ]; then 
  echo "Please run as root (for running docker commands)"
  exit 1
fi

get_timestamp () {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo ${timestamp}
}

docker_stop_image () {
    # stop all containers for $image_name
    echo "[+] stopping containers for ${image_name}..."
    local container_ids=$(docker ps -q --filter ancestor="${image_name}")
    if [[ -z "${container_ids}" ]]; then
        echo "[+] no containers running for image: ${image_name}"
    else
        docker stop ${container_ids}
    fi
}

docker_wait_image () {
    echo "[+] wait for running containers..."
    local container_ids=$(docker ps -q --filter ancestor="${image_name}")

    if [[ -z "${container_ids}" ]]; then
        echo "[+] no containers running for image: ${image_name}"
        return
    fi

    echo "[+] waiting for containers:"
    for container_id in $container_ids; do
        if docker ps -q | grep -q "^${container_id}$"; then
            echo "    - Waiting for container: ${container_id}"
            docker wait "${container_id}"
        else
            echo "    - No such container: ${container_id}"
        fi
    done    
}

finish() {
    local result=$?
    echo "[+] - $(get_timestamp) - exiting worker.sh with ${result}"
    docker_stop_image ${image_name}
    exit ${result}
}
trap finish EXIT ERR


filter_sample_file () {
    local file=$1
    # local size=$(wc -c < "${file}")
    # if (( ${size} > ${max_size} )); then
    #     echo "[-] file too big (${size} bytes)"
    #     rm ${file}
    #     return 0
    # fi

    local file_info=$(file ${file})
    if ! echo "${file_info}" | grep -q -E "ELF|Mach-O|PE32|COFF|DOS exe|COM exe"; then
        echo "[-] file type not allowed: ${file_info}"
        rm "${file}"
        return 0
    fi
    return 1 # file was not filtered
}

run_task () {
    # docker run task in background
    local sample_hash=$1
    local command="python decompiler/util/bugfinder/bugfinder.py /data/samples/${sample_hash} --sqlite-file /data/samples.sqlite3"
    docker run --rm --detach --mount type=bind,source="$(pwd)/data",target=/data \
        ${image_name} timeout ${max_time} ${command}
}

refill_infolder () {
    # save relevant samples (linked on webapp)
    # move samples to infolder for processing
    echo "[+] refilling infolder and copying relevant samples cold storage..."
    if [ -f "data/filtered.sqlite3" ]; then
        source "$(pwd)/.venv/bin/activate"
        for i in $(python filter.py -i data/filtered.sqlite3 --list); do 
            cp -n data/samples/$i data/cold_storage 2> /dev/null
        done
        deactivate
    fi
    rmdir ${infolder} && mv data/samples ${infolder}
    mkdir -p data/samples
}

queue_sample_by_hash () {
    # add a sample by hash to the worker pool
    local sample_hash=$1

    # Wait for a free worker to process the sample
    local running_containers=$(sudo docker ps --filter ancestor="${image_name}" -q | wc -l)
    while [ ${running_containers} -ge ${max_workers} ]; do
      sleep 1
      running_containers=$(sudo docker ps --filter ancestor="${image_name}" -q | wc -l)
    done
    # Start a new worker/container
    echo "[+] $(get_timestamp) - starting worker container"
    run_task ${sample_hash}
}

update_db () {
    local tag=$1
    echo "[*] updating filtered.sqlite3 (${tag})..."
    # does samples.sqlite3 exists?
    if [ ! -f "data/samples.sqlite3" ]; then
        echo "[*] update_db (${tag}) - no samples.sqlite, nothing to do."
        return
    fi
    echo "[*] getting current commit..."
    pushd "${dewolf_repo}"
    git checkout "${dewolf_branch}"
    local current_commit="$(git rev-parse HEAD)"
    popd
    # backup filtered.sqlite3
    if [ -f "data/filtered.sqlite3" ]; then
        echo "[+] backing up filtered.sqlite3"
        cp data/filtered.sqlite3 data/filtered.sqlite3.bak
    fi
    echo "[+] filtering and rotating samples.sqlite3"
    source "$(pwd)/.venv/bin/activate"
    python filter.py -i data/samples.sqlite3 -o data/filtered.sqlite3 --tag ${tag}
    deactivate
    mv --backup=numbered data/samples.sqlite3 data/"${tag}_${current_commit}.sqlite3"
}


quick_run () {
    # process crashing samples from last commit
    # samples must be in infolder and will be moved to data/samples
    echo "[+] starting quick run..."
    if [ ! -f "data/filtered.sqlite3" ]; then
        echo "[-] no filtered.sqlite3 found. Make sure to init database."
        return
    fi
    local last_processed_commit=$(sqlite3 data/filtered.sqlite3 "SELECT dewolf_current_commit FROM summary ORDER BY id DESC LIMIT 1;") 
    source "$(pwd)/.venv/bin/activate"
    python filter.py -i data/filtered.sqlite3 --list --commit ${last_processed_commit} > "./data/quick_run"
    deactivate
    total_files=$(wc -l "./data/quick_run" | awk '{print $1}')
    processed_files=0
    echo "[+] samples to process in quick run: ${total_files} (infolder: $(ls ${infolder} | wc -l))"
    echo "${processed_files}/${total_files}" > data/quick_run.progress
    while IFS= read -r file; do
        if [ ! -f "${infolder}/${file}" ]; then
            # already processed, or missing
            continue
        fi
        mv "${infolder}/${file}" "./data/samples/${file}"
        queue_sample_by_hash ${file}
        ((processed_files++))
        echo "${processed_files}/${total_files}" > data/quick_run.progress
        echo "quick run containers:" > data/healthcheck.txt
        docker ps >> data/healthcheck.txt
    done < "./data/quick_run"
    docker_wait_image
    echo "quick run containers:" > data/healthcheck.txt
    docker ps >> data/healthcheck.txt
    if [ "$processed_files" -ne 0 ]; then
        # quickrun did process files
        echo "[*] finalizing quick run"
        update_db "quick"
    else
        echo "[*] quickrun did already ran?"
    fi
}

clear_infolder () {
    # move files from infolder to data/samples
    # filter, and name by sha256
    echo "[+] clearing infolder..."
    mkdir -p ${infolder}
    for f in $(find ${infolder} -maxdepth 1 -type f ! -name '.gitignore'); do
        echo "[+] clear - $(get_timestamp) - file: ${f}"
        if filter_sample_file $f; then
            continue # file was filtered
        fi
        hash=$(sha256sum $f | awk '{ print $1 }')
        status=$?
        if [[ ${status} -ne 0 ]]; then
            echo "[-] ERROR: hashing failed (${status})"
            exit 1
        fi
        mv "${f}" "./data/samples/${hash}"
    done
}

check_new_commit() {
    echo "[+] checking new commit..."
    local current_time=$(date +%s)
    local time_diff=$((current_time - last_commit_check))

    if [ ${time_diff} -lt ${rate_limit_duration} ]; then
        echo "[+] Skipping commit check due to rate limiting"
        return 0
    fi

    last_commit_check=${current_time}
    touch data/idle # indicate last check for new dewolf commit

    pushd "${dewolf_repo}"
    git checkout "${dewolf_branch}"
    git fetch
    local current_commit="$(git rev-parse HEAD)"
    local upstream_commit=$(git rev-parse "${dewolf_branch}"@{upstream})
    popd

    if [ "${current_commit}" != "${upstream_commit}" ]; then
        echo "[+] New commit found in upstream"
        return 1  # Return a non-zero status to indicate a new commit
    else
        echo "[+] No new commit in upstream"
        return 0
    fi
}

long_run () {
    # process all remaining files in infolder
    # perform renaming and filtering
    echo "[+] starting long run..."
    total_files=$(ls "${infolder}" | wc -l)
    processed_files=0
    echo "[+] samples to process in long run: ${total_files}"
    echo "${processed_files}/${total_files}" > data/long_run.progress
    for file in $(find ${infolder} -maxdepth 1 -type f ! -name '.gitignore'); do
        check_new_commit
        if [ $? -eq 1 ]; then
            echo "[+] Breaking long run due to new commit in upstream"
            break
        fi
        echo "[+] long run - $(get_timestamp) - filename: ${file}"
        if filter_sample_file $file; then
            continue # file was filtered
        fi
        hash=$(sha256sum $file | awk '{ print $1 }')
        status=$?
        if [[ ${status} -ne 0 ]]; then
            echo "[-] ERROR: hashing failed (${status})"
            exit 1
        fi
        mv "${file}" "./data/samples/${hash}"
        queue_sample_by_hash ${hash}
        ((processed_files++))
        echo "${processed_files}/${total_files}" > data/long_run.progress
        echo "long run containers:" > data/healthcheck.txt
        docker ps >> data/healthcheck.txt
    done
    docker_wait_image
    echo "long run containers:" > data/healthcheck.txt
    docker ps >> data/healthcheck.txt
    clear_infolder
    update_db "long"
}

init_new_run () {
    # get local and remote commits
    echo "[+] checking upstream commit..."
    pushd "${dewolf_repo}"
    git checkout "${dewolf_branch}"
    git fetch
    local current_commit="$(git rev-parse HEAD)"
    local upstream_commit=$(git rev-parse "${dewolf_branch}"@{upstream})
    popd
    touch data/idle # indicate last check for new dewolf commit
    
    # update and refill queue if new version
    if [ "${current_commit}" != "${upstream_commit}" ]; then
        echo "[+] updating dewolf"
        ./update_dewolf.sh
        # check if update worked
        pushd "${dewolf_repo}"
        new_commit="$(git rev-parse HEAD)"
        popd
        if [ "${upstream_commit}" != "${new_commit}" ]; then
            echo "[-] updating dewolf failed!"
            exit 1
        fi
        clear_infolder
        refill_infolder
    else
        echo "[+] no new dewolf version" 
    fi
}

set -o pipefail

while [[ true ]]; do
    quick_run
    long_run
    init_new_run

    echo "[+] sleeping for ${rate_limit_duration}..."
    sleep ${rate_limit_duration}
done
