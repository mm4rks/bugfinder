#!/bin/env bash

DEWOLF_REPO=$(pwd)/dewolf/repo
image_name="bugfinder-dewolf"
dewolf_branch="issue-241-_Bugfinder_Log_total_function_count_of_binary_sample"

read -p "Update dewolf? [Y/n]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ ! -z $REPLY ]]; then
    echo "skipping update dewolf"
    exit 0
fi

echo "[+] setup dewolf repo"
if [ ! -d "$DEWOLF_REPO" ]; then
    echo "cloning into $(pwd)/${DEWOLF_REPO}"
    git clone https://github.com/fkie-cad/dewolf.git $DEWOLF_REPO
fi
pushd $DEWOLF_REPO
git fetch --all 
git checkout ${dewolf_branch}
git pull
popd

read -p "Build dewolf image? [Y/n]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ ! -z $REPLY ]]; then
    echo "skipping building of dewolf docker image"
    exit 0
fi

cp dewolf/license.txt ${DEWOLF_REPO}
cp dewolf/BinaryNinja.zip ${DEWOLF_REPO}
pushd $DEWOLF_REPO
sudo docker build -t ${image_name} .
popd

