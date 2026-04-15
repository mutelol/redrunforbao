from __future__ import annotations

import base64
import html
import re
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse, urlsplit, urlunsplit


def absolute_url(base: str, value: str) -> str:
    return urljoin(base, value)


def clean_text(value: str) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*", "\n", text)
    return text.strip()


def collapse_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:40] or "item"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def guess_extension_from_url(url: str) -> str:
    path = urlparse(url).path.lower()
    if path.endswith(".png"):
        return ".png"
    if path.endswith(".webp"):
        return ".webp"
    if path.endswith(".jpeg"):
        return ".jpeg"
    return ".jpg"


def mime_type_from_extension(ext: str) -> str:
    ext = ext.lower()
    if ext == ".png":
        return "image/png"
    if ext == ".webp":
        return "image/webp"
    return "image/jpeg"


def as_data_uri(image_bytes: bytes, mime_type: str) -> str:
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def normalized_request_url(url: str) -> str:
    split = urlsplit(url)
    path = quote(split.path, safe="/%._-~")
    query = quote(split.query, safe="=&?/%._-~")
    return urlunsplit((split.scheme, split.netloc, path, query, split.fragment))
