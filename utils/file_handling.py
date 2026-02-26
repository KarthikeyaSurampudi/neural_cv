# File handling utilities

# utils/file_handling.py

from pathlib import Path
from typing import List

from core.constants import SUPPORTED_EXTENSIONS, MAX_FILE_SIZE_MB


def scan_resume_folder(folder_path: str) -> List[Path]:
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(f"{folder_path} not found")

    files = []

    for file in folder.iterdir():
        if not file.is_file():
            continue

        if file.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        size_mb = file.stat().st_size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            continue

        files.append(file)

    return files