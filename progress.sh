#!/bin/env bash

while [[ true ]]; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    free_mem=$(free -h | grep Mem | awk '{ print $3 }')
    infolder_count=$(ls ./infolder | wc -l)
    sqlite_size=$(ls -l -h data/samples.sqlite3 | awk '{ print $5 }')
    echo "${timestamp} - Mem: ${free_mem}, Infolder: ${infolder_count}, SQLite: ${sqlite_size}"
    sleep 60
done

