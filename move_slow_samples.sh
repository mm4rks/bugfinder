#!/bin/env bash

# Create ./data/slow_samples.txt by:
# python filter.py -i data/<commit_hash>.sqlite3 --slow 300 | tee -a data/slow_samples.txt
FILE_LIST="./data/slow_samples.txt"
DEST_DIR="./data/cold_storage/"

# Check if the destination directory exists, if not create it
if [ ! -d "$DEST_DIR" ]; then
    echo "ERROR: $DEST_DIR does not exist."
    exit 1
fi

# Loop through each line in the sample list 
# and move sample from ./infolder and ./data/samples to ./data/cold_storage
while IFS= read -r file; do
    mv "./infolder/$file" "$DEST_DIR"
    mv "./data/samples/$file" "$DEST_DIR"
done < "$FILE_LIST"
