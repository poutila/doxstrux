import re


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[\s\t\n]+", "-", text)
    return re.sub(r"[^\w\-]", "", text)
