# Pearnly 测试任务书 · 通用测试标准 + POS/平台套餐专项

> 用途:把"一个功能做完后怎么按大厂标准测"固化成一份可复用文档。
> Part 1 = 任何功能都套用的通用标准(以后新功能直接复用)。
> Part 2 = 本次 POS 模块 + 平台业态套餐切换模块 的具体用例。
> 默认是【只读体检】:只测、只定位问题、只出报告,不改任何代码/数据。

---

# Part 1 · 通用测试标准(任何功能复用)

## ⚠️ 最高约束:只读测试,禁止任何写操作(覆盖本文档后面所有内容)
1. 只能:运行已有测试、读代码、跑浏览器 E2E、观察结果,目的是定位真实问题。
2. 禁止:修改/新增/删除任何文件(源码、测试、文档、配置都不行)。
3. 禁止:git add / commit / push;禁止改动任何 prod / 真实数据库的真实数据。
4. 所有发现的问题、所有"建议新增的测试/建议的修复",只写进报告里描述,不要真建文件、不要真改。
5. 跑 E2E 一律用独立测试租户,事务结尾 rollback,零残留,不污染任何真实数据。
6. 凡涉及"改/建/修复"的动作,一律停下来写进报告等人决定,不许自己动手。
> 本仓库多个窗口共享同一 git 工作树,任何写操作都可能卷入别处未提交的改动,所以严格只读。

## 测试心态
你是测试部门,来"找问题"的,不是来证明它能跑的。
对每条用例主动构造:异常输入、边界值、越权访问、并发竞态。默认怀疑实现有 bug。
判 PASS 必须给真实运行结果 / 代码 file:line 证据,不许凭感觉。

## 测试环境与前置
- 后端测试用 unittest,禁止 pytest(CI 不装 pytest,import pytest 会 CI 红)。
  跑法:`python -m unittest discover -s tests -p "test_*.py"`,或按目录/单文件跑。
- 真账号 E2E:本地 uvicorn 接真 Supabase + 本地反代 + 真浏览器 Playwright(headless 也要 getComputedStyle)。
  账号 pearnly_e2e_1/_2/_3(密码在 pearnly_test_accounts.txt,只取首段非空白串)。
  一般 e2e_3 跑全链路、e2e_1/_2 做跨租户隔离对照。
- UI 验证铁律:真浏览器抓 isVisible + getComputedStyle + 截图 才算数;grep 类名 / 查 MODAL=true 不算。
- 前端是 immutable 缓存:本地反代/无缓存能过 ≠ 真用户拿得到;报告注明验的是哪个 bundle 版本。

## 测试分层(测试金字塔,逐层覆盖)
- L1 单元/契约:把相关 tests/unit/test_*.py 全跑一遍,记录通过率。每个功能必须 ≥1 测试;无覆盖记缺陷「缺测试覆盖」。
- L2 集成(路由):每端点覆盖 正常200 / 缺参422 / 越权401-403 / 不存在404 / 业务冲突409;
  校验统一返回信封格式、错误码不外泄堆栈。
- L3 E2E(真账号+真浏览器):按业务流逐条跑,每条截图存档。

## 必测的横切维度(每个功能都要过这 13 项)
1. 功能正确:正常路径 happy path 全走通。
2. 边界值:0 / 负数 / 空 / 超长 / 超大金额 / 最大最小。
3. 异常输入:非法字符、坏文件、缺字段、错类型 → 应优雅报错(422/明确提示),不能 500/崩。
4. 多租户 + 套账隔离:RLS 在 prod 不强制(postgres BYPASSRLS),真隔离靠应用层每句 WHERE tenant_id。
   主动构造跨租户 / 跨套账(workspace_client_id)越权读写,全部必须失败。
   区分两个"客户":workspace_client_id(套账=硬边界) vs client_id(买方=内部维度),别混。
5. 权限/角色 RBAC:owner / 被邀请成员 / 收银员 各自能做什么,越权调用应 403。
6. 安全:SQL 全参数化(构造 引号 / ; DROP / % 注入尝试)、列白名单、鉴权图片要 Bearer 不能直接当 src。
7. 钱:全链路 Decimal,无 float 漂移;价内/价外 VAT、找零、折扣精度对齐。
8. 并发竞态:连号 numbering 并发不重复不跳号(FOR UPDATE);同一资源两端同时操作(如同桌台同时埋单、
   同终端同时下单)行为正确;client_uuid 幂等不重复入账。
9. 时间:存 UTC。
10. i18n:四语 th/en/zh/ja 齐全,无缺键 / 串语言 / 乱码 / 撑破布局。
11. 四态 UI:每个列表/详情都要真触发并截图 loading / empty / error / success 四态,不能只有成功态。
12. 性能:无 N+1、无笛卡尔积放大,关键查询可 EXPLAIN 抽查。
13. 回归:跑全量后端测试,确认新功能没打坏既有模块。

## 真实 UI 实测(逐屏逐按钮 · 强制真浏览器)
原则:UI 判 PASS 只认 真浏览器 isVisible + getComputedStyle + 截图。
每屏必做:
1. 逐按钮真点:屏上每个按钮/切换/链接真点一遍,确认有正确反应(不是死按钮、点了无反应、报错)。
2. 四态都真触发并截图:loading / empty(无数据不能白屏) / error(造断网或 500) / success。
3. 表单边界:必填留空、超长、非法字符、负数/0、提交后状态正确。
4. 弹窗/遮罩:能打开能关、ESC/点遮罩行为正确、不残留把整屏挡死。
5. i18n:切四语每屏文案正确、不撑破布局。
6. 视觉对照:对照设计快照做保真比对(关键元素颜色如按钮蓝 #2563EB、间距、对齐与设计稿一致)。
产出:每屏一组截图 + 一张「逐按钮点击结果表」(屏/按钮/预期/实际/截图)。

## 迁移测试(老客户"缺格子"专项 · Blocker 级)
背景:prod 部署只重启进程、不自动跑 alembic upgrade。新表/新列在 prod 生效靠
①手动 alembic upgrade ②代码里 ensure_*() 运行时兜底建表。两条都有盲区,本地用干净新库测不出来,
历史反复在 prod 暴雷。本节专门戳盲区(只检测不修)。每条用独立测试库,结尾 rollback。
① 老客户缺列盲区(最重要):造"表已存在但故意缺本次新列/新表"的旧结构库(模拟老租户),跑迁移+触发 ensure_*,
   断言本次所有新表/列/约束/默认值在老库里真的出现且正确;特别戳 CREATE TABLE IF NOT EXISTS 对
   "表已在只缺列"是否能补上列,补不上记 Blocker。
② 幂等:迁移 + ensure_* 连跑两遍,第二遍不报错/不重复建/不改坏数据。
③ alembic vs ensure_* 一致性:同表两套定义逐列比对(名/类型/约束/默认值),不一致记 Blocker。
④ 数据保全:迁移不丢老数据、不破坏既有行;带 tenant_id/workspace_client_id 回填的迁移验回填正确且不串租户。
⑤ 回滚:本次 alembic downgrade() 能干净执行、不报错、不误删无关数据。
⑥ "忘手动 upgrade"演练:在"只重启不 upgrade"前提下启动应用,逐一确认本次每个新列 要么有 ensure_* 兜底、
   要么明确标注必须手动 upgrade;任何"既没兜底又依赖手动 upgrade"的新列=上线即 500,记 Blocker 并列清单。

## 守门闸(只验证、不修复,结果写进报告)
size(<500行)/ ratchet / ai-smell(注释 emoji/console.log 残留)/ ui-consistency(按钮蓝 #2563EB、新 UI 用 .modal 不用 .drawer)/
no-pytest / visual-fidelity 六道。可跑 scripts/git-hooks/pre-push 看退出码(别信终端回显,曾有显示故障藏红)。

## 缺陷报告格式(每问题一条)
ID / 模块 / 子流程 / 严重级(Blocker/Critical/Major/Minor) / 精确复现步骤(账号·输入·端点) /
期望 vs 实际(贴真实输出·截图路径·代码 file:line) / 根因 / 建议修复方向(只描述不动手)。
严重级:Blocker=数据错乱/越权/钱算错/连号重复/老客户上线即崩;Critical=主流程不可用;
Major=边界异常缺失;Minor=文案/四态/i18n 瑕疵。

## 验收标准(Exit Criteria)
- 现有全量后端测试是否全绿(列出红的)。
- 核心 E2E 是否全部跑通 + 截图存档。
- Blocker / Critical 数量(可上线要求:0 个未关闭)。
- 隔离 / 权限 / 钱精度 / 连号并发 / 迁移老客户 五项专项结果。
- 六道守门闸结果。

## 交付物
1) 测试报告:覆盖率(跑了哪些用例、PASS/FAIL 统计)、截图清单。
2) 缺陷清单:按严重级排序,附复现与证据。
3) 「建议新增的测试」清单:只描述应补什么,不要真建文件。
4) 一句话结论:是否达到可上线标准;若否,列出阻塞项。

---

# Part 2 · 本次专项:POS 模块 + 平台业态套餐切换模块

> 先读基线文档对齐预期,再按 L1→L2→L3 推进,Part 1 的 13 项横切维度 + UI 实测 + 迁移测试 全部套用。

## 先读(对齐预期)
- POS:docs/pos/10-acceptance.md, 06-error-codes.md, 07-ui-states.md, 05-button-action-matrix.md,
  08-offline-sync-adr.md, 12-visual-fidelity-gate.md
- 平台:docs/platform-onboarding/01-module-gating-map.md, 02-business-presets.md, 03-api-contracts.md, 04-ui-contracts.md

## 模块 A:POS(库存 + 收银 + 餐厅 + 收银台接入)
代码:
- 库存:routes/inventory_routes.py, inventory_report_routes.py, products_routes.py
- 收银(零售/药房):routes/pos_auth_routes.py, pos_sales_routes.py, pos_report_routes.py
  前端 static/pos/:pos.js, pos-cashier.js, pos-data.js, pos-ops.js, pos-totals.js, pos-offline.js, pos-sw.js
- 餐厅:routes/pos_restaurant_routes.py, pos_restaurant_admin_routes.py
  前端:static/pos/pos-restaurant.js, pos-restaurant-ops.js, pos-restaurant.css
- 收款设置/桌台后台/收银员管理:routes/pos_payment_routes.py, pos_modules_routes.py
已有单测(先跑):tests/unit/test_pos_*.py(auth/sales/sync/upgrade/report/permission_gate/
inventory_sql_isolation/numbering/local_totals/catalog_uuid_cast/store_binding/payment_settings/onboarding*)

业务流用例(每流程套 Part 1 的 正常/边界/异常/越权 四类):
- A1 收银台接入:店铺码绑定签长期店铺令牌→PIN 卖货;错码/重复绑定/reset 后旧令牌吊销/任意设备 PIN/
  错 PIN/停用收银员不能登录/未开班不能卖货;A 店绝不能看到 B 店数据(e2e_1 vs e2e_2)。
- A2 开班/小票:开班(含默认终端回落,曾把 422 包成「商品行有误」,重点回归)/交班减找零/建小票/退货/作废/
  取单(QR)/热敏渲染;并发同终端连号不重复;client_uuid 幂等不双扣;价内外 VAT + 找零精度。
- A3 库存:入库/盘点/FEFO 顺序/近效期/进销存周转报表四态;
  重点回归历史 bug:catalog 的 ANY(%s) 必须 ::uuid[]、多 join 笛卡尔积翻倍库存、apply_stock_delta 必带 tenant_id;
  库存写 require_owner,收银员调用应 403。
- A4 餐厅:区域/桌台 CRUD、批量加桌、停用=is_active(无物理删)、桌台状态机 free/seat/cook/bill 派生零漂移;
  埋单 整桌/按项/AA + 服务费+VAT 单次取整对齐稿;菜品=成品不扣库存(验埋单不误走扣减);
  并发:两端同时埋同一桌行为正确。
- A5 离线 PWA:断网下外壳可用 + 本地 pos-totals 算价与后端 totals.py 一致 + 下单进 outbox;
  恢复后批量同步逐张 SAVEPOINT 隔离、单张失败不污染同批、幂等不重复入账。
- A6 税票/报表:小票升税票复用连号/冻结/不可改、金额反解不重算、仅 already_upgraded/tax_id_invalid 两种拒绝;
  销售报表四态、每分区独立查询防笛卡尔积(2 行 2 支付增量断言)。

UI 实测覆盖屏:登录/绑定屏、收银主屏(商品网格/购物车/结算)、开班/交班、退货/作废/取单、税票升级、
销售报表、餐厅 桌台总览/点单/KOT 厨房/埋单弹窗、库存后台各屏、收款设置、收银员管理、桌台后台。

## 模块 B:平台业态套餐切换
代码:routes/modules_routes.py, me_routes.py, auth_me_routes.py;
前端 src/home 下 module-nav / onboarding-business / module-settings(自行定位)。

业务流用例:
- B1 注册选业态自动配模块:首进自动弹(哨兵)、6 业态预设(firm/retail/pharmacy/restaurant/service/b2b)
  与 02-business-presets.md 完全一致;哨兵消费后不再弹、老租户无哨兵永不弹且模块默认全开不被改写。
- B2 模块开关:PUT /api/me/modules/{key} 关=隐藏不删(数据保留再开恢复)、导航实时增减(真浏览器验入口出现/消失)、
  切业态更新可见集;require_account_owner(invited_by is None),被邀请成员调用应 403。
- B3 导航数据驱动:完全由 /api/me/modules 驱动、未开通模块入口不渲染;POS/inventory 默认关→未开通看不到入口。

UI 实测覆盖屏:注册业态选择弹窗、设置模块开关页、切业态后导航变化。

## 本次迁移测试对象(套 Part 1 迁移测试六条)
- alembic:alembic/versions/0021_tenant_modules ~ 0029_pos_payment_settings
- ensure_*:services/pos/*(payment_settings/cashier/store_binding/sales_store/restaurant/schema)、
  services/modules/store.py、services/workspace/store.py、services/inventory/store.py、services/products/units.py
- 已有迁移测试雏形:tests/unit/test_pos_core_migration.py、test_pos_sales_migration.py、
  test_pos_perf_indexes_migration.py、test_field_overrides_migration.py

## 本次核查发现(测试前必读 · 由源码核查得出 · 别误报)
1. mock 兜底层自动关:static/pos/pos-data.js 有 mock 回落,但 `POS.allowMock()=!state.workspaceClientId`——
   绑了真账号/真租户后 mock 自动关死,后端缺路由一律走诚实失败,不渲染假数据。
   ⇒ 必须用【真账号(已绑套账/workspaceClientId)】测,不要用未绑的纯预览模式测,否则看到的是 mock 假数据=假绿。
2. 交班屏「关班前」实时汇总是诚实空态,不是 bug:`GET /api/pos/shifts/{id}/summary` 后端尚未实现
   (现仅 /shifts/open、/shifts/{id}/close),前端识别接口缺失返 null→屏5 显空态;真汇总数字在【关班(close)】那一刻返回。
   ⇒ 测交班:验"关班"返回的 summary 正确即可;关班前的空态记为「已知延后(Minor)」,不要记成 Blocker。
3. 按设计延后、不在测试范围(不要记成缺陷):刷卡真实在线扣款(Omise/2C2P 网关,现刷卡=记账方式不真扣)、
   B7 称重/会员积分/批发账期。

## UI 实测已知坑(别被假失败骗,不要记成缺陷)
- 跑部分屏前先设 localStorage pearnly_work_mode=personal,否则 #ws-modal 全屏遮罩会让 Playwright
  点不动→一堆假失败(测试环境问题,非产品 bug)。
- headless getComputedStyle 偶有探针误报(曾误判样式没加载),拿不准的用截图人工复核,别单凭探针下结论。

---

## 给非技术使用者的一句话
这份文档做完后,覆盖了:① 看不见的(钱算错/越权/老客户上线崩)→ 代码+迁移测试;
② 看得见的(屏/按钮/四态/语言)→ 逐屏真点 UI 实测。两条腿都硬,基本堵住"上线后冒隐藏问题"的主要来源。
以后任何新功能做完,直接复用 Part 1 + 照 Part 2 的写法填本功能的用例即可。
