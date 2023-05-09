#!/bin/env bash

infolder=$(pwd)/infolder
tmp=/tmp/aptdownloader
workdir=${tmp}/workdir

set -o pipefail

progress_file="$(pwd)/data/last_package.txt"
package_list="$(pwd)/data/package_list.txt"
touch ${progress_file}
last_line_number=$(head -n 1 ${progress_file})
current_line_number=${last_line_number:-1}

mkdir -p ${workdir}

if [[ ! -f ${package_list} ]]; then
    echo "[+] create package list"
    apt-cache search . | awk -F" - " '{print $1}' > ${package_list}
    echo "[+] done"
fi

extract_package () {
    local package_name=$1
    pushd ${workdir}
    local status=$?
    if [[ ${status} -ne 0 ]]; then
        echo "[-] ERROR: moving to ${workdir}"
        exit ${status}
    fi
    rm -rf *
    mkdir -p extracted
    apt-get download $package
    for debfile in $(ls *.deb); do
        rm -rf extracted/*
        dpkg-deb -x ${debfile} extracted/
        for elf in $(find extracted/ -exec file {} \; | grep -Po ".*(?i)(?=: elf)")
        do
            cp ${elf} ${infolder}/
        done
        rm ${debfile}
    done
    popd
}

for package in $(awk "NR>${current_line_number}" ${package_list}); do
    echo "[+] ${package}"
    extract_package ${package}
    current_line_number=$((current_line_number+1))
    echo ${current_line_number} > ${progress_file}
done
