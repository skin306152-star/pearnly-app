# -*- coding: utf-8 -*-
"""Google Drive 归档(建归档树文件夹 + 上传原图/PDF · 契约 05 §2.2)。

分两层:DriveClient 真 API 适配器(googleapiclient · 用户验收范围,本环境验不了)与
ensure_folder_path/archive_doc 编排(纯逻辑,注入 client 可单测)。归档树路径由
archive_tree(纯)算好;drive 只按段逐层 find-or-create 文件夹再上传。

隔离:client 用某套账的 access_token(valid_access_token 取)· 主体目录由该套账主体派生
→ 绝不跨套账串目录。drive.file scope:只动本 app 建的文件,不要全盘权限。
"""

from __future__ import annotations

from typing import Optional

from services.export import archive_tree

_FOLDER_MIME = "application/vnd.google-apps.folder"


class DriveClient:
    """googleapiclient Drive 适配器(真 API · 用户验收)。access_token 来自 google_oauth。"""

    def __init__(self, access_token: str):
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        self._svc = build(
            "drive", "v3", credentials=Credentials(token=access_token), cache_discovery=False
        )

    @staticmethod
    def _esc(name: str) -> str:
        return (name or "").replace("\\", "\\\\").replace("'", "\\'")

    def find_folder(self, name: str, parent_id: str) -> Optional[str]:
        q = (
            f"name='{self._esc(name)}' and '{parent_id}' in parents "
            f"and mimeType='{_FOLDER_MIME}' and trashed=false"
        )
        res = self._svc.files().list(q=q, fields="files(id)", pageSize=1).execute()
        files = res.get("files") or []
        return files[0]["id"] if files else None

    def create_folder(self, name: str, parent_id: str) -> str:
        body = {"name": name, "mimeType": _FOLDER_MIME, "parents": [parent_id]}
        return self._svc.files().create(body=body, fields="id").execute()["id"]

    def find_file(self, name: str, parent_id: str) -> Optional[str]:
        q = f"name='{self._esc(name)}' and '{parent_id}' in parents and trashed=false"
        res = self._svc.files().list(q=q, fields="files(id)", pageSize=1).execute()
        files = res.get("files") or []
        return files[0]["id"] if files else None

    def upload(self, parent_id: str, name: str, data: bytes, mime: str) -> dict:
        from googleapiclient.http import MediaInMemoryUpload

        media = MediaInMemoryUpload(data, mimetype=mime, resumable=False)
        body = {"name": name, "parents": [parent_id]}
        return (
            self._svc.files().create(body=body, media_body=media, fields="id,webViewLink").execute()
        )


def ensure_folder_path(client, segments: list, root_parent: str = "root") -> str:
    """按归档树段逐层 find-or-create 文件夹,返回叶文件夹 id(幂等:已存在则复用)。"""
    parent = root_parent
    for seg in segments:
        fid = client.find_folder(seg, parent) or client.create_folder(seg, parent)
        parent = fid
    return parent


def folder_web_link(folder_id: str) -> str:
    return f"https://drive.google.com/drive/folders/{folder_id}"


def archive_doc(
    client,
    *,
    subject: str,
    doc_date,
    supplier: str,
    doc_id: str,
    image_bytes: Optional[bytes] = None,
    image_name: str = "原图.jpg",
    image_mime: str = "image/jpeg",
    pdf_bytes: Optional[bytes] = None,
) -> dict:
    """归档一张单:证据原图进 证据/<日期_商户_id>/ 子夹,PDF 进 交会计/ 扁平。

    返回 {evidence_folder_id, evidence_url, pdf_file_id}。注入 client → 编排可单测。
    """
    out = {"evidence_folder_id": None, "evidence_url": "", "pdf_file_id": None}

    ev_segs = archive_tree.evidence_folder_path(subject, doc_date, supplier, doc_id)
    ev_folder = ensure_folder_path(client, ev_segs)
    out["evidence_folder_id"] = ev_folder
    out["evidence_url"] = folder_web_link(ev_folder)
    if image_bytes:
        client.upload(ev_folder, image_name, image_bytes, image_mime)

    if pdf_bytes:
        acct_segs = archive_tree.accountant_dir_path(subject, doc_date)
        acct_folder = ensure_folder_path(client, acct_segs)
        pdf_name = archive_tree.accountant_pdf_name(doc_date, supplier, doc_id)
        res = client.upload(acct_folder, pdf_name, pdf_bytes, "application/pdf")
        out["pdf_file_id"] = res.get("id")
    return out
