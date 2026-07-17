# -*- coding: utf-8 -*-
"""line_client channel profile 守门(DL-1 · B1)。

不传 channel = 逐字节走 default('LINE_CHANNEL_*');channel='dms' 走独立
'LINE_DMS_CHANNEL_*';DMS 凭据缺失 → verify False + warning。
"""

import base64
import hashlib
import hmac
import os
import unittest
from unittest import mock

from services.line_binding import line_client


def _sign(body: bytes, secret: str) -> str:
    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(mac).decode("utf-8")


class ChannelSecretProfileTests(unittest.TestCase):
    def test_default_channel_reads_legacy_env(self):
        body = b'{"events":[]}'
        with mock.patch.dict(os.environ, {"LINE_CHANNEL_SECRET": "legacy-sec"}, clear=False):
            sig = _sign(body, "legacy-sec")
            # 不传 channel = 老会计站行为:用 LINE_CHANNEL_SECRET 验签。
            self.assertTrue(line_client.verify_signature(body, sig))
            self.assertEqual(line_client._get_channel_secret(), "legacy-sec")

    def test_dms_channel_reads_dms_env_not_legacy(self):
        body = b'{"events":[]}'
        with mock.patch.dict(
            os.environ,
            {"LINE_CHANNEL_SECRET": "legacy-sec", "LINE_DMS_CHANNEL_SECRET": "dms-sec"},
            clear=False,
        ):
            # 用 default secret 签的 body 不能被 dms channel 验过(隔离)。
            self.assertFalse(
                line_client.verify_signature(body, _sign(body, "legacy-sec"), channel="dms")
            )
            # 用 dms secret 签的才过。
            self.assertTrue(
                line_client.verify_signature(body, _sign(body, "dms-sec"), channel="dms")
            )

    def test_dms_env_missing_returns_false_and_warns(self):
        body = b'{"events":[]}'
        with mock.patch.dict(os.environ, {"LINE_CHANNEL_SECRET": "legacy-sec"}, clear=False):
            os.environ.pop("LINE_DMS_CHANNEL_SECRET", None)  # patch.dict 退出时整体还原
            with self.assertLogs("services.line_binding.line_client", level="WARNING") as cm:
                ok = line_client.verify_signature(body, _sign(body, "legacy-sec"), channel="dms")
            self.assertFalse(ok)
            self.assertTrue(any("LINE_DMS_CHANNEL_SECRET" in m for m in cm.output))

    def test_token_env_names_per_channel(self):
        with mock.patch.dict(
            os.environ,
            {
                "LINE_CHANNEL_ACCESS_TOKEN": "legacy-tok",
                "LINE_DMS_CHANNEL_ACCESS_TOKEN": "dms-tok",
            },
            clear=False,
        ):
            self.assertEqual(line_client._get_channel_token(), "legacy-tok")
            self.assertEqual(line_client._get_channel_token("dms"), "dms-tok")
            # 未知 channel 回落 default(不炸)。
            self.assertEqual(line_client._get_channel_token("nope"), "legacy-tok")


if __name__ == "__main__":
    unittest.main()
