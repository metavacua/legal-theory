"""Convert a Markdown document to validated, XSLT-buildable DocBook 5.2 XML."""

import re
from pathlib import Path


def slugify(text):
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    if not text:
        return "s"
    if re.match(r"^[0-9]", text):
        text = f"s-{text}"
    return text


def extract_title(md_path):
    with open(md_path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^#{1,6}\s+(.*)", line)
            if m:
                return re.sub(r"[*_]", "", m.group(1)).strip()
    return Path(md_path).stem.replace("-", " ").replace("_", " ").title()
