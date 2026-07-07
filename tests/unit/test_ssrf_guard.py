# -*- coding: utf-8 -*-
"""SSRF 守卫:私网/loopback/link-local/元数据必挡,公网放行(安全评估 2026-07-07)。"""

from __future__ import annotations

import asyncio
import unittest

from services.erp.ssrf_guard import assert_public_config_url, assert_public_url


class SsrfGuardTest(unittest.TestCase):
    def test_blocks_internal_and_metadata(self) -> None:
        for bad in (
            "http://127.0.0.1/",  # loopback
            "http://10.0.0.5/api",  # private A
            "http://192.168.1.1/",  # private C
            "http://169.254.169.254/latest/meta-data/",  # AWS 元数据 / link-local
            "http://metadata.google.internal/computeMetadata/v1/",  # GCP 元数据主机名
            "http://0.0.0.0/",  # unspecified
        ):
            with self.assertRaises(ValueError, msg=f"应挡 {bad}"):
                assert_public_url(bad)

    def test_allows_public(self) -> None:
        # 公网字面 IP · 不触发 DNS · 不应抛
        for ok in ("http://8.8.8.8/", "https://1.1.1.1/path"):
            assert_public_url(ok)

    def test_empty_host_rejected(self) -> None:
        with self.assertRaises(ValueError):
            assert_public_url("http://")

    def test_config_helper_blocks_internal_and_skips_empty(self) -> None:
        # 共享入口:config.system_url 内网必挡;缺/空则放行(no-op)
        with self.assertRaises(ValueError):
            asyncio.run(assert_public_config_url({"system_url": "http://169.254.169.254/"}))
        asyncio.run(assert_public_config_url({}))  # 无 system_url · 不抛
        asyncio.run(assert_public_config_url({"system_url": ""}))  # 空 · 不抛


if __name__ == "__main__":
    unittest.main()
