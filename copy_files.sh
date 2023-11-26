#!/bin/env bash


# Define source and destination directories
SOURCE_DIR="./data/windows_samples/examples"
DEST_DIR="./data/win7"

# Check if source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Source directory does not exist."
    exit 1
fi

# Check if destination directory exists, create if not
if [ ! -d "$DEST_DIR" ]; then
    echo "creating ${DEST_DIR}"
    mkdir -p "$DEST_DIR"
fi


# Copy and rename files
for file in $(find "$SOURCE_DIR" -type f); do
    # Calculate SHA256 hash of the file
    file_hash=$(sha256sum "$file" | awk '{print $1}')

    # Copy the file to the destination directory with the hash as its name
    cp "$file" "$DEST_DIR/$file_hash"
done
