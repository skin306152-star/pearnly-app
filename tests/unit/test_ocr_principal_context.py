# -*- coding: utf-8 -*-
"""请求级 principal → 引擎档账号灰度的兜底钥匙。

守两件事:① 鉴权层设过 email 后,深处建 OcrRequest 的那几条链(银行/GL-VAT/VAT 报表/
身份证)也吃得到灰度;② 没设时行为与上线前逐字节一致 —— 兜底不是新档位来源,
只是把「当前是谁」补进来。
"""

import unittest
from unittest import mock

from core import db  # noqa: F401 · 先 import 完成,避免 partial-init 循环
from services.ocr import engine_policy as ep
from services.ocr import principal_context as pc

_ENV_CLEAR = {"OCR_ENGINE_MODE": ""}
_GRAY_CFG = {**ep.DEFAULT_CONFIG, "overrides_by_account": {"gray@pearnly.com": "qwen"}}


class PrincipalContextTests(unittest.TestCase):
    def tearDown(self):
        self.assertIsNone(pc.current_email(), "上下文泄漏到了下一个用例")

    def test_unset_is_none(self):
        self.assertIsNone(pc.current_email())

    def test_email_is_lowercased_and_trimmed(self):
        with pc.principal_context("  Gray@Pearnly.COM  "):
            self.assertEqual(pc.current_email(), "gray@pearnly.com")

    def test_blank_email_is_none_not_empty_string(self):
        for blank in (None, "", "   "):
            with pc.principal_context(blank):
                self.assertIsNone(pc.current_email())

    def test_reset_restores_previous_value(self):
        token = pc.set_principal("outer@pearnly.com")
        try:
            inner = pc.set_principal("inner@pearnly.com")
            pc.reset_principal(inner)
            self.assertEqual(pc.current_email(), "outer@pearnly.com")
        finally:
            pc.reset_principal(token)


class ResolveModeFallbackTests(unittest.TestCase):
    """灰度名单命中与否,只看「有没有 principal」这一个变量。"""

    def test_principal_hits_account_override(self):
        with mock.patch.dict("os.environ", _ENV_CLEAR), pc.principal_context("gray@pearnly.com"):
            self.assertEqual(ep.resolve_mode("bank_statement", config=_GRAY_CFG), "qwen")

    def test_no_principal_keeps_previous_behaviour(self):
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            # 名单外的口径:银行任务照旧钉 direct35,不因兜底改档
            self.assertEqual(ep.resolve_mode("bank_statement", config=_GRAY_CFG), "direct35")
            self.assertEqual(ep.resolve_mode("invoice", config=_GRAY_CFG), "economy")

    def test_account_off_the_list_is_unaffected(self):
        with mock.patch.dict("os.environ", _ENV_CLEAR), pc.principal_context("other@pearnly.com"):
            self.assertEqual(ep.resolve_mode("invoice", config=_GRAY_CFG), "economy")

    def test_explicit_account_wins_over_principal(self):
        # 批处理可能代他人跑:调用方点名了账号,就不许被「当前登录的是谁」改档
        with mock.patch.dict("os.environ", _ENV_CLEAR), pc.principal_context("gray@pearnly.com"):
            mode = ep.resolve_mode("invoice", config=_GRAY_CFG, account="other@pearnly.com")
        self.assertEqual(mode, "economy")


class _FakeRequest:
    def __init__(self, auth):
        self.headers = {"Authorization": auth}


class AuthWiringTests(unittest.TestCase):
    """鉴权层是唯一设点:断在这里,六条深层构造链的灰度一起失效。真跑鉴权,不读源码断言。"""

    def setUp(self):
        # 鉴权层设了不 reset(请求 task 结束即回收),单测得自己把上下文还回去
        self._token = pc.set_principal(None)

    def tearDown(self):
        pc.reset_principal(self._token)

    def _authenticate(self, user):
        import core.auth as auth
        from services.auth import user_lookup

        user_lookup._USER_CACHE.clear()  # 鉴权走 TTL 缓存,每个用例从干净态进
        with (
            mock.patch.object(auth, "decode_access_token", return_value={"sub": "42"}),
            mock.patch("core.db.find_user_by_id", return_value=user),
        ):
            return auth.get_current_user_from_request(_FakeRequest("Bearer tok"))

    def test_login_email_lands_in_principal(self):
        returned = self._authenticate(
            {"id": 42, "email": "Gray@Pearnly.com", "tenant_id": "t-7", "is_active": True}
        )
        self.assertEqual(pc.current_email(), "gray@pearnly.com")
        self.assertEqual(returned["email"], "Gray@Pearnly.com")  # 返回值不被改写

    def test_authenticated_request_hits_account_gray_release(self):
        # 端到端的那句话:登录的是灰度名单里的人 → 深处不传 account 也解析到 qwen 档
        self._authenticate({"id": 42, "email": "gray@pearnly.com", "is_active": True})
        with mock.patch.dict("os.environ", _ENV_CLEAR):
            self.assertEqual(ep.resolve_mode("bank_statement", config=_GRAY_CFG), "qwen")

    def test_user_without_email_leaves_principal_empty(self):
        self._authenticate({"id": 42, "email": None, "is_active": True})
        self.assertIsNone(pc.current_email())


if __name__ == "__main__":
    unittest.main()
