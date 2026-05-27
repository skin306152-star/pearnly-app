# ADR-007 · 巨石业务逻辑抽到 `services/` · copy-out + re-export 范式

> **状态**:已采纳并大规模实践(2026-05-22 起)· B2 已抽 18 域 DAL · B1 已抽 21 router · 进行中
> **关联 task**:REFACTOR-B1(`app.py` 拆 router)· REFACTOR-B2(`db.py` 拆 services DAL)
> **关联铁律**:#23 硬门槛 #1(`app.py` 封死)/ #2(`db.py` 封死)· #17 / #21(新逻辑进独立模块)

---

## 背景

整顿前后端两块巨石:`app.py`(曾 10,075 行 · 几百个 `@app.*` 路由)和 `db.py`(曾 10,663 行 ·
几百个业务 SQL 函数)。改一处牵连一片,无法单独测试,也违反"每文件 100-500 行"的 Google 级目标。

直接"剪切—粘贴"拆分有两个致命风险:
1. **调用点海量**:`db.xxx()` / `from db import xxx` 散布全项目,搬走函数 = 要改几百个调用点 = 高回归风险。
2. **测试 patch 失效 + 循环 import**:很多既有测试 `mock.patch("db.get_cursor")` 做 tenant 隔离;若 service 模块用 `from db import get_cursor` 按值导入,patch 就打不中;service 反过来 import `app`/`db` 顶层符号又容易循环。

## 决策

**把 `db.py` / `app.py` 巨石里的业务逻辑用「copy-out + re-export」范式,整片搬到
`services/<域>/store.py`(数据访问层)与 `*_routes.py`(路由层),调用点零改动。**

这套范式有 7 条要点(下窗口照搬):

1. **整片搬 cohesive 域**:一个内聚的业务域(如 notification、erp.push)整组函数一次搬进一个 service 模块,不零敲碎打。
2. **`import db` + 运行时 `db.get_cursor()`**:service 模块顶部 `import db`,函数体里调 `db.get_cursor()` —— **不用** `from db import get_cursor`(按值导入会让 `mock.patch("db.get_cursor")` 的 tenant 隔离测试 patch 失效),同时避免循环 import(只 import 模块、运行时才解析符号)。
3. **`db.py` 文件尾 re-export**:在 `db.py` 末尾写 `from services.X import a as a`(用 `x as x` 显式重导出形式,pyflakes 不报 F401)。这样所有 `db.xxx()` / `from db import xxx` 调用点**零改动**,函数对象还是同一个。
4. **私有 helper / 常量不外露**:`_helper` / `_常量` 留在 service 模块内,不 re-export(先确认无外部 `db._x` 引用);校验常量只在本域用则随域搬(如 `ERP_TYPES_VALID` 随 mappings 域搬)。
5. **字节级 LF splice**:大块用 PowerShell 字节级提取拼装(把 `get_cursor(` 替成 `db.get_cursor(` + 拼 header),避免手抄 700+ 行出错;LF 无 BOM,边界 assert。
6. **每域带契约测试**:验证"函数在 service 模块" + "db 命名空间 re-export 的是**同一个对象**"(`assertIs`),防漂移。
7. **抽前必 re-grep 行号**:行号随每次删除下移,别用旧的 def-list 行号。

`app.py` 同理 → 新路由建 `*_routes.py` + `app.include_router()`,不进巨石。

## 落地交付

**B2(`db.py` → `services/<域>/store.py`)**:`db.py` 10,663 → **4,513 行**(减 6,150)· 抽 **18 个域 DAL**:
`email_ingest` / `erp.oauth` / `erp.mappings` / `notification` / `erp.push` /
`recon.{vat_recon_tasks,gl_vat,bank_recon_v2,bank_recon_v1}` / `archive` / `rd` / `cost` /
`exceptions` / `clients` / `billing` / `recon.vat_recon`(三表组)/ `audit` / `team`。

**B1(`app.py` → `*_routes.py`)**:`app.py` 10,075 → **4,459 行**(减 5,616)· 抽 **21 router / 30 个 `*_routes.py`**(notification / clients / exceptions / team / erp_mappings / bank_recon / tenant / erp_xero / pages / me / line_binding 等)。

**契约测试范例**(`tests/unit/test_notification_store_contract.py`,实物):
```python
import db
from services.notification import store

class NotificationStoreContractTests(unittest.TestCase):
    def test_all_functions_live_in_service_module(self):   # 函数在 service 模块
        for name in _MOVED:
            self.assertTrue(callable(getattr(store, name)))
    def test_db_reexports_same_object(self):               # db re-export 同一对象(防漂移)
        for name in _MOVED:
            self.assertIs(getattr(db, name), getattr(store, name), f"db.{name} 漂移!")
```

**db.py 尾部 re-export 范例**(实物 `db.py` L4414):
```python
from services.notification.store import (
    ensure_notification_tables as ensure_notification_tables,
    list_notification_rules as list_notification_rules,
    ...
)
```

**service 模块头部范例**(实物 `services/notification/store.py`):`import db` → 函数体 `with db.get_cursor(commit=True) as cur:`。

## 理由

1. **零改调用点 = 零回归风险**:re-export 让 `db.xxx()` 接口不变,几百个调用点一行不动。验证靠"生产 401 路由探测零丢路由"+ 契约测试。
2. **`db.get_cursor()` 运行时解析**:保住 `mock.patch("db.get_cursor")` 的 tenant 隔离测试(既有 dedup / 分类器 / buyer-resolver / salesvat 测试经 re-export 仍全绿),并防循环 import。
3. **契约测试锁死同一性**:`assertIs` 确保 re-export 的不是另一个同名函数,杜绝"db 和 service 两份逻辑漂移"。
4. **批量本地 commit 再 push**:攒几个域再 push,减少生产重启次数。
5. **cohesive 整片搬**:按业务域而非按函数搬,模块职责清晰,符合 `services/<domain>/*.py` 结构。

## 取舍 / 边界

- **`db.py` 仍是"门面"**:re-export 让 `db.py` 短期内还是统一入口(尾部一堆 import),没有强制调用点直接 `from services.X import ...`。这是刻意的渐进——先零回归搬出逻辑,调用点迁移留后续。
- **高敏域排除 batch / 后置**:`credits` / `charge_ocr`(钱)、`user` / `auth`(登录)、`ocr_history`(OCR 热路径)**不进并行 batch、不在无人值守时搬**,Zihao 在场单独做。
- **RLS 基础设施别搬别动**:`get_cursor_rls` / `_is_rls_enabled` / `get_clients_rls_status` / `run_rls_isolation_tests` 是 cursor 框架,与 `get_cursor` 并列,**不属于业务 DAL**,保留在 `db.py`。
- **`app.py` 安全部分已到顶**:剩 22 个 `@app` 路由全是登录/OAuth/email-code/JWT 合并等安全敏感,或 OCR recognize 850 行 / LINE webhook 勿碰,`app.py < 500` 需 auth 专窗口(铁律 #16),不能靠安全搬家达成。

## 后果

- ✅ **硬门槛 #1 / #2 生效**:`app.py` 封死(新路由进 `*_routes.py`)、`db.py` 封死(新业务 SQL 进 `services/`)。
- ✅ `services/**/*.py` 从 ~40 增至 66+,模块文件数往"50-100 个"目标走;每域契约测试给 D 阶段测试覆盖率免费加分(unit 测试数随域增长)。
- ✅ 这套范式被 BATCH_STRATEGY.md Wave 1 直接复用为并行 agent 的"copy-out"模板(见 ADR-008)。
- 📌 剩余:`db.py` / `app.py` 冲刺 < 300 行需把高敏域(auth/credits/ocr_history)在 Zihao 在场时搬出,以及把 `db.py` 门面 re-export 进一步收敛。
