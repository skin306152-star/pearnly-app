# -*- coding: utf-8 -*-
"""撞码 409 得报「条码」而不是「编码」(P1-F 里用户看得见的那一半)。

数据库把重复条码拦下之后用户看到什么,由三处接缝共同决定:索引名(运行期建索引 SQL /
迁移 0092)、路由的 constraint_name → 错误码映射、四语文案。名字在任一处漂一个字母,
映射静默失配回落成「商品编码已存在」——用户按提示改编码,条码还是重的。这种漂法唯一索引
照样在、真库集成测试照样绿(它只验索引拦得住),没这道闸就没人看得见。

被断言的索引名不写死:从真产物里抠 —— _BARCODE_UNIQUE_DDL(prod 启动期靠它建)与 alembic
迁移链(本地/新库靠它)。「diag.constraint_name 真等于索引名」由真库那条验:
tests/integration/test_products_barcode_unique_real_db.test_violation_names_the_barcode_index。

迁移那边算的是"跑完整条链之后还活着的索引"= 各 upgrade() 建的减掉被 DROP 的:0093 把 0092
建的单位码索引换成了带 product_active 谓词的新名,只读某一个文件就会把已经被换掉的老名当成
现状。downgrade() 段落不算——它建的是回退后的样子,不是生产上跑着的样子。
"""

import re
import types
import unittest
from pathlib import Path

import psycopg2
from fastapi import HTTPException

from core.route_helpers import translate_unique_violation
from routes import products_routes
from services.sales import products as products_dal
from tests.unit.test_pos_inventory_i18n import APP_UI_LANGS, _lang_slices, _value

_ROOT = Path(__file__).resolve().parents[2]
_VERSIONS = _ROOT / "alembic" / "versions"
_ROUTES = _ROOT / "routes" / "products_routes.py"
_CREATED_INDEX = re.compile(r"CREATE UNIQUE INDEX IF NOT EXISTS (\w+)")
_DROPPED_INDEX = re.compile(r"DROP INDEX IF EXISTS (\w+)")
# 只传一个码的调用 = 忘了给映射,一律回落成默认码。
_UNMAPPED_CALL = re.compile(r"translate_unique_violation\(\s*\"[^\"]+\"\s*\)")


def _upgrade_body(text: str) -> str:
    body = text.split("def upgrade()", 1)[-1]
    return body.split("def downgrade()", 1)[0]


def _live_migration_index_names() -> set:
    """整条迁移链 upgrade() 跑完后还在的条码唯一索引名(按名字里的 barcode 认领)。

    按名字筛而不是按建表语句解析:迁移里同一个 upgrade() 常常既建条码索引又建别的唯一索引
    (0006 就是),整段抓会把 uq_sales_doc_number 之类一起卷进来。名字漏了 barcode 的情况由
    运行期那边兜:test_runtime_ddl_declares_both_barcode_indexes 锁死条数。
    """
    created: set = set()
    dropped: set = set()
    for path in sorted(_VERSIONS.glob("*.py")):
        body = _upgrade_body(path.read_text(encoding="utf-8"))
        created |= {n for n in _CREATED_INDEX.findall(body) if "barcode" in n}
        dropped |= {n for n in _DROPPED_INDEX.findall(body) if "barcode" in n}
    return created - dropped


class _Violation(psycopg2.errors.UniqueViolation):
    """带 constraint_name 的唯一约束冲突(真 psycopg2 类型 · 只把 diag 换成给定的名字)。"""

    def __init__(self, constraint):
        super().__init__("duplicate key value violates unique constraint")
        self._constraint = constraint

    @property
    def diag(self):
        return types.SimpleNamespace(constraint_name=self._constraint)


def _detail_for(constraint, *, default, mapping):
    with unittest.TestCase().assertRaises(HTTPException) as ctx:
        with translate_unique_violation(default, mapping):
            raise _Violation(constraint)
    return ctx.exception.detail


def _runtime_index_names():
    created = {
        m.group(1)
        for ddl in products_dal._BARCODE_UNIQUE_DDL
        for m in [_CREATED_INDEX.search(ddl)]
        if m
    }
    dropped = {
        m.group(1)
        for ddl in products_dal._BARCODE_UNIQUE_DDL
        for m in [_DROPPED_INDEX.search(ddl)]
        if m
    }
    return created - dropped


class BarcodeConflictSaysBarcodeTests(unittest.TestCase):
    def test_product_barcode_violation_is_not_reported_as_a_code_clash(self):
        detail = _detail_for(
            "uq_products_ws_barcode",
            default="sales.product_code_exists",
            mapping=products_routes._PRODUCT_UNIQUE_CODES,
        )
        self.assertEqual(detail, "sales.product_barcode_exists")

    def test_unit_barcode_violation_is_not_reported_as_a_name_clash(self):
        detail = _detail_for(
            "uq_product_units_live_barcode",
            default="sales.unit_name_exists",
            mapping=products_routes._UNIT_UNIQUE_CODES,
        )
        self.assertEqual(detail, "sales.unit_barcode_exists")

    def test_reviving_a_product_onto_a_taken_unit_barcode_is_not_a_code_clash(self):
        """重新上架/按编码复活会把单位码一起收回来,那一刻码可能已被别人占了。走的是建/改商品
        那条路,报「编码已存在」就是撒谎——用户改多少次编码都过不去,真正要改的是那个箱码。"""
        detail = _detail_for(
            "uq_product_units_live_barcode",
            default="sales.product_code_exists",
            mapping=products_routes._PRODUCT_UNIQUE_CODES,
        )
        self.assertEqual(detail, "sales.unit_barcode_exists")

    def test_code_violation_still_reports_the_code(self):
        detail = _detail_for(
            "uq_products_tenant_code",
            default="sales.product_code_exists",
            mapping=products_routes._PRODUCT_UNIQUE_CODES,
        )
        self.assertEqual(detail, "sales.product_code_exists")

    def test_unrecognized_constraint_falls_back_to_the_default_code(self):
        """老索引/新加的约束认不出时宁可给个笼统的码,也不能 500。"""
        detail = _detail_for(
            "uq_something_added_later",
            default="sales.product_code_exists",
            mapping=products_routes._PRODUCT_UNIQUE_CODES,
        )
        self.assertEqual(detail, "sales.product_code_exists")


class IndexNamesMatchAcrossArtifactsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = _runtime_index_names()
        cls.migration = _live_migration_index_names()
        cls.mapped = set(products_routes._PRODUCT_UNIQUE_CODES) | set(
            products_routes._UNIT_UNIQUE_CODES
        )

    def test_runtime_ddl_declares_both_barcode_indexes(self):
        self.assertEqual(len(self.runtime), 2, f"建索引 SQL 解析不出两条索引名:{self.runtime}")

    def test_migration_and_runtime_create_the_same_index_names(self):
        """prod 不跑 alembic(靠启动期双跑),本地跑迁移。名字不一致 = 两边长出不同索引,
        路由按名字翻的 409 只对一边生效。"""
        self.assertEqual(self.migration, self.runtime)

    def test_every_barcode_index_has_a_409_mapping(self):
        self.assertTrue(self.runtime <= self.mapped, f"没映射的索引:{self.runtime - self.mapped}")

    def test_no_write_path_forgets_to_pass_the_mapping(self):
        """新增写路径漏传映射 = 撞条码报「编码已存在」,前端只会照翻。"""
        found = _UNMAPPED_CALL.findall(_ROUTES.read_text(encoding="utf-8"))
        self.assertEqual(found, [], f"这些调用没带 constraint 映射:{found}")


class ConflictCopyExistsInFourLangsTests(unittest.TestCase):
    """映射出来的码没文案 = 前端 salesErrText 找不到键,回落成笼统的「保存失败」。"""

    @classmethod
    def setUpClass(cls):
        cls.slices = _lang_slices()
        cls.codes = sorted(
            set(products_routes._PRODUCT_UNIQUE_CODES.values())
            | set(products_routes._UNIT_UNIQUE_CODES.values())
        )

    def test_every_mapped_code_has_copy_in_four_langs(self):
        for code in self.codes:
            for lang in APP_UI_LANGS:
                val = _value(self.slices[lang], code)
                self.assertIsNotNone(val, f"{code} 缺 {lang} 文案")
                self.assertTrue(str(val).strip(), f"{code}.{lang} 是空的")


if __name__ == "__main__":
    unittest.main()
