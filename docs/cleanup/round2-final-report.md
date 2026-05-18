# Pearnly 屎山清理 Round 2 · 收尾报告

> **会话日期**:2026-05-18
> **起始版本**:`c46b20b`(今天 OCR 会话 Phase 3.3 收尾)
> **收尾版本**:`62c851a`(本会话最后一次 commit · 待 push)
> **工作方式**:用户授权激进 · 我自主判断 · 中途零汇报
> **OCR 禁区**:全程遵守(services/ocr/、OCR 接入点、OCR cost 函数、/api/health、pdf_utils.py)

---

## 1. 总账(大白话版)

- **commit 数**:6 个
- **代码净删除**:**约 96 行**(主要是删了一个没人用的 OCR 旧验证模块)
- **新增工具/脚本**:1 个长期可用的"启动检查"脚本(151 行,以后每个会话起手都能用)
- **新增文档**:2 篇(本份 + 中途进度记录)

**用大白话总结**:
- 删了 1 个完整没人用的"OCR 字段质量打分"模块(今天 OCR 升级完后变成孤儿)
- 加了 1 个**自动检查脚本**(以后能一键检查"代码里 import 的东西是不是都装了/存在"——这是 Round 1 救命用的小工具,现在永久放进项目)
- 给 2 处"出错但被吞掉"的代码加了日志(将来出问题能看到原因)
- 删了 1 行过时的"墓碑注释"(代码已死,注释也清掉)
- 整理 `.gitignore`(防止 OCR 测试用的真发票数据不小心被推到 GitHub)
- 写了一份"调研报告"说明哪些事情**不能由我自己做**(下面第 3 节)

---

## 2. 每个 commit 干了啥(给你存档用)

| 序 | Commit | 类型 | 一句话说明 |
|---|---|---|---|
| 1 | `1567135` | 🟢 防护 | `.gitignore` 补 4 条规则,把 OCR 测试结果的真发票数据挡在 git 外面 |
| 2 | `e478e69` | 🟢 工具 | 把 Round 1 临时写的"启动检查"脚本搬到 `scripts/check_imports.py`,加 `--quiet` 模式 + 退出码,以后 CI 能用 |
| 3 | `b28f1a5` | 🔄 改善 | `line_client.py` + `report_routes.py` 两处出错被吞掉的代码,按规则一处加注释一处加 warning 日志 |
| 4 | `a284d9b` | 🟢 删除 | 删整个 `quality_check.py`(95 行 · 今天 OCR 升级后彻底没人调用) |
| 5 | `8cf03fe` | 📄 文档 | 中途进度记录 `round2-progress.md` |
| 6 | `62c851a` | 🟢 注释 | 删掉 `app.py` 里 1 行明确写"v118.45 可清"的过时墓碑注释 |

---

## 3. 我**没有动**的事 + 理由(供你审/Round 3 决策)

### 3.1 三件大事保持原样

#### 🛑 银行对账老模块 `bank_reconcile.py`(905 行)
**事实**:你之前以为"前端可能不再调用这个老接口了"。我去前端代码里搜了一遍,发现 `home.js` 里 **15+ 处** 真的还在调用这个老接口的各种功能——对账中心首页、上传银行流水、查 session 列表、看交易候选、手动覆写匹配……前端整个"对账中心"功能还在跑老路径。
**结论**:这**不是死代码**,是活着的功能,前端还在大量用。Round 1 早就有调研报告(`docs/cleanup/bank-reconcile-migration.md`)警告过"这是一整套老体系不是孤立文件"。**绝对不能删**。
**Round 3 怎么办**:如果你真想砍掉它,得先做一个事:决定**新对账中心要走什么接口**,把前端 home.js 那 15 处调用全部改写到新接口,验证完业务正常,再回头一刀切删老模块 + 老路由 + 老 DB 表。这是个**几天的工程**,不是一次清理能完成的。

#### 🛑 邮件抓取模块 `email_ingest.py`(3 处出错被吞掉的代码)
**事实**:文件名字带 "email_ingest",但实际上这个模块**主要的工作就是从邮箱拉附件 → 跑 OCR**。你明确禁止我碰任何 OCR 相关代码。
**结论**:为了避免和今天 OCR 会话的工作冲突,整个文件不动。
**Round 3 怎么办**:等明天/下周 OCR 那边完全稳定(24h 偏差观察通过),可以专门开一个小窗口处理这 3 处。其中 2 处其实和 OCR 完全无关(就是 IMAP 邮箱登出 + 文件夹数量解析),完全可以独立改。

#### 🛑 App 入口里的 "兼容老前端" 代码(`app.py` 里 IP 限流、Typhoon 增援、can_use_automation 等)
**事实**:Round 1 的扫描标记了 3 段"兼容老前端"代码值得清。但我去前端 home.js 仔细看了:
- **IP 限流字段(`ip_used_today` / `ip_daily_limit`)**:前端 home.js 里 4 处真的在读取(`if (_quota && _quota.ip_daily_limit) { ... }`)。虽然现在服务端永远返回 null,但前端代码路径活着。
- **Typhoon 增援字段(`typhoon_enhanced` / `typhoon_pages`)**:这些字段在 OCR 主路由的响应里——**OCR 禁区**。
- **`can_use_automation`**:前端 0 引用,但牵涉 db.py 5 处代码(种子账号创建函数的参数、UPDATE/INSERT SQL 列、传参),改起来跨文件,有 Pydantic 模型构造的边界 case 风险。不秒删。
**结论**:能秒删的只有 1 行墓碑注释(已删,见 commit 6)。其他 3 段需要"前端配合"或"跨文件改造",不属于"自主判断 + 不汇报"能完成的范围。
**Round 3 怎么办**:`can_use_automation` 字段是最简单的——专门开一次跨文件清理(app.py + db.py 各一处),验证 Pydantic 模型构造时不会因为缺字段而炸。IP 字段和 Typhoon 字段要跟前端配合,需要先确认"前端真的可以不要这些字段了"。

### 3.2 跳过的具体清单(给 Round 3 接手 agent 看)

| 项 | 现状 | 跳过原因 | Round 3 处理建议 |
|---|---|---|---|
| `email_ingest.py:328` 空 except | OCR 字段置信度判断 | OCR 禁区 | OCR 完全稳定后,加 logger.warning |
| `email_ingest.py:596` 空 except | IMAP conn.logout | OCR 禁区(整文件保守) | 完全可以独立改,加注释即可 |
| `email_ingest.py:627` 空 except | IMAP folder_count int 解析 | 同上 | 同上 |
| `app.py` IP 限流字段(582-584、634-635、817-818、1490-1491、1674-1675、2120-2121)| 前端真在用 + 部分在 OCR 区 | 跨前后端 + OCR 禁区 | 跟前端一起决定字段去留 |
| `app.py` typhoon 增援字段(2182、1732-1733、2112-2113)| OCR 主路由响应字段 | OCR 禁区 | 等 OCR 团队认领 |
| `app.py:608` + `db.py` `can_use_automation` | 前端 0 引用 server 仍在写 | 跨 2 文件 5 处 · 有 Pydantic 风险 | 单独一次清理 + 跑测试验证 |
| `bank_reconcile.py` 905 行整文件 | 前端 15+ 处在用 | 活体系不是死代码 | 业务级重构,不算清理 |
| `app.py:4287` "老 URL L4209 仍返回 home.html" 注释 | 行号陈旧 + 逻辑陈旧 | 风险:可能丢失运维意图 | 让维护者更新而不是删 |
| `db.py:6049, 6506-6581` MR.ERP SQL 注释 + seed 函数 | Round 1 因"误名"停下 | `get_mrerp_mappings_bundle` 实际给 Xero 用 · 误删炸 | schema 重构窗口统一改名 |

---

## 4. 4 个决策项 · 用户回复(2026-05-18 收尾后追加)

| # | 决策项 | 用户回复 | 备注 |
|---|---|---|---|
| 1 | 银行对账老模块要砍吗? | **保留**,明天连同"GL 总账明细新 Sheet + Sheet 合并 7→4"一起迁移到 bank_recon_v2 | 待用户拍板细节后开始 |
| 2 | IP 限流字段拉前端一起删? | **保留**(前端在用,B 选项) | 关闭 |
| 3 | 两个 VAT 导出策略留哪个? | **两个都留**(都活着 · 不是重复 · 详见下文调研)| Round 1 audit 误判修正 |
| 4 | `C:\Users\skin3\_audit_pearnly_imports*.py` 删不删? | 用户自己手动删 · 不在项目目录 | 关闭 |

### 4.1 VAT 导出双轨调研(决策 3 详细结论)

Round 1 audit 把 `vat_excel_export.py` 和 `vat_excel_exporter.py` 归为"功能重叠 / 重复代码候选" → **本会话调研后修正:不是重复,是两个不同产品**:

| 模块 | 行数 | 路由族 | 前端调用 | 用途 |
|---|---|---|---|---|
| `vat_excel_export.py` | 1497 | `/api/vat_excel/*`(via `vat_excel_routes.py`)| 7+ 处 (`home.js` build/tasks/download/regenerate/clear_old)| 新版 A/B 测试:**AI 只抽 8 个字段 → Excel 公式自己核对**(Zihao 2026-05-13 拍板的实验)|
| `vat_excel_exporter.py` | 391 | `/api/recon/*`(via `recon_routes.py:21`)| 10+ 处 (`home.js` bank-v2 export / 销项税对账导出)| 传统流程:**AI 全程对账完成后,把结果输出成 Korn 模板风格 Excel** |

**关键差异**:
- `vat_excel_export.py` 是**完整工作流**(input PDF → output Excel · AI 不判定 · 让 Excel 公式判定)
- `vat_excel_exporter.py` 是**单一导出工具**(已有 task + rows + client + vat_report → 输出 Excel)

**结论**:**都保留**。Round 1 把它俩并列写成"哪个是 strangler 目标"是审计偏差(被相似文件名误导)。本会话调研后此项**关闭**,不再视为待清理候选。

---

## 5. Round 3 建议(下个清理窗口的菜单)

按"能不能不汇报独立做完"分级。

### 🟢 易做(独立窗口可清完 · 适合短会话)
1. **`can_use_automation` 字段清理**:app.py + db.py 跨文件改 · 1 commit · 跑导入检查 + 启动测试就 OK
2. **`email_ingest.py` 后 2 处空 except**:OCR 完全稳定后做(IMAP 容错,跟 OCR 无关)· 加 logger.warning
3. **`scripts/git-deploy.sh` 拆分**:Round 1 留底的 deploy P1,把 `app.py:208-293` 写死的字符串拆成独立 shell 脚本 · 加 import 预检步骤
4. **`docs/` 整理**:`docs/cleanup/` 目录现在有 8 篇文档(audit、rerated、bank-reconcile、legacy-comments、3 个 round 报告等),可以加一个 `README.md` 做导航

### 🟡 中等(需要小决策 + 跨多文件)
5. **`db.py` MR.ERP seed 残余清理**:6506-6581 的"灌一份 mrerp 演示映射"函数 + 各引用 · 已确认是测试数据,但要先 SELECT 一下生产 DB 看有没有 endpoint 真用 mr_erp adapter
6. **`docs/cleanup/app-py-legacy-comments-pure.md` §3.2 老多租户兜底**:`app.py:1046+` "plan 字段为 NULL 的极旧用户" 兜底逻辑 · 50+ 行 · 验证 DB 后可清

### 🔴 大工程(需要专门开窗 + 业务参与)
7. **银行对账迁移**(见上 §3.1)
8. **VAT Excel 两条路线选一条**(业务决策)
9. **OCR 域剩余清理**:`pdf_text_extractor.py` 在 vat_excel_* 还在用,等 vat_excel 也迁到新 pipeline 才能动

---

## 6. 工具基线 + 健康检查

跑了 `python scripts/check_imports.py --quiet` 验证 Round 2 没引入新的"本地缺失模块":

```
项目根目录 .py 文件:34(Round 1 = 35,删了 quality_check.py)
全部 import 能解析:26
有 import 解析失败:8(全是已知第三方包,服务器装着的:fastapi/bcrypt/jwt/passlib/psycopg2/uvicorn/xlrd)
本地模块缺失:0(Round 1 抢救的 7 个幽灵模块全部就位)
```

**等于:本会话没破坏任何依赖关系**。

---

## 7. 给生产部署的提示

本会话 6 个 commit 即将 push 到 `origin/master`。预期效果:

1. 服务器 webhook 收到 → spawn detached subprocess → `bash /opt/mrpilot/git-deploy.sh` 自动重启服务(同今天 OCR 那次部署的流程)
2. **没有任何运行时行为改变**:
   - 删的 `quality_check.py` 服务器侧本来就没人调
   - 删的 `app.py:4277` 是一行 Python 注释
   - 改的 `line_client.py:306` 是注释化
   - 改的 `report_routes.py:265` 是把"静默吞错"换成"打 warning"——只新增日志输出,不改业务逻辑
   - 新增的 `scripts/check_imports.py` 不在任何启动路径里
   - `.gitignore` 不影响运行时
3. 推荐部署后看一眼 systemd 日志,确认服务正常启动即可(`journalctl -u mrpilot -n 50`)

---

## 8. 不变的承诺

- ✅ 全程不动 OCR 禁区(services/ocr/、4 个 OCR 接入点、db.py OCR cost 函数、/api/health、services/ocr/pdf_utils.py)
- ✅ 每个 commit 前后跑 `scripts/check_imports.py`,基线干净
- ✅ 涉及业务判断的(VAT 导出路线、银行对账重写)挂决策清单不动手
- ✅ 涉及 DB schema 改动的(MR.ERP seed 数据)不动
- ✅ 不确定的项(`can_use_automation` 跨文件 Pydantic 风险)挂 Round 3 不秒删

---

*Round 2 报告 · 2026-05-18 · 由本会话生成 · 即将 push 至 GitHub*
