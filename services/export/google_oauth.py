# -*- coding: utf-8 -*-
"""Google OAuth 2.0(独立外流授权 · Drive 写入 + Sheets · 非 userinfo 登录流 · 契约 05 §2.2)。

登录用的 Google OAuth 只有 userinfo scope,拿不到 Drive/Sheets 写权 → 必须独立流。
凭据按套账存(google_store)。env 配置(产品自己的 OAuth client):
  GOOGLE_EXPORT_CLIENT_ID / GOOGLE_EXPORT_CLIENT_SECRET / GOOGLE_EXPORT_REDIRECT_URI

HTTP 调用集中在小函数(requests)便于 mock 单测;真授权(浏览器跳转 + 写真 Drive)
是用户验收范围。
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

import requests

from services.export import google_store

AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo"

# Drive 文件级写入(只动本 app 建的文件,不要全盘 drive 权) + Sheets + 拿邮箱标识连接账号。
SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
    "openid",
    "email",
]
_TIMEOUT = 20


def client_id() -> str:
    return os.environ.get("GOOGLE_EXPORT_CLIENT_ID", "").strip()


def _client_secret() -> str:
    return os.environ.get("GOOGLE_EXPORT_CLIENT_SECRET", "").strip()


def redirect_uri(default: str = "") -> str:
    return os.environ.get("GOOGLE_EXPORT_REDIRECT_URI", "").strip() or default


def is_configured() -> bool:
    """产品 OAuth client 是否配齐(未配 → 路由返友好引导,不 500)。"""
    return bool(client_id() and _client_secret())


def build_authorize_url(*, state: str, redirect: str) -> str:
    """授权跳转 URL。access_type=offline + prompt=consent 确保拿到 refresh_token。"""
    params = {
        "client_id": client_id(),
        "redirect_uri": redirect,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    return f"{AUTH_ENDPOINT}?{urlencode(params)}"


def _expires_at(expires_in) -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=int(expires_in or 0))


def exchange_code(*, code: str, redirect: str) -> dict:
    """授权码 → token。返回 {access_token,refresh_token,expires_at,scope,email}。失败抛。"""
    resp = requests.post(
        TOKEN_ENDPOINT,
        data={
            "code": code,
            "client_id": client_id(),
            "client_secret": _client_secret(),
            "redirect_uri": redirect,
            "grant_type": "authorization_code",
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    tok = resp.json()
    return {
        "access_token": tok.get("access_token") or "",
        "refresh_token": tok.get("refresh_token") or "",
        "expires_at": _expires_at(tok.get("expires_in")),
        "scope": tok.get("scope") or "",
        "email": fetch_email(tok.get("access_token") or ""),
    }


def refresh_access_token(*, refresh_token: str) -> dict:
    """refresh_token → 新 access_token。返回 {access_token, expires_at}。失败抛。"""
    resp = requests.post(
        TOKEN_ENDPOINT,
        data={
            "refresh_token": refresh_token,
            "client_id": client_id(),
            "client_secret": _client_secret(),
            "grant_type": "refresh_token",
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    tok = resp.json()
    return {
        "access_token": tok.get("access_token") or "",
        "expires_at": _expires_at(tok.get("expires_in")),
    }


def fetch_email(access_token: str) -> str:
    """拿连接账号邮箱(标识 UI 显示)。失败返空(不阻断授权)。"""
    if not access_token:
        return ""
    try:
        resp = requests.get(
            USERINFO_ENDPOINT,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("email") or ""
    except requests.RequestException:
        return ""


def _is_expired(expires_at) -> bool:
    """过期或 60 秒内即将过期 → 需刷新。无过期时间视为需刷新。"""
    if not expires_at:
        return True
    if isinstance(expires_at, str):
        try:
            expires_at = datetime.fromisoformat(expires_at)
        except ValueError:
            return True
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) >= expires_at - timedelta(seconds=60)


def valid_access_token(cur, *, tenant_id, workspace_client_id) -> Optional[str]:
    """取该套账可用 access_token,过期则用 refresh_token 刷新并写回。无凭据 → None。"""
    cred = google_store.get_credential(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    if not cred:
        return None
    if not _is_expired(cred.get("expires_at")):
        return cred["access_token"]
    refreshed = refresh_access_token(refresh_token=cred["refresh_token"])
    google_store.update_access_token(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        access_token=refreshed["access_token"],
        expires_at=refreshed["expires_at"],
    )
    return refreshed["access_token"]
