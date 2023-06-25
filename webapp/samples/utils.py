from pathlib import Path


def get_health(path: Path):
    """Return last modified timestamp and contents of healthcheck file"""
    return path.stat().st_mtime, path.read_text()
