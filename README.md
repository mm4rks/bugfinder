# bugfinder

The bugfinder project is a tool designed to find crashes in the dewolf decompiler project.
It achieves this by utilizing the 'bugfinder.py' (located in the dewolf project) on a large corpus of sample binaries.
The tool identifies crashes and groups them by exception type. Additionally, it identifies the minimal crashing samples, which are functions with the fewest basic blocks.

The bugfinder project incorporates a web application built with Django, where the grouped crashes and minimal crashing samples are displayed.
The tool relies on the Makefile for simplified execution of common tasks.

Processed binaries are stored in `data/samples` and can be downloaded with the web app.


## Requirements

To use the bugfinder project, ensure that you have the following dependencies installed:

- Docker Compose
- Python and pandas

## Usage Instructions

The project provides several targets in the Makefile to facilitate usage:

- Start the web application in the specified environment (development or production).
  - Dev: `make`
  - Production: `make PROD=1`

- **install**: Set up the project for the specified environment, including directory and file creation, migrations, and static file collection. It optionally installs a worker service.
  - Default: `make install`
  - Production: `make install PROD=1`

- **filter**: Execute a Python script to filter data to be displayed by the web application. Requires the input database (`data/samples.sqlite3`) created by the `worker.sh` script.
  - Command: `make filter`

To start the decompilation worker, execute `./worker.sh`. The worker will monitor `infolder/` for binaries and process them.

If the worker service is registered in systemd, use:

```bash
sudo systemctl start bugfinder_worker
```

## Utilities

The bugfinder project includes an utility to download ELF files, implemented in the `apt_downloader.sh` bash script. This utility downloads Debian packages and extracts ELF files from them.
It maintains progress by tracking the last processed line number in a progress file. The extracted files are saved in the specified `infolder` directory.
