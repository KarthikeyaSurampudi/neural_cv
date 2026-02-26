# Resume preprocessing utilities

import re


_BOILERPLATE = re.compile(
    r"(references\s+available\s+upon\s+request|curriculum\s+vitae|confidential\s+resume)",
    re.IGNORECASE,
)


def preprocess_resume_text(text: str, max_chars: int = 5000) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = _BOILERPLATE.sub("", text)

    if len(text) > max_chars:
        text = text[:max_chars]

    return text.strip()