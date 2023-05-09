#!/bin/env bash

while [[ true ]]; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    free_mem=$(free -h | grep Mem | awk '{ print $3 }')
    infolder_count=$(ls ./infolder | wc -l)
    sqlite_bytes=$(wc -c ./data/samples.sqlite3)
    echo "${timestamp} - Mem: ${free_mem}, Infolder: ${infolder_count}, SQLite: ${sqlite_bytes}"
    sleep 60
done

