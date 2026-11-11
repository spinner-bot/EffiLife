"""Fingerprint all production files, including separately served frame assets."""
from pathlib import Path
import hashlib

def frontend_fingerprint(directory: Path) -> str:
    result = hashlib.sha256()
    for path in sorted(directory.rglob('*')):
        if not path.is_file() or path.relative_to(directory).parts[0] == 'examples':
            continue
        file_hash = hashlib.sha256()
        with path.open('rb') as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                file_hash.update(chunk)
        result.update(path.relative_to(directory).as_posix().encode() + b'\0' + file_hash.digest())
    return result.hexdigest()
