# -*- coding: utf-8 -*-
"""每个注册 DMS OA 的公共契约 —— 遍历 channel registry,不写死 A/B。

新增 OA = 只在 `services/line_platform/channels.py` 加 registry 条目;本文件自动把这个 key
纳入 webhook / 绑定 / 会话 / 客户与订车取数 / 编辑 / 门户 / 凭据 / 查询权限 / 审批 /
菜单 URL 这些**真实共享入口**的机械契约。缺 Provider LIFF 声明、缺少真实入口、或 channel
key 没被传递下去 → 这里红。业务分支不在这里复写,只验入口与 key 传递。
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import os
import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes import line_dms_booking_edit_routes as dms_edit
from routes import line_dms_webhook_routes as webhook_routes
from services.line_dms import approval_flow, binding_guard, edit_link, masters_cache, menu_sync
from services.line_dms import menu_cards as dms_menu_cards
from services.line_dms import qa_cards, rich_menu
from services.line_dms import session_store
from services.line_dms import store as dms_store
from services.line_platform import channels
from services.line_platform import client as line_client
from services.line_platform import webhook_dedup

CHANNELS = tuple(channels.DMS_CHANNELS)
# Same Provider as the DMS Messaging API channels, so its LIFF app is the one they may reuse.
PROVIDER_LIFF = "2010411313-ProviderApp"
_SECRETS = {key: f"{key}-sec" for key in CHANNELS}
_TOKENS = {key: f"{key}-tok" for key in CHANNELS}


def _sign(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def _env() -> dict:
    """Production shape: the shared Provider LIFF exists, no per-OA LIFF override does."""
    env = {"LINE_LIFF_ID": PROVIDER_LIFF}
    for key, cfg in channels.DMS_CHANNELS.items():
        env[cfg.secret_env] = _SECRETS[key]
        env[cfg.token_env] = _TOKENS[key]
    return env


def _binding(key: str) -> dict:
    return {
        "id": f"epoch-{key}",
        "line_user_id": "L1",
        "user_id": "U1",
        "tenant_id": "T1",
        "channel_key": key,
    }


class _BearerRequest:
    def __init__(self, token: str = "tok"):
        self.headers = {"Authorization": f"Bearer {token}"}


class WebhookEntranceTests(unittest.TestCase):
    """每个注册 OA 都有自己的签名入口:自己的 secret 验签、自己的 OA 回复。"""

    _BODY = (
        b'{"events":[{"webhookEventId":"E1","type":"follow",'
        b'"source":{"userId":"L1"},"replyToken":"rt-1"}]}'
    )

    def _client(self) -> TestClient:
        app = FastAPI()
        app.include_router(webhook_routes.router)
        return TestClient(app)

    def _post(self, path: str, secret: str):
        return self._client().post(
            path, content=self._BODY, headers={"x-line-signature": _sign(self._BODY, secret)}
        )

    def test_every_channel_has_a_webhook_on_its_own_secret_and_oa(self):
        with mock.patch.dict(os.environ, _env(), clear=True):
            for key in CHANNELS:
                with self.subTest(channel=key):
                    with (
                        mock.patch.object(
                            dms_store, "get_binding_by_line_user", return_value=None
                        ) as lookup,
                        mock.patch.object(
                            webhook_routes, "dms_line_enabled_for", return_value=True
                        ),
                        mock.patch.object(line_client, "reply_text") as reply,
                        # Dedup is DB-backed; this contract is about the entrance, not the table.
                        mock.patch.object(
                            webhook_dedup, "claim", return_value=webhook_dedup.CLAIM_FRESH
                        ),
                        mock.patch.object(webhook_dedup, "mark_done"),
                    ):
                        response = self._post(channels.webhook_path(key), _SECRETS[key])
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json(), {"ok": True})
                    # 绑定查找按入口 OA 走,回复也用该 OA 的 token。
                    lookup.assert_called_once_with("L1", key)
                    self.assertEqual(reply.call_args.kwargs.get("channel"), key)

    def test_wrong_secret_is_rejected_on_every_channel(self):
        with mock.patch.dict(os.environ, _env(), clear=True):
            for key in CHANNELS:
                for other in CHANNELS:
                    if other == key:
                        continue
                    with self.subTest(channel=key, signed_by=other):
                        response = self._post(channels.webhook_path(key), _SECRETS[other])
                        self.assertEqual(response.status_code, 400)

    def test_unknown_channel_has_no_webhook_route(self):
        with mock.patch.dict(os.environ, _env(), clear=True):
            for path in ("/api/line/dms/webhook/zzz", "/api/line/dms/webhook/dms-zzz"):
                with self.subTest(path=path):
                    self.assertEqual(self._post(path, _SECRETS["dms"]).status_code, 404)

    def test_registry_paths_are_mounted_in_the_real_app(self):
        import app as app_module

        mounted = {getattr(route, "path", "") for route in app_module.app.routes}
        for key in CHANNELS:
            with self.subTest(channel=key):
                self.assertIn(channels.webhook_path(key), mounted)


class BindingScopeTests(unittest.TestCase):
    """绑定 / 会话 / 客户与订车取数共用同一处 channel 作用域。"""

    def test_master_reads_resolve_the_binding_under_the_channel_key(self):
        for key in CHANNELS:
            with self.subTest(channel=key):
                binding = _binding(key)
                with (
                    mock.patch.object(
                        dms_store, "get_binding_by_line_user", return_value=binding
                    ) as lookup,
                    mock.patch(
                        "services.erp.dms_id_ocr.resolve_dms_endpoint",
                        return_value={"id": "E1"},
                    ),
                ):
                    with binding_guard.scope(binding):
                        self.assertEqual(binding_guard.current_channel(), key)
                        endpoint = asyncio.run(masters_cache.qa_endpoint("L1", "E1"))
                self.assertEqual(endpoint, {"id": "E1"})
                lookup.assert_called_once_with("L1", key)

    def test_browser_authorization_keeps_the_token_channel(self):
        for key in CHANNELS:
            with self.subTest(channel=key):
                binding = _binding(key)
                claims = {
                    "entry": "dms",
                    "typ": "access",
                    "sub": "U1",
                    "dms_binding": dict(binding),
                }
                with (
                    mock.patch("core.auth.decode_access_token", return_value=claims),
                    mock.patch.object(
                        dms_store, "get_binding_by_line_user", return_value=binding
                    ) as lookup,
                    mock.patch("services.line_dms.binding_guard.current", return_value=True),
                ):
                    user = binding_guard.authorize_browser(_BearerRequest(), {"id": "U1"})
                self.assertEqual(user["_dms_binding"]["channel_key"], key)
                lookup.assert_called_once_with("L1", key)

    def test_browser_authorization_rejects_an_unknown_binding_channel(self):
        from core.pos_api import PosError

        claims = {
            "entry": "dms",
            "typ": "access",
            "sub": "U1",
            "dms_binding": {**_binding("dms"), "channel_key": "dms_zzz"},
        }
        with (
            mock.patch("core.auth.decode_access_token", return_value=claims),
            mock.patch.object(dms_store, "get_binding_by_line_user") as lookup,
        ):
            with self.assertRaises(PosError) as caught:
                binding_guard.authorize_browser(_BearerRequest(), {"id": "U1"})
        self.assertEqual(caught.exception.http_status, 401)
        lookup.assert_not_called()

    def test_session_store_keeps_the_channel_and_fails_closed_for_unknown(self):
        """会话行按 (tenant, channel, line) 落库:作用域里取当前 OA,未知 key 一律拒绝。"""
        for key in CHANNELS:
            with self.subTest(channel=key):
                with binding_guard.scope(_binding(key)):
                    self.assertEqual(session_store._channel(None), key)
                self.assertEqual(session_store._channel(key), key)
        with self.assertRaises(ValueError):
            session_store._channel("dms_zzz")
        with self.assertRaises(ValueError):
            session_store.get_session("T1", "L1", "dms_zzz")


class EditAndMenuUrlTests(unittest.TestCase):
    """编辑深链与菜单 URL 都带 channel key,并落到显式声明的 Provider LIFF。"""

    def setUp(self):
        self.enterContext(mock.patch.dict(os.environ, _env(), clear=True))

    def test_preview_edit_url_carries_the_channel(self):
        for key in CHANNELS:
            with self.subTest(channel=key):
                expected = f"https://liff.line.me/{PROVIDER_LIFF}?draft=N1&channel={key}"
                self.assertEqual(qa_cards._edit_url("N1", key), expected)
                self.assertEqual(edit_link.url("N1", key), expected)

    def test_legacy_oa_without_its_own_liff_also_uses_the_provider_app(self):
        """老 OA 的 ``LINE_DMS_LIFF_ID`` 从未配置时,菜单 3/4 也不能退化成无鉴权门户壳。"""
        self.assertNotIn("LINE_DMS_LIFF_ID", os.environ)
        self.assertEqual(qa_cards._edit_url("N1", "dms"), edit_link.url("N1", "dms"))
        self.assertIn(f"https://liff.line.me/{PROVIDER_LIFF}", edit_link.url("N1", "dms"))
        self.assertEqual(
            rich_menu.credentials_liff_url("dms").split("?")[0],
            f"https://liff.line.me/{PROVIDER_LIFF}/dms-booking",
        )
        self.assertEqual(
            rich_menu.portal_external_url("dms"),
            "https://pearnly.com/home/dms-booking?portal=dms&channel=dms&openExternalBrowser=1",
        )
        basic, query = rich_menu.menu_names("dms")
        self.assertEqual((basic, query), (rich_menu.MENU_NAME, rich_menu.QUERY_MENU_NAME))

    def test_channel_own_liff_override_beats_the_provider_declaration(self):
        with mock.patch.dict(os.environ, {"LINE_DMS_A_LIFF_ID": "A-OWN"}, clear=False):
            self.assertEqual(channels.liff_id("dms_a"), "A-OWN")
            self.assertEqual(channels.liff_env_name("dms_a"), "LINE_DMS_A_LIFF_ID")
            self.assertEqual(
                edit_link.url("N1", "dms_a"), "https://liff.line.me/A-OWN?draft=N1&channel=dms_a"
            )

    def test_rich_menu_and_flex_card_carry_the_channel(self):
        for key in CHANNELS:
            with self.subTest(channel=key):
                payload = rich_menu.build_payload(channel=key)
                self.assertEqual(payload["name"], channels.menu_name(rich_menu.MENU_NAME, key))
                actions = [area["action"] for area in payload["areas"]]
                self.assertEqual(actions[2]["uri"], rich_menu.portal_external_url(key))
                self.assertIn(f"channel={key}", actions[2]["uri"])
                self.assertEqual(
                    actions[3]["uri"],
                    f"https://liff.line.me/{PROVIDER_LIFF}"
                    f"/dms-booking?credentials=dms&channel={key}",
                )
                rows = dms_menu_cards.menu_card(channel=key)["contents"]["body"]["contents"]
                flex = [row["action"] for row in rows if row.get("action")]
                self.assertEqual(flex[2]["uri"], actions[2]["uri"])
                self.assertEqual(flex[2]["altUri"]["desktop"], rich_menu.portal_desktop_url(key))
                self.assertEqual(flex[3]["uri"], actions[3]["uri"])
                self.assertEqual(
                    flex[3]["altUri"]["desktop"], rich_menu.credentials_desktop_url(key)
                )
                self.assertTrue(flex[3]["uri"].startswith(f"https://liff.line.me/{PROVIDER_LIFF}/"))

    def test_menu_sync_reads_and_writes_on_the_same_channel(self):
        for key in CHANNELS:
            with self.subTest(channel=key):
                basic, query = rich_menu.menu_names(key)
                with (
                    mock.patch.object(
                        rich_menu,
                        "_list_menus",
                        return_value=[
                            {"name": basic, "richMenuId": "basic-id"},
                            {"name": query, "richMenuId": "query-id"},
                        ],
                    ) as listed,
                    mock.patch.object(menu_sync, "_allowed", return_value=False),
                    mock.patch.object(
                        menu_sync, "_request", return_value={"richMenuId": "query-id"}
                    ) as api,
                ):
                    menu_sync.sync("L1", key)
                listed.assert_called_once_with(key)
                self.assertIn(mock.call("GET", "user/L1/richmenu", key), api.call_args_list)
                self.assertIn(
                    mock.call("POST", "user/L1/richmenu/basic-id", key), api.call_args_list
                )


class PortalAndCredentialsEntryTests(unittest.TestCase):
    """门户与凭据入口:config/auth 都按 channel 解 Provider LIFF 与 chan 内绑定。"""

    def setUp(self):
        self.enterContext(mock.patch.dict(os.environ, _env(), clear=True))

    def test_liff_config_returns_provider_app_and_the_channel_key(self):
        for key in CHANNELS:
            with self.subTest(channel=key):
                result = asyncio.run(dms_edit.dms_booking_liff_config(channel=key))
                self.assertEqual(
                    result["data"],
                    {"liff_id": PROVIDER_LIFF, "channel_key": key, "available": True},
                )

    def test_unknown_channel_config_is_rejected(self):
        from core.pos_api import PosError

        with self.assertRaises(PosError) as caught:
            asyncio.run(dms_edit.dms_booking_liff_config(channel="dms_zzz"))
        self.assertEqual(caught.exception.http_status, 404)

    def test_liff_auth_verifies_provider_liff_and_scopes_the_binding(self):
        user = {"id": "U1", "username": "sale02", "tenant_id": "T1", "is_active": True}
        for key in CHANNELS:
            with self.subTest(channel=key):
                binding = _binding(key)
                with (
                    mock.patch.object(
                        dms_edit, "verify_id_token", return_value={"sub": "L1"}
                    ) as verify,
                    mock.patch.object(
                        dms_store, "get_binding_by_line_user", return_value=binding
                    ) as lookup,
                    mock.patch.object(dms_edit.db, "find_user_by_id", return_value=user),
                    mock.patch(
                        "services.dms_roster.store.get_profile", return_value={"status": "active"}
                    ),
                    mock.patch("services.line_dms.account_channel.get_channel", return_value=key),
                    mock.patch("services.line_dms.binding_guard.current", return_value=True),
                    mock.patch.object(dms_edit, "create_access_token", return_value="JWT") as issue,
                ):
                    result = asyncio.run(
                        dms_edit.dms_booking_liff_auth(
                            dms_edit.LiffAuthIn(id_token="tok", channel=key)
                        )
                    )
                # 没有 OA 专属 LIFF → 用 registry 里显式声明的共享 Provider env 验 token。
                verify.assert_called_once_with("tok", channels.liff_env_name(key))
                self.assertEqual(channels.liff_env_name(key), "LINE_LIFF_ID")
                lookup.assert_called_once_with("L1", key)
                self.assertEqual(result["data"]["token"], "JWT")
                self.assertEqual(issue.call_args.kwargs["dms_binding"], binding)


class ApprovalRecipientTests(unittest.TestCase):
    def test_approver_targets_keep_their_own_oa(self):
        for key in CHANNELS:
            with self.subTest(channel=key):
                rows = [
                    {
                        "user_id": "U9",
                        "display_name": "Admin",
                        "line_user_id": "L9",
                        "line_channel_key": key,
                        "dms_role": "admin",
                        "status": "active",
                    }
                ]
                with mock.patch.object(
                    approval_flow.roster_store, "list_profiles", return_value=rows
                ):
                    approvers = approval_flow._bound_approvers("T1")
                self.assertEqual([a["channel_key"] for a in approvers], [key])


class TransportCredentialTests(unittest.TestCase):
    """传输层凭据 env 名来自 registry,新增 OA 不会再漏改第三张表。"""

    def test_every_registry_channel_has_transport_credentials(self):
        for key, cfg in channels.DMS_CHANNELS.items():
            with self.subTest(channel=key):
                self.assertEqual(
                    line_client._channel_env_names(key), (cfg.secret_env, cfg.token_env)
                )
                self.assertEqual(line_client._credentials_blob_env(key), cfg.credentials_env)

    def test_unknown_channel_has_no_transport_credentials(self):
        self.assertEqual(line_client._channel_env_names("dms_zzz"), ("", ""))
        self.assertEqual(line_client._credentials_blob_env("dms_zzz"), "")


if __name__ == "__main__":
    unittest.main()
