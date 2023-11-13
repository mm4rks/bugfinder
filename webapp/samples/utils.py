import hashlib
import os
import zipfile
from pathlib import Path
from typing import Tuple, Union


def unzip_flat(zip_file_path, target_dir, pwd=None):
    """Extract zipfile content files into target directory, without preserving folder structure"""
    if isinstance(pwd, str):
        pwd = pwd.encode("utf-8")
    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        for zip_info in zip_ref.infolist():
            if zip_info.is_dir():
                continue
            zip_info.filename = os.path.basename(zip_info.filename)
            zip_ref.extract(zip_info, target_dir, pwd=pwd)


def get_file_last_modified_and_content(path: Path):
    """Return last modified timestamp and contents of healthcheck file"""
    if not path.exists():
        return 0, f"'{path}' does not exist"
    return path.stat().st_mtime, path.read_text()

def get_progress(path: Path) -> Tuple[int, int]:
    """Parse file contents of the form 'processed/total'."""
    if not path.exists():
        return 0, -1
    a, b = path.read_text().split("/")
    return int(a), int(b)


def get_last_line(path: Path):
    """Return last line, if file exists"""
    if not path.exists():
        return 0, f"'{path}' does not exist"
    return path.read_text().splitlines()[-1]


def is_hex(value):
    """Fast check if hex for small strings (<100)"""
    try:
        int(value, 16)
        return True
    except ValueError:
        return False


def sha256sum(file_path: Union[str, Path]) -> str:
    # https://stackoverflow.com/questions/22058048/hashing-a-file-in-python
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with open(file_path, "rb", buffering=0) as f:
        while n := f.readinto(mv):
            h.update(mv[:n])
    return h.hexdigest()
