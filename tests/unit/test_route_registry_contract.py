# -*- coding: utf-8 -*-
"""路由注册表守门(routes/registry.py)。

清单从 app.py 搬出来之后,最大的隐患是「搬漏一条」或「同一条挂两遍」——两者都不会报错,
只会让某个入口 404 或让匹配优先级悄悄改变。三条机器闸:
① ROUTERS 里没有重复对象;② include_all 挂的条数与 ROUTERS 一致、顺序一致;
③ ROUTERS 每个 router 的每条 path 都真出现在 app.app.routes 里(app 真的用了这张表)。
"""

from __future__ import annotations

import unittest

from routes import registry


class _RecordingApp:
    def __init__(self):
        self.included = []

    def include_router(self, router):
        self.included.append(router)


class RoutersTableTests(unittest.TestCase):
    def test_no_router_is_registered_twice(self):
        ids = [id(r) for r in registry.ROUTERS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_include_all_mounts_every_router_in_order(self):
        app = _RecordingApp()
        registry.include_all(app)
        self.assertEqual(app.included, list(registry.ROUTERS))


class MountedInRealAppTests(unittest.TestCase):
    """反证:表里有而线上没有 = 搬迁漏挂(这条闸就是为了不靠肉眼数 99 行)。"""

    @classmethod
    def setUpClass(cls):
        import app as app_module

        cls.mounted = {getattr(r, "path", "") for r in app_module.app.routes}

    def test_every_path_in_the_table_is_live(self):
        for router in registry.ROUTERS:
            for route in router.routes:
                # route.path 已含 router.prefix,别再拼一次
                self.assertIn(getattr(route, "path", ""), self.mounted, route)

    def test_retired_features_stay_unmounted_while_erp_team_remains(self):
        retired_prefixes = ("/api/knowledge", "/api/team", "/api/invitations")
        retired_pages = {"/console", "/console/{rest:path}", "/invite/{token}"}
        self.assertFalse(sorted(path for path in self.mounted if path.startswith(retired_prefixes)))
        self.assertTrue(retired_pages.isdisjoint(self.mounted))
        self.assertIn("/api/erp/team/access", self.mounted)
        self.assertIn("/api/erp/team/members", self.mounted)


if __name__ == "__main__":
    unittest.main(verbosity=2)
