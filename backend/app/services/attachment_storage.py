"""
Filesystem storage for case attachments.

Files are written to `settings.UPLOAD_DIR` (a mounted Docker volume) with a
UUID name to avoid collisions and path-traversal. The DB row keeps the mapping
to the original filename.
"""
from __future__ import annotations

import os
import uuid

from app.config import settings


def _ext_for_mime(mime: str) -> str:
    return {
        "application/pdf": ".pdf",
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/webp": ".webp",
    }.get(mime, "")


def ensure_upload_dir() -> str:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    return settings.UPLOAD_DIR


def save_bytes(data: bytes, mime_type: str) -> str:
    """Persist bytes under a fresh UUID filename; return the stored filename."""
    ensure_upload_dir()
    stored = f"{uuid.uuid4().hex}{_ext_for_mime(mime_type)}"
    path = os.path.join(settings.UPLOAD_DIR, stored)
    with open(path, "wb") as f:
        f.write(data)
    return stored


def read_bytes(stored_filename: str) -> bytes:
    # Defensive: never let a crafted stored_filename escape the upload dir.
    safe = os.path.basename(stored_filename)
    path = os.path.join(settings.UPLOAD_DIR, safe)
    with open(path, "rb") as f:
        return f.read()


def delete_file(stored_filename: str) -> None:
    safe = os.path.basename(stored_filename)
    path = os.path.join(settings.UPLOAD_DIR, safe)
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def full_path(stored_filename: str) -> str:
    return os.path.join(settings.UPLOAD_DIR, os.path.basename(stored_filename))
