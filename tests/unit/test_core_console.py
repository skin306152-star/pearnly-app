# -*- coding: utf-8 -*-
"""core.console 契约:stdout 编码兜底(errors=replace)+ 三个 CLI 共用同源不留私副本。"""

import sys
import unittest
from unittest.mock import MagicMock, patch

from core import console


class MakeStdoutEncodingSafeTests(unittest.TestCase):
    def test_reconfigures_errors_replace_keeping_native_encoding(self):
        fake = MagicMock(spec=["reconfigure"])
        with patch.object(sys, "stdout", fake):
            console.make_stdout_encoding_safe()
        fake.reconfigure.assert_called_once_with(errors="replace")

    def test_noop_when_stream_lacks_reconfigure(self):
        with patch.object(sys, "stdout", MagicMock(spec=[])):
            console.make_stdout_encoding_safe()  # 不抛即过(StringIO 等替身流)

    def test_clis_share_the_single_implementation(self):
        from services.fileconv import cli as fileconv_cli
        from services.payroll import cli as payroll_cli
        from services.sales_agg import cli as sales_agg_cli

        for mod in (fileconv_cli, payroll_cli, sales_agg_cli):
            self.assertIs(mod.make_stdout_encoding_safe, console.make_stdout_encoding_safe)


if __name__ == "__main__":
    unittest.main()
