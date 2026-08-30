"""Pure parsing primitives for the managed Express heartbeat auth seam.

This module deliberately has no database or legacy-agent dependency.  It only
turns the Companion bearer token into the two values a managed lookup needs.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import re
from typing import Optional
from uuid import UUID

_TOKEN_PREFIX = "exp_"
_MAX_TOKEN_LENGTH = 1024
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_SECRET_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ManagedAgentToken:
    """The non-sensitive identity extracted from a Companion token."""

    endpoint_id: str
    token_digest: str


def parse_managed_agent_token(token: str) -> Optional[ManagedAgentToken]:
    """Parse exactly ``exp_<canonical-uuid>_<secret>`` without exposing secret."""
    if not isinstance(token, str) or not token or len(token) > _MAX_TOKEN_LENGTH:
        return None
    if not token.startswith(_TOKEN_PREFIX):
        return None
    parts = token.split("_", 2)
    if len(parts) != 3 or parts[0] != "exp" or not parts[2]:
        return None
    endpoint_id = parts[1]
    if not _UUID_RE.fullmatch(endpoint_id):
        return None
    try:
        parsed_uuid = UUID(endpoint_id)
    except ValueError:
        return None
    if str(parsed_uuid) != endpoint_id.lower() or not _SECRET_RE.fullmatch(parts[2]):
        return None
    return ManagedAgentToken(
        endpoint_id=str(parsed_uuid),
        token_digest=hashlib.sha256(token.encode("utf-8")).hexdigest(),
    )


def stored_token_matches(stored_hash: str, token_digest: str) -> bool:
    """Compare fixed-format SHA-256 hex digests without a timing shortcut."""
    if not isinstance(stored_hash, str) or not isinstance(token_digest, str):
        return False
    if not _DIGEST_RE.fullmatch(stored_hash) or not _DIGEST_RE.fullmatch(token_digest):
        return False
    return hmac.compare_digest(stored_hash, token_digest)


__all__ = ["ManagedAgentToken", "parse_managed_agent_token", "stored_token_matches"]
