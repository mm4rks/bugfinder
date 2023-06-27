from pathlib import Path


def get_file_last_modified_and_content(path: Path):
    """Return last modified timestamp and contents of healthcheck file"""
    if not path.exists():
        return 0, f"'{path}' does not exist"
    return path.stat().st_mtime, path.read_text()

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

