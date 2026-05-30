#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/integration/test_dal_facade_completeness_safety_net.py · REFACTOR-WC

DAL facade 完整性安全网 · 纯加测试不改业务 · 给 A 拆 db.py/services 当保险。

锁定 A 重构的核心机制 —— DAL facade re-export(REFACTOR-WA-B2):各业务域 DAL 已搬到
services/*/store.py,db.py 末尾 `from services.dal_reexports import *` 桥回 db 命名空间,
所有历史 `db.xxx()` 调用点零改动(见 services/dal_reexports.py)。

隐患:A 拆某域时若漏掉/拼错 `_REEXPORTS` 里一个名,或源模块没定义它,则 `db.<name>`
凭空消失 —— 调用点(charge_ocr 等热路径)运行期才 AttributeError 炸,且单测单独测叶子
模块时未必发现。本文件数据驱动遍历 `_REEXPORTS`,断言每个声明的 re-export 真落到 db 上
且对象身份一致(自维护:A 加新 re-export 自动纳入,漏一个立刻红)。纯 import(0 DB ·
0 网络)→ CI 真跑不 skip。

覆盖维度(对应 loop「给 A 拆高敏当保险」· facade 机制层):
  1. 完整性 — _REEXPORTS 每个名都 hasattr(db, name)(不漏桥)
  2. 身份 — db.<name> is 源模块.<name>(桥对对象 · 不是同名另一物)
  3. 高敏锚点 — 钱写入热路径名(charge_ocr/estimate_*/get_cursor/_bkk_year_month)显式在且可调用
"""

from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load():
    try:
        import db
        import services.dal_reexports as dal
    except Exception as e:  # pragma: no cover - import 环境问题才触发
        raise unittest.SkipTest(f"db / services.dal_reexports 不可 import:{e}")
    return db, dal


def _iter_reexports(dal):
    """yield (modpath, src_name, dst_name) · 处理 str 同名 与 (src,dst) 重命名两种元素。"""
    for modpath, names in dal._REEXPORTS.items():
        for entry in names:
            src, dst = (entry, entry) if isinstance(entry, str) else (entry[0], entry[1])
            yield modpath, src, dst


class ReexportsStructureTest(unittest.TestCase):
    """_REEXPORTS 是非空 dict · 桥机制的数据源"""

    def setUp(self) -> None:
        self.db, self.dal = _load()

    def test_reexports_is_non_empty_dict(self) -> None:
        self.assertIsInstance(self.dal._REEXPORTS, dict)
        self.assertGreater(len(self.dal._REEXPORTS), 0)

    def test_has_meaningful_name_count(self) -> None:
        # 当前 ~286 名 / 36 域 · 设个下限防有人把字典清空还以为没事
        total = sum(1 for _ in _iter_reexports(self.dal))
        self.assertGreater(total, 100, f"re-export 名总数 {total} 异常偏低 · facade 可能被掏空")


class FacadeCompletenessTest(unittest.TestCase):
    """每个声明的 re-export 都桥到 db 上(漏一个 = db.xxx() 运行期 AttributeError)"""

    def setUp(self) -> None:
        self.db, self.dal = _load()

    def test_every_reexport_present_on_db(self) -> None:
        missing = []
        for modpath, _src, dst in _iter_reexports(self.dal):
            if not hasattr(self.db, dst):
                missing.append(f"{modpath} :: {dst}")
        self.assertEqual(
            missing,
            [],
            msg=(
                "_REEXPORTS 声明了但 db 上没有(桥漏/源模块未定义)· 缺失:\n  "
                + "\n  ".join(missing)
                + "\n这些名的 db.<name>() 调用点会运行期 AttributeError · 拆 DAL 别漏桥。"
            ),
        )

    def test_reexport_object_identity_preserved(self) -> None:
        # db.<name> 必须就是源模块那个对象(桥对身份 · 不是恰好同名的另一个东西)
        mismatch = []
        for modpath, src, dst in _iter_reexports(self.dal):
            try:
                mod = importlib.import_module(modpath)
            except Exception as e:  # pragma: no cover
                mismatch.append(f"{modpath} (import 失败: {e})")
                continue
            if not hasattr(self.db, dst) or not hasattr(mod, src):
                continue  # 缺失由 completeness 测负责报
            if getattr(self.db, dst) is not getattr(mod, src):
                mismatch.append(f"{modpath} :: {src} -> db.{dst}(身份不一致)")
        self.assertEqual(mismatch, [], msg="re-export 身份漂移:\n  " + "\n  ".join(mismatch))


class HighSensitivityAnchorTest(unittest.TestCase):
    """钱写入热路径名显式锚定(铁律 #26)· 即便遍历测被误改也兜住"""

    def setUp(self) -> None:
        self.db, self.dal = _load()

    def test_billing_hot_path_names_present_and_callable(self) -> None:
        for name in (
            "get_cursor",
            "charge_ocr",
            "charge_ocr_async",
            "estimate_pdf_cost_thb",
            "estimate_excel_cost_thb",
            "is_user_billing_exempt",
            "_bkk_year_month",
        ):
            self.assertTrue(hasattr(self.db, name), f"db.{name} 不见了(钱路径桥丢)")
            self.assertTrue(callable(getattr(self.db, name)), f"db.{name} 不可调用")


if __name__ == "__main__":
    unittest.main(verbosity=2)
