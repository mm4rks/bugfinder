#!/bin/env bash

origin="https://github.com/fkie-cad/dewolf.git"
dewolf_repo="$(pwd)/dewolf/repo"
image_name="bugfinder-dewolf"
dewolf_branch="main"

finish() {
    local result=$?
    echo "[+] exiting update with ${result}"
    exit ${result}
}
trap finish EXIT ERR

build_dewolf_image () {
    cp dewolf/license.txt "${dewolf_repo}"
    # curl --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" https://gitlab.fkie.fraunhofer.de/api/v4/projects/1250/repository/files/BinaryNinja.zip/raw?ref=main --output dewolf/BinaryNinja.zip
    cp dewolf/BinaryNinja.zip "${dewolf_repo}"
    pushd "${dewolf_repo}"
    sudo docker build -t ${image_name} .
    popd
}

update_dewolf () {
    pushd "${dewolf_repo}"
    git fetch --all 
    git checkout "${dewolf_branch}"
    git pull
    popd
    build_dewolf_image
}


# clone if repo does not exists
if [ ! -d "${dewolf_repo}" ]; then
    echo "[+] cloning dewolf into $(pwd)/${dewolf_repo}"
    git clone "${origin}" "${dewolf_repo}"
fi


echo "[+] building dewolf"
update_dewolf

docker system prune -f
