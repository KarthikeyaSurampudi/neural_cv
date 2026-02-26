# Hash utilities

import hashlib
from pathlib import Path
from typing import List


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def hash_file(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def hash_resume_set(paths: List[Path]) -> str:
    combined = ""
    for p in sorted(paths, key=lambda x: x.name):
        combined += hash_file(p)
    return hashlib.sha256(combined.encode()).hexdigest()