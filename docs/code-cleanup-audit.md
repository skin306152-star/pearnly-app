# Pearnly 代码屎山审计报告

> **审计日期**:2026-05-18
> **项目状态**:生产线上 v118.33.13.6(per claude-mem),开发本地分支同步
> **审计窗口**:本会话(代码清理专线)
> **状态**:🟡 阶段 1 完成 — 等待用户审阅

---

## 0. 审计元数据

### 0.1 审计范围

**已审计**:
- 项目根目录 34 个 `.py` 文件(共约 36k 行)
- 5 个根目录前端文件:`home.html`、`home.css`、`home.js`、`login.html`、`pearnly_nav_prototype_final.html`
- `static/admin/` 4 个文件(admin SPA)
- `static/version-banner.js`
- `mrerp_bridge/` 2 个文件
- 根目录依赖文件 / 配置文件

**显式排除**:
- `.git/`、`__pycache__/`、`_pkg/`、`_pkg_tmpstatic/`(空)— 运行时/版控产物
- `CLAUDE.md/` 目录下的 10 个 .md 项目文档 — 不是代码
- `docs/` 下的 .md 文档 — 不是代码
- 根目录 3 个 `deploy_v*.tar.gz/zip` 部署包(已 gitignore,见后述)
- 数据库 SQL 迁移文件 — 不在本次清理类目内

### 0.2 与现有 TECH_DEBT.md 的边界

项目已有 `CLAUDE.md/TECH_DEBT.md`(2026-05-15 启动),覆盖了 **前端三大件**(home.js / home.css / home.html)的头部问题:
- home.js 1346 KB / 30071 行
- `deleteEndpoint` 12694 行函数
- `closeSettingsModal` 2386 行函数
- 106 处空 catch(本审计重新计数 = 118 处,详见 §3.4)
- 713 处 `// v##.x` 注释(重新计数 = 648 处)
- 209 处 `window.*` 全局赋值
- 55 处 `var` 残留
- 26 处 `'use strict'` 不一致
- 0 个 UI 测试

**本审计的定位**:
- ❌ **不重复** TECH_DEBT.md 已记录的前端三大件结构问题(在 §4.1 引用,不再展开)
- ✅ **重点补充** TECH_DEBT.md 未覆盖的部分:Python 后端 34 个模块、Python 空 catch、孤立的 .py / .html 文件、备份残留、MR.ERP 迁移残留、strangler 进行中的模块对、OCR 引擎并存等
- ✅ **重新核对** TECH_DEBT.md 中的几个数字(轻度漂移已记录,见 §4.1)

### 0.3 关键约束(影响所有评级)

本项目使用 **绞杀者模式(Strangler Pattern)**:老代码不动,等新代码完全替换完才删。因此**很多"看起来没人用"的代码实际是"待替换"** — 这类一律标 🟡 不标 🟢。

OCR 模块正在另一个会话(`docs/ocr-migration/`)进行架构迁移(Vision API + Gemini 三层兜底)。涉及文件:`gemini_engine.py`、`nvidia_engine.py`、`typhoon_engine.py`、`vision_engine.py`、`ocr_engine.py`、`engine_chain.py`。这些文件在本审计中**只列出,不评级**(标 ⚪),由 OCR 会话处理。

---

## 1. 总览统计

### 1.1 按风险等级

| 等级 | 项数 | 说明 |
|---|---|---|
| 🟢 安全清理 | 8 | 5 个 `_` 私函数 + 1 个备份 .py + 1 个空目录 + 1 类部署包(3 文件) |
| 🟡 需要确认 | 20 | 含阶段 1.5 新发现的 4 个幽灵模块跨仓库不一致问题(🟡-15.5) |
| 🔴 谨慎处理 | 3 | 涉及核心或设计基准,本会话不处理 |
| ⚪ 不评估 | 8 | OCR 迁移热区 / 前端已在 TECH_DEBT |

### 1.2 按问题类型

| 类型 | 🟢 | 🟡 | 🔴 | ⚪ | 备注 |
|---|---|---|---|---|---|
| 1. 死代码 | 7 | 8 | 0 | 2 | 🟢:5 私函数 + 1 备份 .py + 1 空目录 / 🟡 含 quality_check 模块 |
| 2. 重复代码 | 0 | 4 | 0 | 0 | 备份 .py 已计入"死代码" / strangler 对(bank_reconcile vs v2、vat_excel_export vs exporter)、两个 HANDOVER 计入"重复" |
| 3. 过时代码 | 1 | 4 | 1 | 0 | 🟢 部署包 1 类 / 🟡 MR.ERP 残留 + 各种"老/废弃"注释 / 🔴 设计 prototype |
| 4. 可疑代码 | 0 | 3 | 2 | 6 | 🟡 ~175 处空 catch + 版本注释 + 长函数未深扫 / 🔴 OCR 引擎 + 多租户兜底 |
| 5. 未用依赖 | — | — | — | — | **N/A** — 项目无 requirements / pyproject / package.json |
| **合计** | **8** | **19** | **3** | **8** | |

---

## 2. 🟢 安全清理(5 项)

### 🟢-1 `excel_export_v108_backup.py`(167 行)
- **位置**:`D:\Users\Skin\Desktop\pearnly_project\excel_export_v108_backup.py`
- **类型**:死代码 — 文件级未引用
- **证据**:
  - `diff excel_export.py excel_export_v108_backup.py` → 字节级完全相同
  - 全项目 grep `excel_export_v108_backup` → 0 引用
  - 命名直白:`_v108_backup` 后缀
- **建议处理方式**:直接删除文件
- **风险**:零

### 🟢-2 根目录 `_pkg_tmpstatic/` 空目录
- **位置**:`D:\Users\Skin\Desktop\pearnly_project\_pkg_tmpstatic\`
- **类型**:死代码 — 空目录
- **证据**:`ls` 结果为空
- **建议处理方式**:`rmdir`
- **风险**:零(.gitignore 未覆盖此目录名,但目录为空)

### 🟢-3 根目录 3 个旧部署包
- **位置**:
  - `deploy_v118.32.5.5.35.tar.gz`(165 KB,May 16)
  - `deploy_v118.32.5.5.36.tar.gz`(536 KB,May 17)
  - `deploy_v11841137.zip`(542 KB,May 17)
- **类型**:过时代码 — 旧部署产物
- **证据**:
  - `.gitignore` 已忽略 `*.tar.gz` 和 `deploy_v*.tar.gz`
  - 当前生产 v118.33.13.6,这些包都是 v118.32.x → 旧
  - 项目已切换到 git push 部署流程(CLAUDE.md §部署),tar.gz 仅作 emergency fallback
- **建议处理方式**:删除磁盘文件(已 gitignore,不会影响仓库)
- **风险**:零(emergency fallback 流程不依赖具体某个旧包)

### 🟢-4 `app.py:7020` `_gen_temp_password`(单函数,约 6 行)
- **位置**:`app.py:7020-?`
- **类型**:死代码 — 私函数零引用
- **证据**:全项目 grep `_gen_temp_password` 只命中定义行,**零调用**
- **建议处理方式**:删除函数
- **风险**:零(`_` 前缀私函数 + 无引用)

### 🟢-5 `bank_recon_v2.py:1996` `_build_index`(单函数)
- **位置**:`bank_recon_v2.py:1996`
- **类型**:死代码 — 私函数零引用(银行对账 v2 内部辅助)
- **证据**:全项目 grep `_build_index` 只命中定义行
- **建议处理方式**:删除函数
- **风险**:零

### 🟢-6 `recon_routes.py:1161` `_user_api_key`(单函数)
- **位置**:`recon_routes.py:1161`
- **类型**:死代码 — 私函数零引用
- **证据**:全项目 grep 只命中定义行
- **建议处理方式**:删除函数
- **风险**:零

### 🟢-7 `vat_excel_export.py:538` `_is_image_ext`(单函数)
- **位置**:`vat_excel_export.py:538`
- **类型**:死代码 — 私函数零引用
- **证据**:全项目 grep 只命中定义行
- **建议处理方式**:删除函数
- **风险**:零

### 🟢-8 `vat_excel_exporter.py:127` `_diff_field_match`(单函数)
- **位置**:`vat_excel_exporter.py:127`
- **类型**:死代码 — 私函数零引用
- **证据**:全项目 grep 只命中定义行
- **建议处理方式**:删除函数
- **风险**:零

> **修正**:engine_chain.py 改归 🟡-1(OCR 领域),🟢 总数 → 4。


---

## 3. 🟡 需要确认(逐项展开)

### 3.1 死代码 / 未引用类

#### 🟡-0 `quality_check.py`(95 行,整个模块)
- **位置**:`quality_check.py`(根目录)
- **类型**:死代码候选 — 整模块零外部引用
- **证据**:
  - `grep -E "quality_check|assess_page_quality|assess_pages_quality|_looks_like_thai_invoice|_is_blank"` 全项目结果**只命中模块内部**,无任何 import/from/调用
  - 模块功能:OCR 输出字段质量评估(判断 OCR 是否抽取完整、是否像泰国发票)
- **不确定点**:OCR 迁移方案 `docs/ocr-migration/README.md` §7.2 规划了新的 `services/ocr/validators.py` 做同类工作 → 这个旧 validator **可能是被绕过的设计**,等新 OCR 上线后才能确认彻底无用
- **建议处理方式**:**留给 OCR 迁移会话**统一处置(降级到 🟡 非 🟢 的原因:虽然零引用,但 OCR 领域)
- **风险**:低(零引用)但分类为 OCR 领域

#### 🟡-1 `engine_chain.py`(302 行,整个模块)
- **位置**:`engine_chain.py`
- **类型**:死代码 — 模块零外部 import
- **证据**:
  - 全项目 `from engine_chain` / `import engine_chain` 均 0 结果
  - 内部 import `typhoon_engine`、`nvidia_engine`、`gemini_engine`,本身是 OCR 编排器
  - 但 `app.py:2186` 用 `"engine_chain"` 作为返回字典的字符串 key(纯字符串,不是模块引用)
- **不确定点**:OCR 编排器可能在 OCR 迁移规划中,或已被绕过,本会话**不下删除决定**
- **建议处理方式**:**留给 OCR 迁移会话**统一处置
- **风险**:中(OCR 领域)

#### 🟡-2 `erp_push.py:199` `push_mr_erp` stub
- **位置**:`erp_push.py:199-205`
- **类型**:死代码 — 函数永远返回未实现
- **证据**:
  ```python
  def push_mr_erp(endpoint_config, payload):
      return False, 0, "mr_erp adapter not implemented yet · 请先用 webhook 适配器"
  ```
  - 注册在 `ADAPTER_REGISTRY["mr_erp"]`(line 223)
  - `app.py:3126, 3185` 校验 `req.adapter not in _erp.ADAPTER_REGISTRY`,所以 "mr_erp" 是**可达分支**,只是永远失败
  - CLAUDE.md 提到 "MR.ERP 搁置等 bridge API · 2026-05-14 全删" — 但这个 stub 没清
- **不确定点**:DB 里可能有用户 endpoint 残留 `adapter="mr_erp"`,如直接删可能让那些 endpoint 校验失败 → 行为变化
- **建议处理方式**:查 DB 中是否有 `erp_endpoints WHERE adapter='mr_erp'`,无则可删函数 + 注册表 entry + 三处校验逻辑
- **风险**:低(用户层只是看到不同错误信息)

#### 🟡-3 `bank_reconcile.py`(905 行,旧版银行对账)
- **位置**:`bank_reconcile.py` 整个文件
- **类型**:死代码候选 — strangler 进行中
- **证据**:
  - 仍被 `app.py:3695` 和 `app.py:3821` import(`import bank_reconcile as br`)
  - 同时有新版 `bank_recon_v2.py`(3137 行)
  - CLAUDE.md 显示银行对账 v118.26.x 已暂停,但 v118.33.13.x 是最新 bank_recon_v2 系列
- **不确定点**:旧版可能还在某些 route 兜底用;两处 app.py 引用具体走什么路径
- **建议处理方式**:查看 app.py:3695 / 3821 上下文,确认是否为完全可绕过的兜底路径,然后讨论
- **风险**:中(影响银行对账旧路径用户)

#### 🟡-4 `vat_excel_export.py`(1497 行)vs `vat_excel_exporter.py`(391 行)
- **位置**:两个文件均在根目录
- **类型**:重复代码候选 — 功能重叠
- **证据**:
  - `vat_excel_export.py`:v118.32.4.10.1,"Excel 公式对账模块"(AI 抽字段 + Excel 公式让用户核对),被 `vat_excel_routes.py:19` 用
  - `vat_excel_exporter.py`:v118.32.x,"Korn 模板克隆 Excel 导出",被 `recon_routes.py:21` 用(`export_recon_task`)
  - 文件名 99% 相似(`_export` vs `_exporter`),实际是两种不同的 Excel 导出策略
  - 两者都在被使用 → 不是单纯重复,可能是策略并存或 strangler 进行中
- **不确定点**:Zihao 是否在 A/B 测试两种导出?还是 vat_excel_exporter.py 是被 vat_excel_export.py 替代但未完成?
- **建议处理方式**:用户确认两个模块的关系/未来计划,**不要自动判定哪个是死的**
- **风险**:高(都是 VAT 模块核心)

#### 🟡-5 `pearnly_nav_prototype_final.html`(139 KB)
- **位置**:`pearnly_nav_prototype_final.html`(根目录)
- **类型**:可疑 — 是代码还是设计稿?
- **证据**:
  - CLAUDE.md 钦定"唯一基准文件 · Zihao 提供 + 头像菜单升级版"
  - 仅在 `home.js:31373` 一行注释中被引用("视觉基准:pearnly_nav_prototype_final.html")
  - 不被 app.py 作为路由 serve,不是生产代码
  - 实际是**设计参考文件**,放在根目录占了 139 KB
- **不确定点**:是否需要移到 `docs/design/` 或 `static/_reference/` 等专门目录,而不是混在 .py 源码堆里
- **建议处理方式**:讨论是否归档到 docs/,**绝对不删**(CLAUDE.md 钦定基准)
- **风险**:零(只是移动,不删除)
- **修正**:此项实际应归 🔴(钦定基准) — 见 §4 🔴 区

#### 🟡-6 `app.py:4348` 自报死代码 PEARNLY_ADMIN_MODE
- **位置**:`home.js:10565`、`10590`、`10602`、`11607`(共 4 处)
- **类型**:死代码 — 由 app.py 注释自报
- **证据**:
  - `app.py:4348` 注释明文写"老 PEARNLY_ADMIN_MODE 老逻辑(home.js L10879+)从此 dead code · v118.45 可清"
  - NAV-IA Phase 8 已完成 admin SPA 独立(v118.44.0+),旧 admin mode 逻辑理论上不再触发
  - 但 `static/admin/admin.html:12` 仍设 `window.PEARNLY_ADMIN_MODE = true` → 新 admin SPA **也**用这个 flag(可能是为兼容某些 home.js 全局逻辑)
- **不确定点**:
  - app.py 注释说的"L10879+"位置不准(那里是 `toggleEmployeeActive` 团队管理函数)
  - 真正的 PEARNLY_ADMIN_MODE 处理在 home.js:10565 附近
  - 新 admin SPA 是否真的不需要 home.js 的 PEARNLY_ADMIN_MODE 分支
- **建议处理方式**:这是 NAV-IA 窗口该处理的事,**本会话不动**;此处仅记录线索给 NAV-IA 接手 agent
- **风险**:中(admin 模式入口)

#### 🟡-7 `static/version-banner.js` 中的 `// v##.x` 注释(4 处)
- **位置**:`static/version-banner.js`(共 4 处版本注释)
- **类型**:过时注释(噪音)
- **证据**:`grep "^\s*// v\d+\."` 命中 4 处
- **建议处理方式**:阶段 3 批量清理(不是本审计该决定的)
- **风险**:零

#### 🟡-8 `MODULE_EXPENSE_PRD_v2.md`(在 CLAUDE.md/ 目录,不是代码)
- **位置**:`CLAUDE.md\MODULE_EXPENSE_PRD_v2.md`
- **类型**:过时文档 — 文件名带 `_v2` 暗示存在 v1
- **证据**:`find` 未找到对应的 `MODULE_EXPENSE_PRD.md`(v1)
- **建议处理方式**:不在本审计代码清理范围,但记录给文档治理者
- **风险**:零(只是文件名约定)

### 3.2 过时代码类

#### 🟡-9 `app.py` 中 MR.ERP 残留 8 处
- **位置**:
  - `app.py:1606` 注释 "MR.ERP 自动推"
  - `app.py:2106` 同上
  - `app.py:3067` `adapter: str = Field(..., description="webhook | mr_erp | flowaccount")` — Pydantic 模型字段描述里仍列 mr_erp
  - `app.py:3328` `# v27.8.1.3 · Xero / MR.ERP 后台自动推`
  - `app.py:3344` `mappings = db.get_mrerp_mappings_bundle(tenant_id)`
  - `app.py:7722, 7733, 8001` MR.ERP 相关导出 / 映射
- **类型**:过时代码 — CLAUDE.md 说 "2026-05-14 全删" 但代码里还在
- **证据**:见上
- **不确定点**:CLAUDE.md 的"全删"是指 ERP 适配器**功能层**全删,还是字面上**所有代码引用**全删?这两个意思差很多
- **建议处理方式**:用户澄清"MR.ERP 全删"的精确含义后决定
- **风险**:中(可能影响某些隐藏路径)

#### ⚠ 已知误名(2026-05-18 阶段 3 任务 B-3 发现)
**`db.get_mrerp_mappings_bundle`** 虽然名字带 `mrerp`,但**实际是给 Xero 集成用的通用 ERP 映射拼装函数**(app.py:3344 自动推 + 7988 手动推 都用它取 `erp_type == "xero"` 的 client mapping)。**绝对不能删**,删了 Xero 立即挂。

**处理决策**(2026-05-18 用户拍板):**保留不动,跳过 rename**。理由:rename 涉及 app.py 多处调用,属"超出范围的改造",优先级低于其他清理。**以后做 schema 重构时统一处理**。

---

#### 🟡-10 `db.py` 中 MR.ERP 7 处(`get_mrerp_mappings_bundle` 等)
- **位置**:`db.py:6049`(SQL 注释)、`db.py:6506, 6528, 6554, 6581`(mrerp 演示映射注入)、`db.py:6621-6635`(`get_mrerp_mappings_bundle` 函数定义)
- **类型**:过时代码 + 死函数(待确认)
- **证据**:`get_mrerp_mappings_bundle` 被 `app.py:3344, 8001` 调用 → **不是死的**,但在"全删"语境下值得审视
- **建议处理方式**:与 🟡-9 一起讨论
- **风险**:中

#### 🟡-11 `bank_recon_v2.py:1327, 1600, 1605` 中 `_parse_gl_mrerp_table`
- **位置**:`bank_recon_v2.py:1327`(函数定义)、`1600, 1605`(调用点)
- **类型**:**这是活的** — Mr.ERP 格式 PDF 解析器,2026-05-18 v118.33.13.4 刚加
- **证据**:claude-mem S207 记录"GL parser rewrite (_parse_gl_mrerp_table)"
- **建议处理方式**:**不动**,只是说明 Mr.ERP 的"全删"不彻底,某些上下文(PDF 解析)仍依赖
- **风险**:不应碰

#### 🟡-12 `app.py` 中各种 "兼容旧前端" / "_legacy_alias" 注释 (~70+ 处)
- **位置**:app.py 中含 `旧|老|废弃|legacy|backup` 的注释 80+ 行(详见 grep 输出)
- **类型**:过时代码 — 历史兼容层
- **证据**:每行注释自报"v0.X 废弃,仅兼容旧前端" / "兼容老用户" 等
- **典型例子**:
  - `app.py:582` IP 限流(v0.8 废弃)
  - `app.py:2182` Typhoon 增援标记(v105 已废弃)
  - `app.py:607` 兼容旧字段(不再使用但前端可能仍引用)
- **不确定点**:具体每条"老前端"指代什么?线上是否还有用户在跑老前端?
- **建议处理方式**:**阶段 4 处理** — 这是典型的 🟡 一项项讨论的代码,不批量
- **风险**:中(每项不同,需逐一评估)

#### 🟡-13 `auth_signup.py:1530` 自报已删但留墓碑
- **位置**:`auth_signup.py:1530-1534`
- **类型**:过时注释 — 墓碑
- **证据**:
  ```python
  # v118.12 · 旧版 admin_list_users / admin_user_detail 已删除
  # 原因:与 app.py:3741 路由冲突 · app.py 版数据更准(JOIN tenants)
  # 详情见 DIAGNOSTIC_v118_12.md 第一节
  # ============================================================
  ```
- **不确定点**:墓碑注释是否仍有教学价值?
- **建议处理方式**:阶段 3 / 4 决定是否清理
- **风险**:零

### 3.3 重复 / 配置类

#### 🟡-14 两个 `HANDOVER_TO_NEXT_WINDOW.md`
- **位置**:
  - 根目录 `HANDOVER_TO_NEXT_WINDOW.md`(29497 字节,May 18 01:50,最新)
  - `CLAUDE.md\HANDOVER_TO_NEXT_WINDOW.md`(19515 字节,May 17 00:56,旧)
- **类型**:重复 + 过时文档
- **证据**:两个文件名相同,大小不同
- **建议处理方式**:用户确认哪个是规范位置后归档/删除另一个
- **风险**:低(项目治理类)

#### 🟡-15 `mrerp_bridge/` 目录(仅 INSTALL.txt + pearnly_bridge.php)
- **位置**:`mrerp_bridge/INSTALL.txt`、`mrerp_bridge/pearnly_bridge.php`
- **类型**:过时代码 — MR.ERP bridge 集成
- **证据**:
  - CLAUDE.md 提到 "MR.ERP 搁置等 bridge API · 2026-05-14 全删"
  - 但目录还在 + 含 PHP 脚本
- **不确定点**:bridge 是部署在 mrerp 客户那边的脚本,可能与本仓库无关只是参考
- **建议处理方式**:用户澄清此目录用途
- **风险**:低(目录占地小)

### 3.4 可疑代码类

#### ✅ 🟡-15.5 **4 个"幽灵模块" — 已解决**(2026-05-18 commit `90c1271`)
> 状态:**已修复**。用户从生产服务器 scp 回 4 个文件 + git commit + push 完成。详见 `docs/startup-check-report.md` §7。
> 原始发现保留如下作为历史记录:

##### 原始发现:4 个"幽灵模块"被 import 但本仓库不存在
- **位置**:
  - `pdf_storage` — `app.py:48`(顶级 · 无 ImportError 保护)+ 1927/2971/2986/3022(调用 `.save_pdf` 等)
  - `pdf_searchable` — `app.py:1916`(try/except 内,可选)
  - `excel_template_th` — `app.py:2223, 2322`(try 块内 · 外层 try except Exception 兜)
  - `xero_pusher` — `app.py:3370, 7803, 7837, 7882, 7949, 8016`(try/except ImportError 全保护)
- **类型**:可疑代码 — 跨"本地仓库 vs 生产服务器"代码不一致
- **证据**:
  - `git log --all --diff-filter=AD -- <这 4 个>.py` → 全部零结果(从未在 git 历史)
  - 最新 deploy_v*.tar.gz / .zip 包内零相关文件
  - 全盘 `find ... -name "<module>*.py"` 零结果
  - `pip show` 全部"Package not found"
  - 但生产 v118.33.13.6 在线 → 服务器必有
- **不确定点**:这是历史遗留(从未纳入 git)还是某次 git 清理误删?需 SSH 服务器核查
- **建议处理方式**:
  - **阶段 2 前置必做**:从服务器 `/opt/mrpilot/` scp 回本地 + git add + commit
  - 否则本机永远起不来,阶段 2 的冒烟测试无法本地跑
  - 详见 `docs/startup-check-report.md` §5
- **风险**:**高** — 这是"本地 ≠ 生产"的危险信号;`pdf_storage` 是顶级无保护 import,如果哪天有人意外用本地版本部署,生产线会瞬间挂掉

#### 🟡-16 Python 空 `except: pass`(57+ 处)
- **位置**:分布如下(grep 多行匹配 `except[^:]*:\s*\n\s*pass\s*$`)
  | 文件 | 数量 |
  |---|---|
  | `app.py` | ~25 |
  | `auth_signup.py` | ~10 |
  | `bank_recon_v2.py` | ~6 |
  | `db.py` | ~5 |
  | `email_ingest.py` | 3 |
  | `gemini_engine.py` | 3 |
  | `nvidia_engine.py` | 2 |
  | `excel_export.py` + 备份 | 2 |
  | `line_client.py`, `ocr_engine.py`, `report_routes.py` | 各 1 |
- **类型**:可疑 — 静默吞错误
- **证据**:TECH_DEBT.md 已记录前端 106 处,本审计补充 Python 后端 57+ 处。**全项目空 catch 总数约 175+ 处**
- **建议处理方式**:CLAUDE.md 已有标准方案("`catch (_) {}` → `catch (e) { logger.error(...) }`"),按 TECH_DEBT.md P0 第 4 项分批清理(每窗口 10-20 处)
- **风险**:中(改完可能让某些原本静默吞的错误暴露出来,需测试)

#### 🟡-17 长函数(Python 后端,未深入)
- **位置**:本审计的 agent 主要扫了"函数/类零引用",未做"函数体长度"统计
- **证据**:已知 app.py 有 283 个函数/类定义(grep `^def|^class|^async def`),平均行数 ~28 行,中位数可能更低;但具体哪些是 >150 行需另行扫描
- **建议处理方式**:阶段 2 安全网建立时,可顺手用 `radon cc` 或 `lizard` 跑一次圈复杂度
- **风险**:零(只是诊断)

#### 🟡-18 静态文件版本注释 `// v##.x`(JS 共 648 处)
- **位置**:
  - `home.js` 644 处
  - `static/version-banner.js` 4 处
- **类型**:过时代码 — 历史考古注释
- **证据**:TECH_DEBT.md §1.1 已列(说 713 处,本次重新计数 648 处,差异可能是部分已清/不同 regex 严格度)
- **建议处理方式**:TECH_DEBT 已归 P2(长期清),本审计不重复处理
- **风险**:零

---

## 4. 🔴 谨慎处理(本会话不动,仅记录)

### 🔴-1 `pearnly_nav_prototype_final.html`(139 KB)
- **位置**:根目录
- **类型**:设计基准文件
- **证据**:CLAUDE.md 钦定 "**唯一基准文件**"
- **建议处理方式**:**不删,不评级**;讨论是否移到 `docs/design/`(可选)
- **风险**:破坏会扰乱整个 NAV-IA 设计基准

### 🔴-2 OCR 引擎 6 个文件(列出但不评级)
- **位置**:`gemini_engine.py`、`nvidia_engine.py`、`typhoon_engine.py`、`vision_engine.py`、`ocr_engine.py`、`engine_chain.py`
- **类型**:OCR 迁移热区
- **证据**:`docs/ocr-migration/` 是另一会话的领地,新架构 = Vision API + Gemini 三层兜底,目标模块 `services/ocr/`(未建)
- **建议处理方式**:**本会话不评级**,等 OCR 会话替换/废弃后再清
- **风险**:OCR 是核心功能,误删会让所有发票识别挂掉
- **备注**:engine_chain.py(零外部 import)虽符合 🟢 字面定义,但因属此类强制降级为 🟡-1

### 🔴-3 旧多租户兜底逻辑(`app.py:1046+`)
- **位置**:`app.py:1046` "以下为老多租户兜底(plan 字段为 NULL 或非标值的极旧用户)"
- **类型**:历史兼容层 — 涉及付费/配额
- **证据**:CLAUDE.md "改影响多客户核心逻辑(OCR / ERP 推送)" 属于需先讨论
- **建议处理方式**:**不在本会话清理范围**,等 plan 系统重构时一起替换
- **风险**:破坏会影响极旧用户登录/配额

---

## 5. ⚪ 不评估(8 项 — OCR 迁移热区 + TECH_DEBT 已覆盖)

### 5.1 OCR 迁移热区(6 个文件)
见 🔴-2,这里只列出但不重复评级:
- ⚪ `gemini_engine.py`(532 行)
- ⚪ `nvidia_engine.py`(270 行)
- ⚪ `typhoon_engine.py`(185 行)
- ⚪ `vision_engine.py`(127 行)
- ⚪ `ocr_engine.py`(230 行)
- ⚪ `engine_chain.py`(302 行)— **降级到 🟡-1**(零外部 import)但仍归 OCR 领域

### 5.2 TECH_DEBT.md 已覆盖
- ⚪ `home.js` 30k 行 / 12694 行的 `deleteEndpoint` / 2386 行 `closeSettingsModal` — 见 TECH_DEBT §1.1
- ⚪ JS 209 处 `window.*` / 55 处 `var` 残留 / 26 处 `'use strict'` 不一致 / 92 处 `console.error/warn` 残留 — 见 TECH_DEBT §1.1

---

## 6. 未审计 / 不能审计

### 6.1 未使用依赖(类目 5)— N/A
- 项目**无** `requirements.txt`、`pyproject.toml`、`Pipfile`、`package.json`、`setup.py`
- 因此无法做"列出但未引用的包"分析
- **建议**:阶段 3 之前先建立 `requirements.txt`(从 import 语句反推),否则将来无法做依赖治理

### 6.2 Python 函数级 dead code(已完成)
- Explore 子代理深度扫描完成,发现:
  - **2 个完整未引用模块**:`quality_check.py`(归 🟡-0)、`excel_export_v108_backup.py`(归 🟢-1)
  - **5 个 `_` 私函数零引用**:已归 🟢-4 到 🟢-8
- agent 同时确认:`archive.py`、`field_comparator.py`、`reconciliation_matcher.py`、`vat_ai_analyzer.py` 所有函数都活的,不入清单
- 路由处理器(`@router.get` / `@app.post` 装饰器自动注册的)未误判为死代码

### 6.3 未深扫的区域
- `home.html`(361 KB)— 仅扫了头部 30 行
- `home.css`(434 KB)— 仅看大小,未审计具体规则
- `login.html`(241 KB)— 完全未审计
- `static/admin/admin.js`(76 KB)— 仅记录存在,未审计内容
- 数据库 SQL 迁移文件(`migration_*.sql`)— 不在代码清理类目内
- `auth_signup.py`、`db.py` 等大文件的逻辑层重复 — agent 会覆盖一部分,但深度有限

---

## 7. 工具与方法说明

### 7.1 用到的扫描
| 检查项 | 方法 | 命中数 |
|---|---|---|
| TODO/FIXME/HACK/XXX (Python) | grep | 2 |
| TODO/FIXME/HACK/XXX (JS) | grep | 0 |
| @deprecated / 废弃 / legacy (Python) | grep | 7 标记 + 70+ 注释 |
| 空 except: pass (Python) | grep multiline | 57+ |
| 空 catch (e/_) {} (JS) | grep | 118 |
| `// v##.x` 注释 (JS) | grep | 648 |
| 文件字节比对 (excel_export 系列) | diff | 完全相同 |
| 模块 import 引用图 | grep `from X` / `import X` | 见 §3 |
| 函数级 dead code | Explore agent(已完成) | 2 模块 + 5 私函数 |

### 7.2 限制
- 本审计**没有**:跑 ruff/pyflakes/vulture 等静态工具(项目无配置)
- 本审计**没有**:运行测试或动态追踪(项目无测试)
- 本审计**没有**:深扫前端 1.76MB home.js(TECH_DEBT 已覆盖主要问题)

---

## 8. 后续阶段建议(供用户决策)

> 本审计**不做优先级排序、不做"先做哪个"建议**,以下仅列出阶段 2/3/4 的衔接点。

- **阶段 2(安全网)** 必要前置:本审计 §6.1 提到项目无 requirements.txt,可能影响测试环境搭建
- **阶段 3(只清 🟢)** 候选清单:本审计 §2 的 4 项(扣除 engine_chain)
- **阶段 4(逐项 🟡)** 候选清单:本审计 §3 的 18 项,**每项都要先讨论再动**

---

*本报告 v1.2 — 由本会话生成于 2026-05-18*
*v1.1 改动:已合并 Python 函数级 dead code agent 结果(+5 私函数到 🟢,+quality_check 模块到 🟡-0)*
*v1.2 改动:阶段 1.5 启动检查新发现 4 个幽灵模块(pdf_storage / pdf_searchable / excel_template_th / xero_pusher)被 import 但不在 git → 🟡-15.5,详见 `docs/startup-check-report.md`*
