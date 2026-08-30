# -*- coding: utf-8 -*-
"""Stable, non-reversible identity for one Express account directory."""

from __future__ import annotations

import hashlib
import ntpath
import re

_KEY_VERSION = "v1"
_DRIVE_ABSOLUTE = re.compile(r"^[a-zA-Z]:\\")
_RESERVED_COMPONENT = re.compile(r"^(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?$", re.I)
_INVALID_PATH_CHARS = frozenset('<>"|?*')
_MAX_ACCOUNT_SET = 120
_MAX_ACCOUNT_DIR = 1024


def _clean_account_set(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("account_set must be a string")
    cleaned = value.strip()
    if not cleaned or len(cleaned) > _MAX_ACCOUNT_SET:
        raise ValueError("account_set is empty or too long")
    if any(ord(char) < 32 for char in cleaned):
        raise ValueError("account_set contains a control character")
    return cleaned.casefold()


def _clean_windows_path(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("account_dir must be a string")
    raw = value.replace("/", "\\")
    if not raw or len(raw) > _MAX_ACCOUNT_DIR:
        raise ValueError("account_dir is empty or too long")
    if raw != raw.strip():
        raise ValueError("account_dir has surrounding whitespace")
    if any(ord(char) < 32 for char in raw):
        raise ValueError("account_dir contains a control character")
    if raw.startswith(("\\\\?\\", "\\\\.\\")):
        raise ValueError("device namespace paths are not supported")

    parts = raw.split("\\")
    if any(part in (".", "..") for part in parts):
        raise ValueError("account_dir contains an ambiguous segment")
    for part in parts:
        if not part or part.endswith((".", " ")) or part.endswith(":"):
            continue
        if _RESERVED_COMPONENT.fullmatch(part):
            raise ValueError("account_dir contains a reserved Windows component")
    if any(part.endswith((".", " ")) for part in parts if part):
        raise ValueError("account_dir contains an invalid Windows component")
    tail = raw[2:] if _DRIVE_ABSOLUTE.match(raw) else raw
    if any(char in _INVALID_PATH_CHARS or char == ":" for char in tail):
        raise ValueError("account_dir contains an invalid Windows path character")

    normalized = ntpath.normcase(ntpath.normpath(raw))
    if _DRIVE_ABSOLUTE.match(normalized):
        if normalized == normalized[:2] + "\\":
            raise ValueError("a drive root is not an Express profile")
        return normalized
    if normalized.startswith("\\\\"):
        unc_parts = [part for part in normalized[2:].split("\\") if part]
        if len(unc_parts) < 2:
            raise ValueError("UNC paths require a server and share")
        return normalized
    raise ValueError("account_dir must be an absolute drive or UNC path")


def profile_key(account_set: object, account_dir: object) -> str:
    """Return an opaque versioned key; the normalized path never leaves this module."""
    account = _clean_account_set(account_set)
    path = _clean_windows_path(account_dir)
    payload = f"{_KEY_VERSION}\0{account}\0{path}".encode("utf-8")
    return f"{_KEY_VERSION}:{hashlib.sha256(payload).hexdigest()}"


__all__ = ["profile_key"]
