#!/bin/env bash

origin="https://github.com/fkie-cad/dewolf.git"
dewolf_repo="$(pwd)/dewolf/repo"
image_name="bugfinder-dewolf"
dewolf_branch="main"
auto_mode=false

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


if [[ $* == *-y* ]]; then
    echo "Automatic mode: Skipping confirmation prompts"
    auto_mode=true
fi


if [ "${auto_mode}" = false ] ; then
    read -p "Update dewolf? [Y/n]: " -n 1 -r
    if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ ! -z $REPLY ]]; then
        echo
        echo "[-] skip building dewolf"
        exit 0
    fi
    echo
fi


if [ ! -d "${dewolf_repo}" ]; then
    echo "[+] cloning dewolf into $(pwd)/${dewolf_repo}"
    git clone "${origin}" "${dewolf_repo}"
fi

if [[ $* == *-b* ]]; then
    echo "Build dewolf image"
    build_dewolf_image
fi

pushd "${dewolf_repo}"
git checkout "${dewolf_branch}"
git fetch
current_commit="$(git rev-parse HEAD)"
if [ "${current_commit}" == $(git rev-parse "${dewolf_branch}"@{upstream}) ]; then
    echo "[+] already on recent commit"
    exit 0
fi
popd

if [ -f "data/samples.sqlite3" ]; then
    if [ -f "data/filtered.sqlite3" ]; then
        cp data/filtered.sqlite3 data/filtered.sqlite3.bak
    fi
    echo "[+] filtering and moving samples.sqlite3"
    source "$(pwd)/.venv/bin/activate"
    python filter.py -i data/samples.sqlite3 -o data/filtered.sqlite3
    deactivate
    mv data/samples.sqlite3 data/"${current_commit}.sqlite3"
else
    echo "[-] samples.sqlite3 does not exist..."
    exit 1
fi


# save relevant samples (linked on webapp)
# move samples to infolder for processing
if [ -f "data/filtered.sqlite3" ]; then
    source "$(pwd)/.venv/bin/activate"
    mkdir -p data/relevant_samples
    for i in $(python filter.py -i data/filtered.sqlite3 --list); do 
        cp data/samples/$i data/relevant_samples
    done
    deactivate
    rmdir infolder && mv data/samples infolder && mv data/relevant_samples data/samples
fi

echo "[+] building dewolf"
update_dewolf

docker system prune -f
