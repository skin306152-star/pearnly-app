"""Validate image evidence and save it atomically with the count receipt."""

import base64
import binascii
import hashlib
import warnings
from io import BytesIO

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError

from services.stocktake import store

MAX_BYTES = 1024 * 1024


def prepare(values):
    if len(values) > 5:
        raise HTTPException(422, detail="stocktake.photo_limit")
    result = []
    for value in values:
        try:
            if len(value) > 1400000:
                raise ValueError()
            raw = base64.b64decode(value, validate=True)
            if not raw or len(raw) > MAX_BYTES:
                raise ValueError()
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(BytesIO(raw)) as source:
                    if source.width * source.height > 16000000:
                        raise ValueError()
                    image = ImageOps.exif_transpose(source).convert("RGB")
                    image.thumbnail((1600, 1600))
                    output = BytesIO()
                    image.save(output, "JPEG", quality=85, optimize=True)
            content = output.getvalue()
            if len(content) > MAX_BYTES:
                raise ValueError()
        except (
            ValueError,
            binascii.Error,
            OSError,
            SyntaxError,
            UnidentifiedImageError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ):
            raise HTTPException(422, detail="stocktake.photo_invalid") from None
        result.append((content, hashlib.sha256(raw).hexdigest()))
    return result


def save(cur, scope, entry_id, images):
    if not images:
        return
    cur.execute(
        "SELECT COUNT(*) AS n FROM cowork_stocktake_photos WHERE entry_id=%s "
        "AND tenant_id=%s AND workspace_client_id=%s",
        (str(entry_id), scope.tenant_id, scope.workspace_client_id),
    )
    count = cur.fetchone()["n"]
    if count + len(images) > 5:
        raise HTTPException(422, detail="stocktake.photo_limit")
    for slot, (content, digest) in enumerate(images, count + 1):
        cur.execute(
            "INSERT INTO cowork_stocktake_photos "
            "(entry_id,tenant_id,workspace_client_id,slot,content,digest,created_by) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (
                str(entry_id),
                scope.tenant_id,
                scope.workspace_client_id,
                slot,
                content,
                digest,
                scope.user_id,
            ),
        )


def listing(scope, task_id, entry_id):
    with store.cursor(scope) as cur:
        store._task(cur, scope, task_id)
        cur.execute(
            "SELECT id FROM cowork_stocktake_entries WHERE id=%s AND stocktake_id=%s "
            "AND tenant_id=%s AND workspace_client_id=%s",
            (str(entry_id), str(task_id), scope.tenant_id, scope.workspace_client_id),
        )
        if not cur.fetchone():
            raise HTTPException(404, detail="stocktake.not_found")
        cur.execute(
            "SELECT slot,content FROM cowork_stocktake_photos WHERE entry_id=%s "
            "AND tenant_id=%s AND workspace_client_id=%s ORDER BY slot",
            (str(entry_id), scope.tenant_id, scope.workspace_client_id),
        )
        return {
            "photos": [
                {"slot": r["slot"], "data": base64.b64encode(bytes(r["content"])).decode("ascii")}
                for r in cur.fetchall()
            ]
        }


def export(cur, scope, task_id):
    cur.execute(
        "SELECT COALESCE(SUM(octet_length(p.content)),0) AS size "
        "FROM cowork_stocktake_photos p JOIN cowork_stocktake_entries e ON e.id=p.entry_id "
        "WHERE e.stocktake_id=%s AND p.tenant_id=%s AND p.workspace_client_id=%s",
        (str(task_id), scope.tenant_id, scope.workspace_client_id),
    )
    if cur.fetchone()["size"] > 80 * MAX_BYTES:
        raise HTTPException(413, detail="stocktake.photo_export_too_large")
    cur.execute(
        "SELECT p.entry_id,p.slot,p.content FROM cowork_stocktake_photos p "
        "JOIN cowork_stocktake_entries e ON e.id=p.entry_id "
        "WHERE e.stocktake_id=%s AND p.tenant_id=%s AND p.workspace_client_id=%s "
        "ORDER BY p.entry_id,p.slot",
        (str(task_id), scope.tenant_id, scope.workspace_client_id),
    )
    return [dict(row, content=bytes(row["content"])) for row in cur.fetchall()]
