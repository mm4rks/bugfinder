# BugFinder

**BugFinder** is a tool designed to detect crashes in the [dewolf decompiler](https://github.com/fkie-cad/dewolf) project. It runs `bugfinder.py` from the dewolf project on a set of binary samples, grouping detected crashes by exception types and traceback. Notably, it highlights the minimal crashing samples, i.e., the functions with the fewest basic blocks. Minimal crashes are accessible via the web interface. Corresponding issues can be opened directly on the dewolf GitHub repository by integrating with the GitHub API.

**Data Store:** Processed binaries are archived in the `data/samples` directory and can be accessed through the web application. Samples to be processed are stored in the `infolder/` directory. After a complete run, i.e., `infolder/` is empty, the `infolder/` will be populated with processed samples from `data/samples` again.
Binary samples that should not be part of this iteration but still be available through web download are stored in `data/cold_storage`.

## 🛠 Requirements

Before getting started with BugFinder, ensure your system meets the following prerequisites:

- Docker Compose
- Python 
- Pandas library

## 🚀 Getting Started

For easy installation, use `make install PROD=1`. This will:

- Build the dewolf image 
- Build web containers
- Register `systemd` services.

Start worker and web services via:

```bash
sudo systemctl start bugfinder_worker
sudo systemctl start bugfinder_web
```

### Worker

The `worker.sh` bash script processes the binary samples from `infolder/` by starting multiple dewolf docker images. Decompilation results are stored in `data/samples.sqlite3`. For each complete run, this SQLite file is rotated to `data/<dewolf-commit-hash>.sqlite3`, and its filtered contents are appended to `data/filtered.sqlite3`.

The worker script is started by the `bugfinder_worker` service.

### Web Interface

The web interface displays content from `filtered.sqlite3`. To increase performance, make sure this SQLite file has the correct indexes by:

```bash
sqlite3 data/filtered.sqlite3
sqlite> 
       CREATE INDEX idx_dewolf_errors_is_successful ON dewolf_errors(is_successful);
       CREATE INDEX idx_dewolf_errors_dewolf_current_commit ON dewolf_errors(dewolf_current_commit);
       CREATE INDEX idx_dewolf_errors_case_group ON dewolf_errors(case_group);
       CREATE INDEX idx_dewolf_function_basic_block_count ON dewolf_errors(function_basic_block_count);
```

### Data Filtering

Execute the Python script to curate the data showcased on the web application. The worker script automatically does this after each iteration of sample processing.

```bash
python filter.py -i data/samples.sqlite3 -o data/filtered.sqlite3
```

### GitHub API

To allow BugFinder to create issues on the official dewolf repository, provide an API token in the `.env.prod` file, like:

```
GITHUB_TOKEN=your-token-here
GITHUB_REPO_OWNER="fkie-cad"
GITHUB_REPO_NAME="dewolf"
```

## 📦 Utilities

The script `apt_downloader.sh` offers a utility for downloading ELF binary files from the Ubuntu APT repository.
This tool fetches Debian packages and extracts the embedded ELF files. To keep track of the processed files, it records the last processed line number in a progress file. All extracted files are saved in the `infolder/` directory.

_Progress logging_ can be done with the `progress.sh` script. This periodically prints the number of files within `infolder/`, memory usage, and size of `data/samples.sqlite3`. When invoking this script with

```bash
./progress.sh | tee -a data/progress.log
```

the currect stats are displayed on the web interface dashboard.
