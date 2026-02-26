# Resume text extraction utilities

# processing/resume_text_extractor.py

from pathlib import Path
from typing import Union

import PyPDF2
from docx import Document


def extract_text(file_path: Union[str, Path]) -> str:
    path = Path(file_path)

    if path.suffix.lower() == ".pdf":
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join(page.extract_text() or "" for page in reader.pages)

    if path.suffix.lower() == ".docx":
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)

    return path.read_text(encoding="utf-8", errors="ignore")