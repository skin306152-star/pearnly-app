"""首引顺序冒烟:ERP push 链上的模块"各自第一个被 import"不得 ImportError。

事故(2026-09-18):给 services/erp/express_push/__init__.py 加了一行 express_target_projection
import,于是把 core.db 拉进了 push_exception_classify 的首引链 —— 谁先引到谁崩
(push_exception_classify → express_push → express_target_projection → core.db →
 dal_reexports → push_store → push_log_queries → 回到半初始化的 push_exception_classify)。
分片跑测试时随机红,而 `import app` 冒烟看不见:app 的导入顺序里 core.db 早就在库里了。

所以这里逐个模块起独立子进程,专门验"它就是第一个"的情况。
"""

import subprocess
import sys
import unittest
from pathlib import Path

MODULES = (
    "services.erp.express_account_identity",
    "services.erp.express_push",
    "services.erp.express_push.posting_profile",
    "services.erp.express_target_projection",
    "services.erp.push_exception_classify",
    "services.erp.selected_account",
    "services.erp.target_catalog_evidence",
)


class ErpFirstImportSmokeTests(unittest.TestCase):
    def test_each_module_survives_being_imported_first(self):
        root = Path(__file__).resolve().parents[2]
        for module in MODULES:
            with self.subTest(module=module):
                done = subprocess.run(
                    [sys.executable, "-c", f"import {module}"],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
                self.assertEqual(
                    done.returncode,
                    0,
                    f"{module} 作为首个 import 失败(循环 import?):\n{done.stderr[-900:]}",
                )


if __name__ == "__main__":
    unittest.main()
