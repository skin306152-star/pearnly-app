# -*- coding: utf-8 -*-
"""管家会话附件:限额 + 落盘 + steward_attachments 行 DAL(万能口 F1 的存储层)。

为什么另起一张表:
  ocr_history 是【识别结果】表(一行一张票)——把没识别的工资表/流水塞进去,识别记录页、
  管家 history_query、防重单钥匙、purge_files 四处语义一起被污染;
  work_order_items 是【会计业务对象】——store.py 顶注已写死「任务不复用工单」的同一条理由:
  随手扔进对话的一份表,不该在事务所矩阵里变成一张真月度工单。

只新建「表」,不新建「存储原语」:安全词干 / 租户前缀 / 原名反解全部借 workorder.storage 的
纯函数(复制两份必漂 —— _STEM_UNSAFE 里「保留泰文」那条漏抄一次,泰文文件名就整个变下划线),
加密白拿 core.file_crypto 的 maybe_seal/unseal 双轨读;sha256 一律算【明文】—— 与
ocr.entrypoints.content_hash 同口径,F2 接识别时能直接命中 get_cached_history 的零成本复用。

生命周期:对话里扔的文件是临时件不是业务档案,expires_at 默认 30 天,到期由
sweep_expired 收(挂 background_loops.run_recovery_tick)。先收集 → 删行 → 提交后删盘,
照 workspace/purge_files 的三段式:行没了就再也定位不到文件。
"""

from __future__ import annotations

import json
import logging
import mimetypes
import os
import uuid
from pathlib import Path
from typing import Any, Optional

from core import file_crypto
from services.ocr.entrypoints import SUPPORTED_OCR_EXTENSIONS, content_hash

# 私有名跨模块借用是有意的:这几个是纯函数,复制一份两边必漂(sort.py 借 bank_recon_utils
# 的 _BANK_SIGNATURES 是同一先例)。提到共用位置留给动 workorder/** 的那条线收口。
from services.workorder.storage import _safe_stem, _tenant_short, original_name_of

logger = logging.getLogger(__name__)

_BASE = os.environ.get("STEWARD_STORAGE_DIR", "/opt/mrpilot/storage/steward")
_NAME_SEP = "__"

# 上限:与收料口同口径(routes/workorder_routes 单件 20MB),单批再收一道总量闸。
# 20 而不是 50 件的理由:对话里的进度条看不了 50 条,且 50 份 manifest 会把 planner 的
# _MAX_UTTERANCE 预算撑爆。单一事实源在这里 —— 前端从 /status 读,不各硬编码一份。
MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_BATCH_BYTES = 35 * 1024 * 1024
MAX_FILES_PER_MESSAGE = 20

_DEFAULT_TTL_DAYS = 30

STATUS_READY = "ready"
STATUS_PROMOTED = "promoted"
# 工具产出的文件(转换出来的 xlsx 等)也落这张表:同一份加密/防穿越/租户隔离/到期清理白拿,
# 而且下一轮能被当成料继续用(「把刚才转出来的这张表推进去」)。status 分开是为了让附件盘
# 只显示人自己传的那些 —— 送出前的 chips 不该冒出一个系统产物。
STATUS_ARTIFACT = "artifact"

# kind_source:rule = 确定性判据认出来的;unknown = 判不准(必须问,不许猜)。
SOURCE_RULE = "rule"
SOURCE_UNKNOWN = "unknown"

_COLUMNS = (
    "id, tenant_id, session_id, message_id, user_id, original_name, file_ref, size_bytes, "
    "sha256, mime, kind, kind_source, kind_reason, detect, status, promoted_to, "
    "created_at, expires_at"
)


def ttl_days() -> int:
    try:
        value = int(os.environ.get("STEWARD_ATTACHMENT_TTL_DAYS", "") or _DEFAULT_TTL_DAYS)
    except ValueError:
        value = _DEFAULT_TTL_DAYS
    return max(1, value)


def limits() -> dict[str, Any]:
    """前端读的限额契约(GET /status 里带出去)。超限在【选文件的当下】就拒,不传完再拒。"""
    return {
        "max_file_bytes": MAX_FILE_BYTES,
        "max_batch_bytes": MAX_BATCH_BYTES,
        "max_files": MAX_FILES_PER_MESSAGE,
        "accept": sorted(SUPPORTED_OCR_EXTENSIONS),
        "ttl_days": ttl_days(),
    }


# ── 落盘 ────────────────────────────────────────────────────


def session_dir(tenant_id: str, session_id: str) -> Path:
    return Path(_BASE) / _tenant_short(tenant_id) / str(session_id)


def save(content: bytes, *, tenant_id: str, session_id: str, original_name: str) -> Path:
    """字节落到该会话目录,返回绝对路径。名 = {uuid}__{安全词干}{ext}(uuid 保唯一不可猜,
    原名内嵌留底);写盘前过 maybe_seal —— 开了 FILE_ENC_MODE 即落密文,关了逐字节同今天。"""
    stem = _safe_stem(original_name)
    ext = Path(original_name or "").suffix.lower()
    if not (2 <= len(ext) <= 6):
        ext = ".bin"
    dest = session_dir(tenant_id, session_id)
    dest.mkdir(parents=True, exist_ok=True)
    base = f"{uuid.uuid4().hex}{_NAME_SEP}{stem}" if stem else uuid.uuid4().hex
    path = dest / f"{base}{ext}"
    path.write_bytes(file_crypto.maybe_seal(content))
    return path


def read_content(file_ref: str) -> bytes:
    """取盘统一出口:读盘 + 双轨解密(密文解回明文,存量明文原样返)。"""
    return file_crypto.unseal(Path(file_ref).read_bytes())


def resolve_within_session(tenant_id: str, session_id: str, file_ref: str) -> Optional[Path]:
    """第二道防线:库里登记过的路径也要断言仍落在本会话目录之下(防路径穿越)。"""
    if not file_ref:
        return None
    root = session_dir(tenant_id, session_id).resolve()
    try:
        target = Path(file_ref).resolve()
    except (OSError, ValueError):
        return None
    if root not in target.parents and target != root:
        return None
    return target if target.is_file() else None


def remove_file(file_ref: str) -> None:
    """尽力而为删一件(登记失败回滚 / 到期清理)。删不掉只 warning:留个不被引用的小文件,
    比把已落定的行为报成失败好。"""
    try:
        Path(file_ref).unlink(missing_ok=True)
    except OSError:
        logger.warning("[steward.attachments] remove failed for %s", file_ref)


def guess_mime(original_name: str) -> str:
    return mimetypes.guess_type(original_name or "")[0] or "application/octet-stream"


def sha256_of(content: bytes) -> str:
    """明文哈希(file_crypto 顶注点名的命门:密文哈希会让同一份文件每次都不一样)。"""
    return content_hash(content)


# ── 行 DAL ──────────────────────────────────────────────────


def insert(
    cur,
    *,
    tenant_id: str,
    session_id: str,
    user_id: str,
    original_name: str,
    file_ref: str,
    size_bytes: int,
    sha256: str,
    mime: str,
    kind: str,
    kind_source: str,
    kind_reason: str,
    detect: Optional[dict] = None,
    status: str = STATUS_READY,
) -> dict:
    cur.execute(
        f"""
        INSERT INTO steward_attachments
            (tenant_id, session_id, user_id, original_name, file_ref, size_bytes, sha256, mime,
             kind, kind_source, kind_reason, detect, status, expires_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s,
                now() + make_interval(days => %s))
        RETURNING {_COLUMNS}
        """,
        (
            tenant_id,
            session_id,
            str(user_id),
            original_name[:255],
            file_ref,
            int(size_bytes),
            sha256,
            mime,
            kind,
            kind_source,
            kind_reason[:255],
            json.dumps(detect or {}, ensure_ascii=False, default=str),
            status,
            ttl_days(),
        ),
    )
    return dict(cur.fetchone())


def list_by_ids(cur, *, tenant_id: str, session_id: str, ids: list[str]) -> list[dict]:
    """按 (租户, 会话, id 集) 取。会话已按 (tenant, session, user) 三元组验过归属,
    附件跟会话走同一口径 —— 别人的会话取不到,别的会话的 id 也拼不进来。"""
    if not ids:
        return []
    cur.execute(
        f"SELECT {_COLUMNS} FROM steward_attachments "
        "WHERE tenant_id = %s AND session_id = %s AND id::text = ANY(%s) "
        "ORDER BY created_at, id",
        (tenant_id, session_id, [str(i) for i in ids]),
    )
    return [dict(r) for r in cur.fetchall()]


def get_owned(cur, *, tenant_id: str, attachment_id: str, user_id: str) -> Optional[dict]:
    """下载原件用:租户 + 上传人双锚(会话是私人工作记录,同租户别人也不给下)。"""
    cur.execute(
        f"SELECT {_COLUMNS} FROM steward_attachments "
        "WHERE tenant_id = %s AND id = %s AND user_id = %s",
        (tenant_id, attachment_id, str(user_id)),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def attach_to_message(cur, *, tenant_id: str, session_id: str, ids: list[str], message_id) -> int:
    """送出那一刻把附件挂到用户气泡上(送出前 message_id 为空 = 还在附件盘里)。
    只认还没挂过的行:同一件不会被后一条消息抢走。"""
    if not ids:
        return 0
    cur.execute(
        "UPDATE steward_attachments SET message_id = %s "
        "WHERE tenant_id = %s AND session_id = %s AND id::text = ANY(%s) AND message_id IS NULL",
        (str(message_id), tenant_id, session_id, [str(i) for i in ids]),
    )
    return cur.rowcount


def list_for_message(cur, *, tenant_id: str, session_id: str) -> list[dict]:
    """会话重建用:已挂到消息上的附件(按消息分组交给上层投影)。"""
    cur.execute(
        f"SELECT {_COLUMNS} FROM steward_attachments "
        "WHERE tenant_id = %s AND session_id = %s AND message_id IS NOT NULL "
        "ORDER BY created_at, id",
        (tenant_id, session_id),
    )
    return [dict(r) for r in cur.fetchall()]


def public_attachment(row: dict) -> dict[str, Any]:
    """附件 → 前端视图。file_ref(盘上真实路径)绝不外泄;认不出就如实写 unknown,
    不回落成「其他」这种假装认过的词。"""
    detect = row.get("detect") or {}
    return {
        "attachment_id": str(row["id"]),
        "name": row.get("original_name") or original_name_of(row.get("file_ref")) or "",
        "size_bytes": int(row.get("size_bytes") or 0),
        "mime": row.get("mime") or "",
        "kind": row.get("kind") or "unknown",
        "kind_source": row.get("kind_source") or SOURCE_UNKNOWN,
        "kind_reason": row.get("kind_reason") or "",
        "page_count": detect.get("page_count"),
        "needs_model": bool(detect.get("needs_model")),
        "actions": list(detect.get("actions") or []),
        "quote": detect.get("quote") or {},
        "status": row.get("status") or STATUS_READY,
    }


# ── 到期清理 ────────────────────────────────────────────────


def sweep_expired(limit: int = 200) -> dict[str, int]:
    """到期件收口:先收集 → 删行(事务内)→ 提交后删盘。顺序反了就再也定位不到文件。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute(
            "SELECT id::text AS id, file_ref FROM steward_attachments "
            "WHERE expires_at < now() ORDER BY expires_at LIMIT %s",
            (int(limit),),
        )
        rows = [dict(r) for r in cur.fetchall()]
        if rows:
            cur.execute(
                "DELETE FROM steward_attachments WHERE id::text = ANY(%s)",
                ([r["id"] for r in rows],),
            )
    for row in rows:
        remove_file(row.get("file_ref") or "")
    return {"rows": len(rows), "files": len(rows)}
