# 📊 STATE · Pearnly 项目状态

> **最近更新**:2026-05-13 · v4.10.1 已上线 ✅ · 撤 toggle/BETA/email gate + 标题区跟随子模块 + KPI 4卡 + 任务列表 · 发现 5 个残留待 v4.10.2 顺手修
> **当前线上(已 ssh 核实)**:**v118.32.4.10.1**(KPI卡+任务列表+标题动态跟随 · 全网开放)
> **🔥 v4.10 微版本排期(2026-05-13 Zihao 拍板)**:
>   - ✅ **v4.10.0** · DB + API 纯后端 · 5 API 全过
>   - ✅ **v4.10.1** · 撤 toggle/BETA/email gate + 标题跟随子模块 + KPI 4卡 + 任务列表 · **5 个残留留 v4.10.2 修**
>   - 🔥 **v4.10.2** · 详情抽屉(5 节) + **顺手修 v4.10.1 5 个残留(下载 410 优先)**:
>     - ① 状态列显示英文"done" → i18n 4 语 badge
>     - ② 客户列兜底显示英文"client" → 空时显示"全部客户"4 语；有名称显示原文
>     - ③ 标题区重复(顶部+主区一模一样) → 删主区重复标题
>     - ④ 底部"还没有对账任务"+旧上传区死代码 → 完全删除
>     - ⑤ ★ 旧任务点下载返回 download.json 错误 → 改 fetch 异步处理 410(数据已过期 toast) vs 200(正常下载)
>   - 📅 **v4.10.3** · 4 语完整 + 文件名 + Excel + 存储生命周期
>   - 📅 **v4.10.4** · 收尾回归
>   - 📅 **v4.10.5** · upg/pay/line/plan/team ~60 处补 4 语
>   - 📅 **v4.10.6** · 超管 adm-* 137 key 简化为 zh+th 2 语 + 标记 i18n 分级铁律生效
> **拍板要点(2026-05-13)**:
>   - 试用账号也能用 · 限额 3 次 · 第 4 次弹"升级解锁无限次"(v4.10 撤白名单时实施)
>   - "近期任务" = 当前 tenant 内 · 不跨租户
>   - PDF 溯源三层降级:Gemini bbox → fuzzy text match → "溯源不可用"灰按钮
>   - CLAUDE.md 必测规则已改:项数不限 · 每项 ≤30 秒验完 · 重大版本可分段
>   - **v118.32.4.9.3 分组 bug 根治(暂停)** · 12 张真实测试报告被识别为发票 · vat_file_classifier filename 提示对泰文 \b 边界识别失败 · 转 v4.9.5 内测做 A/B 后再回头
>   - **v118.32.4.10 7 项 OCR 准确率底线(1 天)** · 主线接力
>   - **v118.32.4.11 Excel 4 语对照表导出 + 列表时间戳(0.5 天)** · 按 PDF 模板出会计师签字版
>   - 6 张卡 10 分钟降级到 v118.32.5 · v6 D 后台异步 + 通知
> **🔥 P0-VAT 上下文**:2026-05-12 P0-VAT 升最高优先级 · MR.ERP 剩余 v118.27.8.1.18 → v22 全部暂停 · P0-VAT 完成接力
> **主线**:LINE 登录 ✅ → 用户管理 ✅ → 大厂合规对齐 ✅ → 客户分配 ✅ → ERP 适配器 v27.0-7.1 ✅ → v27.8.0 反向工程 ✅ → **v27.8.1.0-14d MR.ERP 整链路完美闭环** ✅ → **P0-A v15-v17 推完(3/8)** ✅ → ⏸️ **P0-A v18-v22 暂停** → 🔥🔥 **P0-VAT 销项税对账 v118.32.0 → v3.x 进行中** → P1 公测前 → P2 模块扩张
> **重要文档**:`MODULE_SALE_VAT_RECON_PRD.md`(P0-VAT 需求权威)· `HANDOVER_v118_32_3_9.md`(本窗口完整交接)

---

## ⚠️ 战略铁律 · 头号(2026-05-09)

**自动化 ERP 适配器主线升 P0** · 所有后续窗口必须以 ERP 工作优先 · 其他全部排后:
- ⏸️ 银行对账 v118.26.3/.4 暂停
- ⏸️ 用户管理深化 v118.29.x 推后
- ⏸️ 老板看板 v118.30.x 等 ERP 闭环后做
- ✅ Git 私库 + 公测可与 v118.27 并行

理由:OCR 推 ERP 才是 Pearnly 核心商业闭环 · 没这条线 · 银行对账 / 用户管理只是辅助。

---

## 一句话定位

Pearnly = **4 语言 SaaS（中 / 英 / 泰 / 日）** · 会计事务所 + SME 老板的 AP 自动化 SaaS · 4 语都是真产品语言 · **当前 GTM 首发 = 泰国市场** · 强项是多语言 OCR(泰中日)+ 全管道自动化(LINE / 邮件 / 文件夹)+ **ERP 中立中间件(任何 ERP 都能推 · API 直推 / xlsx 兜底 / 浏览器扩展全自动)** + 一页多发票拆分。

**「不让用户换 ERP · 让 Pearnly 适配所有 ERP」** = Pearnly 区别于 FlowAccount / PEAK 单兵作战的核心定位。

> 🌐 4 语铁律：每个功能必须 th / en / zh / ja 4 语完整 · 不许"先做泰文剩下再说" · i18n 字典顺序 th → en → zh → ja（开发优先级·非重要性）· 详见 CLAUDE.md 顶部铁律

---

## 线上版本

| 项 | 值 |
|---|---|
| 域名 | https://pearnly.com(Cloudflare DNS only · 自建 SSL · 已稳)|
| 服务器 | `root@45.76.53.194` · Vultr Tokyo · Ubuntu 24.04 · `/opt/mrpilot/` |
| 数据库 | Supabase PostgreSQL `aydjsgmirjpkjaqknmlg` · AWS ap-southeast-1 · service_role |
| 部署 | `bash /opt/mrpilot/deploy.sh /tmp/<tar.gz>` |
| 邮件 | Gmail SMTP · 发件人 `Pearnly <hello@pearnly.com>` |
| LINE Bot | Greeting message **ON** · 加好友自动推 4 语欢迎 + 6 位代码绑定引导 |
| LINE Login | Channel ID `2010022630` · Email scope **Applied** ✅ |
| env(关键)| `PEARNLY_PUBLIC_URL=https://pearnly.com` `LINE_LOGIN_CHANNEL_ID=2010022630` |
| 联系 | hello@pearnly.com / +66 86-889-2228 / LINE @059oupmg |

**当前 cache bust**:`home.css?v=11828126` · `home.js?v=11828126`(v118.27.8.1.17 · 真生产)
**待部署 v17.1 cache bust**:`11828127`(租户管理 hotfix)
**下版本(v118.27.8.1.18)cache bust**:`11828128`

---

## 🔑 账号分工(铁律)

| 账号 | 用途 | 备注 |
|---|---|---|
| **skin306152@gmail.com (Google OAuth)** | 🧪 功能测试账号 + 测试中心白名单 + ERP dev seed 白名单 | `user_id=468b50c1-5593-4fd6-990d-515ce8085563` `tenant_id=040f012b-a456-49b3-a8f4-f83901bec9ea` |
| **Earn** | 👑 超管账号 | 永远只看 /admin · 不跑系统业务 · 仅平台管理 |
| mrerp@outlook.co.th | yearly · 1500 配额 · **绝对不许碰** | 真实付费用户 |

**铁律**:测产品功能 → skin OAuth · 测平台管理 → Earn /admin · 绝对不许碰 mrerp

---

## 🔌 MR.ERP 测试环境(本窗口新增)

| 项 | 值 |
|---|---|
| 域名 | `mrerp4sme.com` |
| 厂商 | Mr.ERP for SME |
| 类型 | PHP web 应用 |
| 测试账号 | Username: `test01` / Status: User |
| 测试公司 | `1010-01-000006` บริษัท ทดสอบการใช้ จำกัด |
| 测试数据库 | `TEST2019`(URL `?comidyear=6&seldb=1`) |
| 文件格式 | `.xlsx` · 必须 3 sheet · 名 `Worksheet` / `Worksheet 1` / `Worksheet 2` |
| 编码 | UTF-8(.xlsx 内部 XML) |
| 日期格式 | `YYYY-MM-DD` 字符串 · cell 格式 `@` 文本 |
| 客户代码格式 | 三段式 `01-อนุรักษ์-001`(中泰文混) |
| 税率字段 | 字符串枚举 `"นอกระบบ"` / `"7%"` / `"0%"` |
| API | ❌ 无 |
| 文件夹监听 | ❌ 无 |
| 定时导入 | ❌ 无 |

---

## 🔥🔥 P0-VAT v118.32.3.x → v118.32.4.x 真实进展(2026-05-12 外部窗口核实)

> **背景**:上窗口意外关闭 + 文档没来得及更新 · 本窗口 ssh 服务器核实真实状态 · 文档曾误标 v3.9 待部署 · 实际已推到 v4.7 在线
> **核实方式**:服务器 `/opt/mrpilot/static/home.html` 的 cache bust + `/api/version` + 服务器代码版本注释 grep

**v3.0 → v3.9(全部已上线)** —— 上上窗口 BCDEF 优化 · 详情见旧 HANDOVER

**v3.10 → v4.7(已上线 · 上窗口意外关闭前推完 8 版 · 中间细节缺失)**:

| 版本 | 推断内容(代码注释 grep)| 状态 |
|---|---|---|
| v4.0 | C 进度反馈业务化 5 阶段步骤 | ✅ 在线 |
| v4.1 | 失败明细 + 业务错误码 4 语 + 失败 task 关联客户名 | ✅ 在线 |
| v4.2 | 微调(无注释痕迹) | ✅ 在线 |
| v4.3 | 金额格式化含币种 + 概览卡可见性控制 | ✅ 在线 |
| v4.4 | 无注释痕迹 | ✅ 在线 |
| v4.5 | 无注释痕迹 | ✅ 在线 |
| v4.6 | 无注释痕迹 | ✅ 在线 |
| v4.7 | done 状态防被轮询响应覆盖 | ✅ 在线 |

**v4.8(本窗口推上线 · 2026-05-12)**:

| 文件 | 改动 | 业务影响 |
|---|---|---|
| `vat_report_parser.py` | Gemini prompt 加 5 条严格规则 + self-check | OCR 不许自作主张改人名/税号/金额 · self-check 验证 pre_vat + vat ≈ total |
| `recon_routes.py` | RowActionBody 加 `source` 字段(invoice/report) | 行级操作记录用户采纳哪边为准 · 拼进 notes 不改 db schema |
| `home.js` "B 方案" | accepted_diff 视觉等同 matched(绿勾 + 已核对徽章)+ 2 个大按钮 + 新 action 映射(accept-invoice / accept-report / undo) | 金额对不上的行用户校对兜底 · 选完即视为对得上 |
| `home.html` / `home.css` | cache bust 11832470 → 11832480 + 配套样式 | - |

**部署核实**:`/api/version` = `{"version":"11832480"}` ✅ · `systemctl is-active mrpilot` = active

**⚠️ deploy.sh 坑**:`sleep 3` 不够(uvicorn 启动实际 7 秒)· 部署完瞬间 nginx 502 · 等几秒自动恢复 · 下次顺手把 sleep 改 10s

**🔴 P0 遗留(v4.8 没碰)**:6 张文件批量识别仍卡 10 分钟 · 嫌疑根因 `parse_vat_report` 同步函数阻塞 async 事件循环 · 推荐 hotfix 包 `run_in_executor`

**剩余 BCDEF 阶段**:D 后台异步 + LINE/邮件通知(v118.32.5)→ E OCR prompt 升级深化(v118.32.6 · v4.8 已偷跑 prompt 严格规则部分)

---

## 🔥🔥 v118.32.4.9 核对表重构 · 主线推翻(2026-05-12 Zihao 拍板)

> **触发**:Zihao 用 19 张 BAKELAB 发票 + 1 张销项税报告测试 v4.8 · 结果 1✓ 16⚠ 严重对不上 · 截图 + PDF 核对要求(`异常\ขั้นตอนการตรวจรายงานภาษีขาย.pdf`)发回
> **核心认知改变**:Pearnly = **核对表生成器**(不是匹配判定器)· 准确率 100% 定义 = **OCR 抽出来的字段跟原文 100% 一致**(不是匹配率 100%)

### 核对要求(来源 · Zihao 给的会计师标准 PDF)

**必识别 7 项 = PDF 编号 3-9**:
| # | 字段 | 备注 |
|---|---|---|
| 3 | 日期 | 必 |
| 4 | 发票号 | 必 |
| 5 | 客户名 | 必 |
| 6 | 买方税号 | 必 |
| 7 | 买方分公司 | 必(个人买家除外 · PDF 明文) |
| 8 | 净额(VAT 前) | 必 |
| 9 | VAT 金额 | 必 |

**辅助检查**:PDF 第 1 项"是否有 ใบกำกับภาษี 字样" + 第 2 项卖方 4 子项一致性(同一份报告应同一个卖方)

### 三个微版本拆分

**v118.32.4.9 核对表重构**(1.5 天):
- 后端 reconciliation_matcher.py 改"逐字段对照"模式 · 不归一化 · 如实展示两边
- 数据结构每行 7 字段 × 报告/发票两侧 + 一致 bool + 差异类型枚举
- 前端对账中心改对照表 UI(参考 PDF 底部表格布局)
- 每行差异提供 3 个动作:"改报告"/"改发票"/"两边都对是同一笔"
- **UI 顶部加"此次汇总"区**(Zihao 强调):
  - 总行数:N
  - 完全一致:X 行
  - 数据差异:Y 行(细分 · 发票号差/客户名差/金额差/...)
  - 🔴 OCR 没识别完整:Z 行
  - 散客无发票(正常):M 行
- 4 语 i18n × 全部新词条

**v118.32.4.10 7 项 OCR 准确率底线**(1 天):
- vat_report_parser.py + 发票 OCR 都加:7 项任一缺失 → 那一行红字"OCR 没识别完整"+ 重传按钮
- 后端业务规则校验(独立于对照):
  - 净额 + VAT ≠ 总额 → "金额自相矛盾"
  - VAT ≠ 净额 × 7%(非 0% / 免税)→ "税率异常"
  - 税号不是 13 位 → "税号格式异常"(散客除外)
- 系统标完用户自己决定要不要修

**v118.32.4.11 Excel 导出 + 列表时间戳**(0.5 天):
- 按 PDF 底部表格格式导出 Excel(左右双栏 + 备注 + 三签名位 ผู้จัดทำ/ผู้ตรวจสอบ/ผู้อนุมัติ)
- **Excel 表头 4 语 i18n**(F2 已做基础 · 这次扩到对照表全字段)
- **Excel 顶部加"此次汇总"区**(对应 UI 汇总)
- 近期对账列表加时间戳 + 默认时间倒序 + "清 7 天前任务"按钮

---

## 🧪 v118.32.4.9.5 内测结果 + v118.32.4.9.6 规划(2026-05-13 评估完)

> **背景**:v4.9.5 推上线后 Zihao 用 13 个场景实测 Excel 公式对账新方案 · 仅 skin306152 内测可见
> **结果**:4 全对 + 3 部分对 + 6 个 bug → 公式对账思路成立但实现要重做
> **现状**:已评估完工作量 · 等 Zihao 拍 504 + 拍"开干"

### 13 场景测试结果分布

| 类型 | 数量 | 含义 |
|---|---|---|
| ✅ 全对 | 4 | 发票号匹配 + 7 字段全等 + 金额对得上 |
| 🟡 部分对 | 3 | 发票号匹配但金额或字段有差异(Sheet 3 SUMIF 聚合后信息丢失看不出来) |
| 🔴 错 | 6 | 5 类 bug · 见下 |

### 5 个 bug 拆解(v4.9.6 一锅烩 · 评估 2.5 天)

| # | bug 现象 | 根因 | 修法 | 工时 |
|---|---|---|---|---|
| 1 | Sheet 1/Sheet 2「期间」列空白 | invoice.period AI 没抽 + Sheet 2 拿 period_year/month 没拼出 | build_excel 写入时 period 空 → 从 invoice_date / report_date 降级算 MM/YYYY(BE 转公历) | 0.2 天 |
| 2 | 散客发票(无税号)+ 散客在报告里 → 现在标"发票有报告无"孤儿 | 散客硬走"无税号即孤儿"分支 · 没去报告里查 | 散客改三重匹配 客户名+发票号+金额 · 加 `_match_cash_customer` 辅助 | 0.4 天 |
| 3 | Sheet 3 只对总金额 · 漏发票号差/日期差/期间差/分公司差/客户名差 5 维度 | Sheet 3 按 buyer_tax_id SUMIF 聚合 · 同客户多张发票合一行 · 维度信息丢失 | **Sheet 3 整段重写** · 砍 SUMIF · 改 INDEX/MATCH 按发票号一对一 · 5 维度各占独立列 · 报告侧落单行贴在表底 | 0.8 天 |
| 4 | 税号差 1-2 位直接判孤儿 | 等号严格比 · 无 fuzzy | 加 Levenshtein 编辑距离 ≤ 2 → 标"疑似匹配 · 请确认" · 不替用户判定(符合「我们只核实」铁律) | 0.3 天 |
| 5 | 发票缺税号(OCR 漏抽)→ 现在标孤儿 | 当前只看发票自己的 buyer_tax_id 空 = 散客 | 反向匹配 VAT 报告 · 找到了 → "OCR 漏抽税号 · 实际应为 XXX" · 跟 Bug 2 共享代码 | 0.2 天 |

### UI 美化清单(0.6 天 · 基准模板 `异常/vat_recon_BEAUTIFIED_demo.xlsx`)

| 项 | 实现 |
|---|---|
| Sarabun 字体(泰文优先) | openpyxl Font(name="Sarabun") + Tahoma fallback |
| 金额列千分位 #,##0.00 + 右对齐 | 已有部分基础 · 全字段对齐 |
| 斑马条纹(偶数行 #F9FAFB) | 数据循环里设 PatternFill |
| 表头蓝底白字 + 行高 32 | 蓝底白字已有 · 行高从 24 → 32 |
| 冻结第一行 | 已有 freeze_panes="A2"(保持) |
| Sheet 标签彩色 | ws.sheet_properties.tabColor(发票蓝/报告绿/对账橙/说明灰) |
| Sheet 3 KPI 4 大数字卡片 | 顶部 4 个大单元格 · 字号 18 加粗 + 背景色 + 大行高 |

### 核心改造点 · Sheet 3 推翻重做

- **当前**:按 `buyer_tax_id` 聚合 · 每税号 1 行 · `SUMIF(Sheet1!I)` 算金额合计
- **改后**:按 `invoice_no` 一对一 · 每张发票 1 行 · INDEX/MATCH 按发票号查报告
- **报告侧没匹配上的**:贴表底 ("发票无 · 报告有" · 不让信息丢失)
- **散客特殊处理**:三重匹配 客户名+发票号+金额 · 匹配失败再走 OCR 漏抽提示
- **结果**:用户能在一张表上同时看到 5 维度差异 · 不需要回到 Sheet 1/2 翻原数据

### v4.9.6 决策点(等 Zihao 拍)

🟡 **真实国税局 PDF 504 超时**(33 行 BAKELAB · pdfplumber 抽不到 → Gemini 25s timeout)
- 带:+0.5 天 · timeout 60s + 重试 + pdfplumber 优先 · 总 3.0 天
- 不带:推 v4.9.7 · 用户继续用合成数据测 · 总 2.5 天

### 部署后必测(≤2 项 · Zihao 已确认)

1. 重跑 13 个测试 PDF · 看每个 bug 都标对
2. 下载 Excel · 看格式美化是否到位

### 测试数据资产

- `异常/测试/v4_9_多场景/`(1 报告 + 12 发票)
- `异常/测试/รายงานภาษีขาย 03.69 - 001 033.pdf`(33 行真实国税局 · 504 那张)
- `异常/vat_recon_BEAUTIFIED_demo.xlsx`(美化基准模板)

---

## 🎯 v118.32.4.10 UX 大改造 · 等 v4.9.6 测过开干(3.1 天)

> **触发**:2026-05-13 Zihao 拍板 · 公式对账 v4.9.6 修完后 · UX 从"导出 Excel"升级为"UI 主流程 + Excel 变导出"
> **核心认知**:对账完成 → 进 UI 看大盘 + 详情 · Excel 不再是主出口 · 看齐 DataSnipper 同级 UX

### 改动清单

**改动 1 · 撤销旧模式(0.3 天)**
- 删「标准对账 / Excel 公式对账」toggle 切换器
- 销项税对账模块全平台默认走新流程 · 撤 skin306152 email 白名单
- BETA 标签保留(产品未完全成熟)
- 旧 vat_report_parser.py 等模块代码不动 · 保留向后兼容 · 但 UI 入口隐藏
- 试用账号限额 3 次 · 第 4 次弹"升级解锁无限次"(不是直接拒绝)
- 「近期对账任务」= **当前 tenant 内所有用户**的历史任务(不跨租户)

**改动 2 · UI 汇总页核心(2.3 天)**
- 后端:`/build` 不返 xlsx 改返 JSON + 新建 `vat_recon_results` 表 + 单独 export endpoint(0.8 天)
- 前端主体(1.8 天):
  - 顶部 KPI 4 大卡(行高 100)· 蓝总笔数 / 绿匹配 / 红异常 / 橙异常金额
  - 第二行筛选 + 操作:[全部][匹配][缺一边][金额不一致][待确认] tab + 排序 + 批量 + 📥Excel + 📄PDF
  - 对账明细表 · 列:☐ 状态 税号 客户 发票号 期间 发票金额 报告金额 差异 操作
  - 行颜色:匹配绿底 / 异常红底 / 待确认黄底 / hover 高亮
  - 4 语 i18n × 50+ 词条 + 移动端适配 + 防呆撤销

**改动 3 · Excel 导出按钮(0.2 天)**
- 复用现有 build_excel · 单独 GET endpoint
- 点按钮重新生成(用户改了数据也能拿最新)

### 关键决策(已拍)
- 撤白名单 → 所有 plan 都能用(trial 限 3 次 / monthly+yearly+lifetime+admin 无限)
- 详情抽屉 + PDF 预览推到 v4.11 · v4.10 只做列表 · 点行先不展开详情
- 审计 PDF 导出推到 v4.12 · v4.10 只做 Excel 导出

---

## 🔍 v118.32.4.11 详情抽屉 + PDF 溯源 · 等 v4.10 测过开干(3.0 天)

> **核心**:点行 → 抽屉滑出 · 左半数据可编辑 · 右半 PDF.js 预览 + 抽取字段高亮
> **设计哲学**:让会计师"一眼看到 OCR 抽对没" · 不用切回原 PDF

### 改动清单

**改动 1 · OCR 抽 bbox 三层降级(1.5 天)**
- 主路径:Gemini prompt 加 bbox 坐标输出(page_num + x/y/w/h 百分比)
- 兜底 1:Gemini 返回 bbox 不可靠 → 用抽出来的文本 fuzzy match pdfplumber 文字层定位
- 兜底 2:文字层也找不到(图片型 PDF)→ 标"溯源不可用"灰按钮
- DB:`vat_recon_field_bbox` 表(recon_id, row_idx, field, page, bbox_pct)

**改动 2 · 详情抽屉 UI(1.5 天)**
- 抽屉风格参考异常栏抽屉(home.js 现有模式)
- 左半:抽取数据表格 · 每字段可编辑 · 改完 [接受]/[驳回]/[标记疑问]
- 右半:PDF.js 渲染 · 点字段 → 跳页 + 闪烁高亮 bbox(2s 黄底)
- 底部按钮:[修改][接受][驳回][标记疑问]
- PDF.js 用 CDN 加载 · 不要 iframe

---

## ⏸️ v118.32.4.12 暂缓 · 待真实会计师反馈(P3 候选)

> **拍板**:2026-05-13 Zihao 决定 · v4.11 上线后让真实会计师试用 2-3 周再决定要不要做
> **理由**:避免凭空猜需求做错方向

候选内容:
- 审计 PDF 导出(KPI + 异常表 + 异常发票缩略图 + 签字栏 + 4 语)
- 历史对比卡片(同客户跨期"上月 X 张 · 这次 Y 张 · 异常增加 Z")
- 批量操作(选行 · 标已审/驳回 · 全部接受匹配项)

**触发条件**:
- 真实会计师试用 2-3 周
- 反馈表明这些功能确实是高频需求(不是"想要"而是"必需")
- 之后再开 v4.12 · 工时 2.7 天

---

### 推翻的旧方案(留痕 · 别再走回头路)

❌ **v4.9 旧方案 · INV ↔ IV 模糊匹配归一化** —— 替用户做决定 · 违反"我们只核实"哲学
❌ **v4.9 旧方案 · 客户名去 ์ 符号自动算同一人** —— 同上
❌ **匹配率 100% 当成功标准** —— 错位的 KPI · 真正 KPI 是 OCR 字段抽取准确率 100%

---

## 核心模块状态

### ✅ 已上线(线上稳定)

**v118.28 系列(2026-05-08 ~ 05-09 · 17 版)**
- v28.0 客户切换器 + v28.1.0 测试中心
- v28.3 LINE Bot URL · v28.4.x LINE 社交登录
- v28.5.x 顶栏布局 + 移动端 6 BUG
- v29.0 用户管理 UI + 操作日志
- v28.6 超管员工 tab 只读化
- v28.7 + v28.7.1 密码重置链接化
- v28.8 客户老板查 Pearnly 访问日志
- v28.9 改密后旧 JWT 失效
- v28.2 + v28.2.1 超管 /admin URL 独立
- v28.1 客户分配面板

**v118.26 银行对账系列(2026-05-09)**
- v26.0 顶级菜单 + 当月概览
- v26.1.x 批量上传 + 列表筛选
- v26.2.0/.1 右半屏 + 候选 pane + 客户徽章 ✅(测试通过)
- **v26.2.2** OCR P0 紧急修补(quota gate 早返回 · 修 v27.7 fix_orphan tenant=0 死结)✅
- **v26.2.3** admin_upgrade_user 字段修正 + forgot_password 改 SMTP ✅
- **v26.2.4** banned/inactive 安全闸 + 员工 plan 继承 + _require_owner_or_super 懒建 ✅
- **v26.2.5** signup 3 路径同事务建 tenant(根因修复)✅

**前期累计**
- 多语言 OCR(泰中日)· AP 自动化管道 · 4 语 i18n subscribeI18n 总线
- admin 后台 80% 完成度

### 🔥 进行中(主线 · 战略调整后)

**头号 P0 · 自动化 ERP 适配器**(13-17 天):
- ⏳ v118.27.0 客户/科目/税码映射底座(2-3 天)· **下一件**
- ⏳ v118.27.1 MR.ERP 适配器(方案 A · 5-7 天)· 等 4 件物料
- ⏳ v118.27.2 FlowAccount API 直推(2 天)
- ⏳ v118.27.3 PEAK API 直推(2-3 天)· 等 partnership
- ⏳ v118.27.4 Xero + QB API 直推(各 1.5 天)
- ⏳ v118.28.0 Express 适配器(3 天)
- ⏳ v118.28.1 「我的 ERP 是 ___」反馈框(0.5 天)

**P0 公测启动并行**:
- ⏳ A.1 Git 远程私库 push(0.5 天)

**P1 浏览器扩展平台**(公测后):
- ⏳ v118.31 系列 浏览器扩展框架 + MR.ERP web 自动点击(15-18 天)

### ⏸️ 暂停 / 推后

- v118.26.3 银行对账拖拽匹配(1.5 天 · ERP 闭环后)
- v118.26.4 银行 Excel/CSV 解析(0.75 天 · 同上)
- v118.29.x 用户管理深化(3.6 天 · 公测后)
- v118.30.x 老板看板 + 风控告警(L4-L6 · 7-10 天 · ERP 闭环后)

### ❌ 已取消 / 永久砍

- v27.8 全表 RLS(service_role 自动 BYPASS)
- ~~Mr ERP 直推对接(已复活)~~ → v118.27.1 立项
- Facebook 社交登录
- 超管直接重置客户密码(v28.7)
- 老板看到员工临时密码(v28.7)
- **桌面 RPA(D)** + **UI Automation API(E)**(2026-05-09 · v26.2 调研后定砍)
- 用友 T+ 适配(泰国基本无用户)
- Tally 适配(on-premise + API 弱)

### 🚫 阻塞(等外部条件)

- MR.ERP 4 件物料(现金销售真实数据 / 采购 / 会计凭证 / 错误信息)· 等 Zihao 补
- PEAK API 文档 + sandbox · 等 partnership 邮件回
- Express API 文档 · 等商务联络回

---

## 🆕 铁律清单(累计 33 条)

1-22:见 v118.28.1 HANDOVER · 不变

23. **战略调整 · 自动化 ERP 主线升 P0**(2026-05-09)· 银行对账让路 · 所有窗口 ERP 工作优先
24. **ERP 二分法**(2026-05-09)· 有 API → API 直推 / 无 API → A+C · v118.27.0 映射底座是依赖
25. **桌面 RPA(D)+ UI Automation(E)永久砍**(2026-05-09)· 桌面 ERP 走 A 兜底
26. **浏览器扩展平台(C)= Pearnly 平台能力**(2026-05-09)· 不只 MR.ERP · 复用所有 web ERP
27. **MR.ERP `mrerp4sme.com` PHP web 应用 · 厂商 Mr.ERP for SME**(2026-05-09)
28. **MR.ERP 文件格式铁律**(2026-05-09):.xlsx · 3 sheet 命名严格 `Worksheet/Worksheet 1/Worksheet 2`
29. **MR.ERP 字段格式铁律**(2026-05-09):日期字符串 YYYY-MM-DD · 客户代码三段式含泰文 · 税率字符串枚举
30. **MR.ERP 数据库 / 多公司 = 服务器分配**(2026-05-09):URL 参数 · Pearnly 推不需带
31. **MR.ERP 无 API / 无文件夹监听 / 无定时导入**(2026-05-09):全自动只能走方案 C 浏览器扩展
32. **L1-L6 产品价值定位**(2026-05-09):入账 → 学习 → 对账 → 看板 → 合规 → 风控 · 客单价 599 → 3000-5000
33. **公测策略**(2026-05-09):Git 私库后即启动 · ERP 适配器并行 · 公测反馈反推优先级

### 🆘 v118.26.2.2-2.5 紧急修补铁律(34-43)

34. **OCR quota gate 早返回模式**(v118.26.2.2):有效 plan 用户(trial/free/pro/firm/enterprise/monthly/yearly)在 `_check_user_quota` 顶部直接放行 · lifetime 单独看自带 key
35. **tenants 表无 plan / max_seats 字段**(v118.12.1 → v118.26.2.3):任何 `UPDATE tenants` SQL 严禁包含这 2 字段 · 否则整条抛错被 try 吞
36. **forgot_password 邮件用 SMTP 主用**(v118.26.2.3):`_smtp_send_email` from app.py · Resend 作 fallback · 不依赖 RESEND_API_KEY
37. **被禁用 / 未激活账号 OCR 拦截**(v118.26.2.4):`_check_user_quota` 顶部 `is_banned` / `is_active=False` 早返回
38. **员工 plan 继承在 OCR 路径**(v118.26.2.4):`_check_user_quota` 检测 `role=member` 时查 owner.plan
39. **`_require_owner_or_super` 懒建 tenant 兜底**(v118.26.2.4):`tenant_id=NULL` 时自动建
40. **signup 3 路径同事务建 tenant**(v118.26.2.5 根因解):`_ensure_tenant_for_new_user(cur, user_id, plan, ...)` · 用 PLAN_CONFIG 真实 quota
41. **新注册 token 带 tenant_id**(v118.26.2.5):signup 主路径返回的 access_token 立刻带新 tenant_id
42. **大改造后 5 步回归测试铁律**(SOP §7.5 新增):动 users/tenants/plan/role/quota/auth 后 · 部署后跑 5 步验证 · 一步红立刻 hotfix
43. **LINE push API ack 不可靠**(2026-05-09):已有 LINE→Email fallback 是产品权衡 · 不修

---

## 数据资产

| 资产 | 数量 | 用途 |
|---|---|---|
| 银行对账单 PDF | 9 张 | 对账测试 |
| 发票 OCR 异常规则 PDF | 9 张 | OCR 边界测试 |
| skin OAuth 测试数据 | 8 个 TEST_ 客户 / 37 张发票 / 5 条异常 | 功能测试 |
| **MR.ERP 销售-赊销真实样本** | 1 份 .xlsx(2 行数据 · 文件名 mrerp_sample_SC_credit_real.xlsx) | **v27.8.1.0 推送测试 + 适配器开发** |
| **MR.ERP 销售-现金空模板** | 1 份 .xlsx | 同上(待补真实数据 · 当前 sheet 命名错 Sheet1-4 · 应是 Worksheet/Worksheet 1-3 · 不能直接用) |
| **PEARNLY_ERP_RESEARCH_2026_05.md** | 11 家 ERP API 状态调研 | 战略决策档 |
| **PEARNLY_ERP_DEEP_2026_05.md** | 自动化模块深度优化 + L1-L6 | 战略决策档 |

---

## ⭐ 极简模式(新窗口必读)

省 70% Claude 额度 · 4 语红线不破。

### 启动步骤

1. 新窗口第一句话发简化版 `NEW_WINDOW_OPENER.txt`(3 行)
2. 把当前最新 `pearnly_v118_27_8_1_14d.tar.gz` 拖进对话框
3. 模板「我要做的事」一栏写一句话需求
4. **推荐第一个版本:v118.27.8.1.15 批量上传 500 + plan +300 + auto_push 默认开**(P0-A 第一站 · 1 天)
5. **完整路线**:v15→v22(9.5 天)按 BACKLOG.md 顺序推 · 中途不许扩大范围

### 新窗口 Claude 必须遵守

红线 / 业务闭环 / 省钱 / UI ≤ 5 项 / 部署后命令验证 / 测试中心隔离 → 全在 `PEARNLY_WORKFLOW_SOP.md`。

---

## 当前已知小问题

- 🔴 **P0 · v4.9.2 分组 bug 暂停未解**(2026-05-13):用户拖 13 个 v4_9_多场景测试文件 · stats 显示 12 文件 12 发票 0 VAT 报告 → **VAT 报告被识别成 invoice 而非 vat_report** · v4.9.2 加的 "filename 含 รายงาน → 强制 vat_report" 没起作用 · Zihao 拍板暂停修转去做 v4.9.5 内测 · 留给 v4.9.3 / v4.9.6 一起 fix
- 🔴 **v4.9.5 内测 · 真实国税局 PDF 504 超时**(2026-05-13):合成 PDF(12 行 · reportlab)能跑通 · 但真实 BAKELAB 测试文件夹的 `รายงานภาษีขาย 03.69 - 001 033.pdf`(33 行 · 真实国税局格式)Gemini 25 秒超时 · 嫌疑:PDF 是图片化文字层 → pdfplumber 抽不到 → fallback Gemini 但 timeout 太短 · v4.9.6 已规划修(timeout 60 + 重试 + pdfplumber 优先)
- 🟡 **v4.9.5 测试反馈待修(5 bug + UI 美化 · 2.5 天 已评估)**:详见上方"v118.32.4.9.5 内测结果 + v118.32.4.9.6 规划"段 · 等 Zihao 拍 504 + 拍"开干"
- 🔴 **P0 · 6 张文件批量识别卡 10 分钟未根本解决**(v118.32.3.0-3.9 多版未解决 · 下窗口必修)· 嫌疑根因:`parse_vat_report` 同步函数阻塞 async 事件循环 · 详见 `HANDOVER_v118_32_3_9.md`
- 🟡 P1 · F1 金额对齐(`amount_pre_vat`)用户未实测 5/5 BAKELAB 匹配
- 🟡 P1 · F2 Excel 4 语 i18n 表头(中/英/日/泰)用户未实测
- 🟡 P1 · 系统设置改 modal(v3.6-3.9)用户没逐个 tab 测过 · 可能某些 pane 内容布局错乱
- 🟡 P1 · 单据记录列贴右(v3.9 才找到根因 `.card { padding: 20px }`)用户未确认
- 🟢 P2 · `gemini_engine.py` 不在 project knowledge · E 阶段(OCR prompt 升级)前必须 scp 拉到本地
- 🟢 P2 · 测试中心 sidebar badge 当前显示 "24" 异常 · 下窗口让用户截图看具体错误
- v118.26.2.5 用户管理/租户连环 BUG 全修通过用户测试 ✅
- `/api/me/plan` 慢 2.5-3.4s(测试中心 api_slow 触发)· 加 5 分钟前端缓存 · 0.2 天 · P2
- `deploy.sh` 不复制 `VERSION` · 顺手补
- **A.1 Git 远程私库 push**(0.5 天)· **公测前必做**
- home.js 死代码(admin-modal-reset-pw 词条 / showResetPwdResult / `_admin_*_LEGACY`)· 0.2 天 · P3

---

## 公测启动检查清单(只剩 1 项)

| 项 | 状态 |
|---|---|
| LINE 登录 + 补邮箱 modal | ✅ v28.4.x |
| 操作日志 + 分页 + CSV | ✅ v29.0 |
| 超管员工 tab 只读化 | ✅ v28.6 |
| 密码重置链接化 | ✅ v28.7 |
| /reset 落地页 | ✅ v28.7.1 |
| 客户老板查 Pearnly 访问日志 | ✅ v28.8 |
| 改密后旧 token 失效 | ✅ v28.9 |
| 超管 /admin URL 独立 | ✅ v28.2 (+ .1) |
| 客户分配面板 | ✅ v28.1 |
| 银行对账右半屏 | ✅ v118.26.2.1(测试通过) |
| 用户管理/租户连环 BUG 修补 | ✅ v118.26.2.2-2.5(测试通过) |
| **Git 远程私库 push** | ⏳ 0.5 天 |

**做完 Git 私库即启动公测** · ERP 适配器(v118.27.x)并行 · 公测反馈反推 ERP 排序优先级。

---

# 📌 v118.27 系列进度补丁(2026-05-10)

> 本文档主体写于 v118.26.2.5 时代 · v27.x ERP 适配器系列推进至 v27.7.1 · 此章节同步实际进度

## v118.27 系列 ERP 适配器 · 已上线版本(v27.0 → v27.7.1)

| 版本 | 主题 | cache bust | 状态 |
|---|---|---|---|
| v27.0 | 客户/科目/税码映射底座(3 张表 + 6 接口) | - | ✅ |
| v27.0.1 | pearnlyConfirm 全局弹窗 + ERP 映射搬「自动化」+ seed 提速 | - | ✅ |
| v27.1 | MR.ERP xlsx 适配器(stub-first · sales_credit 单张) | - | ✅ |
| v27.4 | Xero OAuth 2.0 适配器 + 推 ACCREC + 错误码 4 语 | - | ✅ |
| v27.4.1 | Xero scope broad → granular | - | ✅ |
| **v27.4.2** | MR.ERP sheet 数动态(customer/product=1 / journal=2 / sales=3 / payment=4) | 11828944 | ✅ |
| **v27.5** | 抽屉 1 推按钮统一 split + 下拉 + `/api/erp/connectors/status` | 11828945 | ✅ |
| **v27.5.1** | hotfix 多发票文件导出只 1 行 BUG · invoices 数组 + 拆 N 行 | 11828946 | ✅ |
| **v27.5.2** | hotfix race condition + SKIN 双闸白名单 | 11828947 | ✅ |
| **v27.5.3** | 「泰国销售明细」导出模板(`excel_template_th.py`) | 11828948 | ✅ |
| **v27.5.4** | 新版本检测横幅 · `/api/version` + 5min 轮询 + no-cache | 11828949 | ✅ |
| **v27.5.5** | hotfix unified IIFE race · placeholder-first | 11828950 | ✅ |
| **v27.6** | 4 模板对齐 · 砍 ERP 录入格式 · 路由分发 | 11828951 | ✅ |
| **v27.6.1** | hotfix 抽屉推送下拉改向上弹出(dropup) | 11828952 | ✅ |
| **v27.7** | 识别中心下拉向上弹 + `/api/ocr/export-by-history-ids` | 11828953 | ✅ |
| **v27.7.1** | hotfix 客户导出 BUG · `db.list_ocr_history` retention_days Optional | 11828954 | ✅ |
| **v27.8.0.4** | MR.ERP 反向工程 + 后端引擎(mrerp_pusher.py + kms_helper.py · 5 步实测全通) | - | ✅ 临时部署 /tmp/v27_8_test |
| **v27.8.1.0** | MR.ERP MVP · mrerp_credentials 表 + 5 db 函数 + 3 endpoints + 凭据 modal | 11828960 | ✅ |
| **v27.8.1.1** | hotfix · setTimeout 600/700ms 自检定时(防 IIFE race) | 11828961 | ✅ |
| **v27.8.1.2** | excel_template_th.py 公式修复(=E*F · 防循环引用) + `_userInfo` 轮询 | 11828962 | ✅ |
| **v27.8.1.3** | 「识别完自动推送」toggle 端到端 · auto_push 字段 + OCR 钩子(2 处) | 11828963 | ✅ |
| **v27.8.1.4** | mrerp_xlsx_generator schema 大改对齐 Korn 真样本(header 18/detail 8/tail 3) | 11828964 | ✅ |
| **v27.8.1.5** | invoice_no `INV-2026-0501` → `690415-001`(BE+MM+DD+seq) + 下载 xlsx debug | 11828965 | ✅ |
| **v27.8.1.6** | 抢救式抓 MR.ERP 错误 hint(red text + JS alert + ไม่พบ/ผิดพลาด)+ raw HTML 存 | 11828966 | ✅ |
| **v27.8.1.7** | 强制 cell 物理保留(`' '` 占位) + sheet1 col 19 spacer · dim=A1:S2 | 11828967 | ✅ |
| **v27.8.1.8** | 🧪 Korn 真样本对照测试 endpoint + UI 按钮 · 决定性诊断(mrerp_pusher OK + xlsx 字节差异) | 11828968 | ✅ |
| **v27.8.1.9** | 后处理 inlineStr → sharedStrings · 处理 `&#NNNN;` 双重 escape 坑 | 11828969 | ✅ |
| **v27.8.1.10** | 🔬 自诊断对比 endpoint(zip 文件级 diff) + UI modal + 两 xlsx 下载 | 11828970 | ✅ |
| **v27.8.1.11** | XML 后处理 · row spans + 完全空 cell + sheet3 只 header + 去 t="n" | 11828971 | ✅ |
| **v27.8.1.12** | ⭐ Korn 模板克隆方案 · 6 metadata 文件不动 · MR.ERP 推送 100% 打通 ✅ | 11828972 | ✅ **真写库验证** |
| **v27.8.1.13a-14d** | 10 个子版本 · MR.ERP 整链路用户旅程完美闭环(凭据 modal 重构 / 字段映射 UX / armas 真客户主表 / mini modal 内联引导 / 智能推荐排前 / Korn 0006 真实推送) | 11828973-11828122 | ✅ |
| **v27.8.1.14e** | 修「上传图片多选强制合并」痛点 · 默认行为反转(gallery 默认分别 · camera 默认合并) | 11828123 | ✅ |
| **v27.8.1.15** | 批量 500 张 + plan 上限+300 + admin 999→9999 + auto_push 默认开 + 大批量进度条 + 新用户引导 modal | 11828124 | ✅ **用户测试通过** |
| **v27.8.1.16** | score=1.0 零点击 + 0.7-0.97 中分 undo toast(3 秒倒计时 + [改一下]/[没问题])+ 列表 recommend/maybe 徽章 | 11828125 | ✅ **用户测试通过** |
| **v27.8.1.17** | 商品对照表 stkmas + detail 行真 product_code + product mini modal(逐个解决)+ 子串闸 fix(占比 ≥ 0.5 才认 0.85)| 11828126 | ✅ **已部署 · 等用户测** |
| **v27.8.1.17.1** | 租户管理 6 bug hotfix(plan_expires_at 字段同步 / monthly/yearly/lifetime 分支 / 员工字段全继承 / tenant.subscription_expires_at 同步 / 幽灵字段移除 / SSoT 对齐) | 11828127 | ⏳ **待部署测试** |

**线上版本号**:**v118.27.8.1.17**(2026-05-11 · 商品对照表 + detail 行真 product_code 全链路完成)
**待部署 hotfix**:v17.1(租户管理一致性修复 · 与 v17 测试并行)
**前期里程碑**:v27.8.1.12 MR.ERP 推送通道打通 · 数据真进 TEST2019 库
**核心成果**:`SI690415-001` 净额 4,635.24 写入 mrerp4sme.com TEST2019 库验证通过 · 整条 OCR → MR.ERP 自动推送链路闭环

---

## 🔥 v118.27.8 系列细化(本窗口拍板 · 不推翻三层架构)

### 三层架构红线(继承 · 全部生效)

| 层 | 名称 | 客户类型 | 状态 |
|---|---|---|---|
| **C** | xlsx 兜底 | 入门 / 谨慎 | ✅ v27.5.3+v27.6 已上 |
| **D** | 浏览器扩展(用浏览器现成 PHPSESSID 推) | 不存密码但要一键 | ⏳ v118.30+ |
| **A** | 后端模拟登录(凭据 KMS 加密存) | 信任 Pearnly · 后台批量 | ✅ 引擎 v27.8.0.4 完成 · 🔥 接 UI 在 v27.8.1.0 |

A 永远不是默认 · UI 必须显眼让用户知道也支持 C。任何一层失败 → 自动降级。

### v27.8 拆分进度(2026-05-11 v14d 收尾更新)

```
v27.8.0   反向工程 + 后端骨架            ✅ 100%
v27.8.1.0 MVP(凭据 + 一键直推)         ✅ 完成
v27.8.1.1 IIFE race + setTimeout 修复   ✅ 完成
v27.8.1.2 公式修复 + _userInfo 轮询      ✅ 完成
v27.8.1.3 自动推送 toggle 端到端         ✅ 完成
v27.8.1.4 schema 大改对齐 Korn 真样本    ✅ 完成
v27.8.1.5 invoice_no 格式 + 下载 xlsx    ✅ 完成
v27.8.1.6 抢救式抓 MR.ERP 错误 hint      ✅ 完成
v27.8.1.7 强制 cell 物理保留 + spacer    ✅ 完成
v27.8.1.8 Korn 真样本对照测试(神器)     ✅ 完成
v27.8.1.9 inlineStr → sharedStrings      ✅ 完成
v27.8.1.10 服务器端字节级自诊断          ✅ 完成
v27.8.1.11 XML 后处理对齐 row spans      ✅ 完成
v27.8.1.12 ⭐ Korn 模板克隆方案 · 推送 ✅ 完成 · 真写库验证
v27.8.1.13a 凭据 modal 重构 + 字段映射 UX + 上传自动归属 bug 修复  ✅ 完成
v27.8.1.13b 测试连接 → 自动探测账套(selectdb.php 解析)            ✅ 完成
v27.8.1.14a/14a.1 dev 抓 MR.ERP 页面 / 客户列表(反向工程)         ✅ 完成
v27.8.1.14b/14b.1 OCR 抽屉 mini modal + 错误码归一 · Korn 0006 验证 ✅ 完成
v27.8.1.14b.2/14b.3 banner + UX 减重(顶栏 SSoT)                  ✅ 完成
v27.8.1.14c 数据源切到 armas 真客户主表 + 深度栈精确解析             ✅ 完成
v27.8.1.14d ⭐ OCR 买方名模糊匹配 + 推荐排前 · MR.ERP 整链路闭环   ✅ 完成
v27.8.1.14e 上传图片多选默认改成分别 · camera vs gallery 分支       ✅ 完成

🔥 P0-A · MR.ERP 全链路完美化(9.5 天):
v27.8.1.15 批量 500 + plan +300 + auto_push 默认开 + 新用户引导     ✅ 完成 · 用户测试通过
v27.8.1.16 score=1.0 零点击 + 0.7-0.97 中分 undo toast              ✅ 完成 · 用户测试通过
v27.8.1.17 商品对照表 stkmas + detail 行真商品码 + 子串闸 fix       ✅ 完成 · 已部署 · 等测试
v27.8.1.17.1 租户管理 6 bug hotfix(套餐升级数据一致性)             ⏳ 待 Zihao 部署测试
v27.8.1.18 OCR 买方名 → Pearnly 客户智能归属 + 学习供应商映射 + 字段对照表 product subtab(v17 遗留) 🔥 下个窗口主任务(1.4 天)
v27.8.2   ERP 主页 UI 三件套(完整映射 UI 已删 · 被 mini modal 替代) 🔥 (2 天)
v27.8.3   推送预览 + 凭据失效检测 + 失败自动降级 xlsx              🔥 (1.7 天)
v27.8.4   真实可达性测试                                          🔥 (0.5 天)
v27.8.5   重复防护 + 批量推送 + ERP 链接 + LINE 推老板             🔥 (1.9 天)

P1 · 公测前 / 战略:
v27.8.6   webhook 卡片化 + 砍蓝按钮(原 v27.8.1.16 降级)           (0.5-1 天)
A.1       Git 远程私库 push · 公测前必做                          (0.5 天)
```

### 🔥 P0-A · MR.ERP 全链路完美化 v15-v22(9.5 天 · v14d 窗口拍板 · 用户全采纳)

> **来源**:`Pearnly_票据到ERP归档_用户旅程分析_v118_27_8_1_14d.md` · 用户拍板"MR.ERP 相关全部排前 · 其他依次排序"
> **详细任务**:见 BACKLOG.md 的 P0-A 章节

**优化目标**(操作数对比):
- 现状:新客户 score=1.0 → 2 次操作 / 批量 50 张 → 50 次推送
- v22 完成后:**新客户 score=1.0 → 0 次操作**(零点击)/ **批量 50 张 → 1 次推送**(批量推)
- 80% 用户场景"想 0 次"· 20% 用户场景"想 1 次"· 0% 用户场景"想 2+ 次"

| 版本 | 内容 | 估时 | 状态 |
|---|---|---|---|
| **v15** | 批量上传 500 + plan 上限+300 + auto_push 默认开 + 新用户引导 | 1 天 | ✅ |
| **v16** | score=1.0 零点击 + 中高分快速确认 toast | 0.6 天 | ✅ |
| **v17** | 商品对照表 stkmas + detail 行真商品码 | 1.5 天 | ✅ 等用户测 |
| **v17.1** | 租户管理 6 bug hotfix | 0.3 天 | ⏳ 待部署 |
| **v18** | OCR 买方名 → Pearnly 客户智能归属 + 学习供应商映射 + 字段对照表 product subtab | 1.4 天 |  |
| **v19** | ERP 主页三件套(4 KPI + 连接器 + 推送日志) | 2 天 |
| **v20** | 推送预览页 + 凭据失效检测 + 失败自动降级 xlsx | 1.7 天 |
| **v21** | 真实可达性测试 | 0.5 天 |
| **v22** | 重复防护 + 批量推送 + ERP 链接 + LINE 推老板 | 1.9 天 |

### 红线 2 · ERP 对接主页 UI 三件套(继承 · v19 实施)

```
① 统计区 · 顶部 · 4 张 KPI 卡(今日已推/待推/失败/自动化率)
② 连接器卡片 · 中部 · Xero/MR.ERP/Webhook + 虚位卡(FlowAccount/PEAK/QB 灰)
③ 推送日志 · 底部 · 表格 + 时间筛选 + 失败行「解决」跳 OCR
```

**注**:原计划在 v19 加的「完整映射 UI / 默认值设置 modal」**已删** —— 14b 已决定 mini modal 替代 + 默认值后端写死(铁律 62)。

### 红线 3 · 真正难点是映射 UI(已被 v14d 解决)

OCR 拿名字 · MR.ERP 要 code:
- 客户名 · v14b/c/d 已用 mini modal + armas + 模糊匹配解决 ✅
- 商品名 · v17 商品对照表用同样方案解决
- 默认仓库 / 部门 / 销售员 · 后端写死(铁律 60 业务化)· 不再要求用户配

---

## 🔌 MR.ERP 反向工程结果(本窗口完成 · 100%)

### 测试环境

```
URL:        https://www.mrerp4sme.com
Username:   test01 / Password: test01
公司:       1010-01-000006 บริษัท ทดสอบการใช้ จำกัด
数据库:     TEST2019(URL ?comidyear=6&seldb=1)
内部 idus:  15(test01 用户 · 从 formupload.php hidden input scrape)
```

### 全 5 步 endpoint 字典(实测通过 ✅)

| 步 | URL | Method | Body | Response |
|---|---|---|---|---|
| 0a 预热 | `/` | GET | - | (set PHPSESSID) |
| 0b 登录 | `/login/checklogin.php` | POST | `txtusers=X&txtpasswords=X&btnsubmit=Submit` | 200 + HTML(同 URL · 不 redirect) |
| 0c 选公司页 | `/login/selectdb.php` | GET | - | 200 |
| 0d 选公司 | `/login/mainmenu.php?comidyear=6&seldb=1` | GET | - | 200 + 主菜单 HTML(被踢回 login = 鉴权失败判定) |
| 0e scrape idus | `/impartran/formupload.php?idmenu=370` | GET | - | 200 + HTML(含 `<input hidden name="idus" value="15">`) |
| **1 上传** | `/impartran/component/uploadexcel.php` | POST | **multipart**: `uploadfile=<file>` + `idus=15` + `selmenu=118` | 200 + 0 字节(文件存 server session) |
| **2 预览** | `/impartran/formrdpc.php` | POST | `idus=15&selmenu=118`(form-urlencoded) | 200 + HTML(form 含 `cbimport[N]` checkbox) |
| **3 确认** | `/impartran/component/importpc.php` | POST | **multipart**: `idus + selmenu + cballfrmimport1=on + cbimport[N]=N` | 200 + 短字符串(数字="2"=新 row id 成功 · 非数字=错误) |

### 路径分类(铁律 51)

```
impartran/  = 交易类业务单据(销售/采购/收付款 import · idmenu=370 是赊销)
imparse/    = 主数据类 / 现金销售 import 走这里(idmenu=371)
expartran/  = 交易类导出(idmenu=404 商品销售导出)
```

### idmenu / selmenu 字典(部分 · v27.8.2 补全)

| 业务 | idmenu | selmenu | 路径 | sheet 数 | 状态 |
|---|---|---|---|---|---|
| SC 赊销 import | 370 | 118 | impartran | 3 | ✅ 实测 |
| SC 销售导出 | 404 | 118(下拉切) | expartran | - | ⚠️ URL 知 · cURL 待抓 |
| SE 现金销售 import | 371 | ❓ 未抓 | imparse | 4 | ⏳ |
| 采购 / 收款 / 付款 / 凭证 | ❓ | ❓ | ❓ | ❓ | ⏳ v27.8.2 |

详细 endpoint 字典 + 8 个踩坑细节 + scrape idus bug 修复 · 见 `HANDOVER_v118_27_8_1_0.md`。

---

## 🆕 铁律清单(累计 62 条 · v14d 窗口新增 61-62)

旧 1-58 见 v118.27.8.0 HANDOVER · 不变。

### 本窗口新增(2026-05-11)

59. **MR.ERP sales_credit xlsx 必须用 Korn 模板克隆生成**(2026-05-11):`mrerp_xlsx_generator.py` 的 sales_credit 路径走 `_generate_xlsx_sales_credit_korn_clone()` · 6 个 metadata 文件不动(workbook.xml / [Content_Types].xml / styles.xml / theme.xml / 2 个 rels) · 只重写 sharedStrings + sheetData · 模板必须存在 `/opt/mrpilot/test_data_mrerp_sample_SC.xlsx` · 不许直接 openpyxl save(它会重写 workbook.xml 丢失 PhpSpreadsheet 兼容性)

60. **UI 文案业务化** · 不能用程序员术语(2026-05-11):「映射」→「对照」/「对照表」(会计师懂)· 「凭据」→「账号」 · 「ERP 端编号」→「客户在 ERP 里的编号 / 商品码」 · `comidyear` / `seldb` 折到「高级设置」隐藏 99% 用户不动 · 文案要假设「会计师不懂技术」 · 所有出现技术名词的地方都要业务化

61. **MR.ERP 主数据用 `showdata.php` 通用 pattern 抓**(2026-05-11 · v14c/v14d 实测):所有 `/X/allview.php?idmenu=N` 列表页 = 空壳 + AJAX 后填(`<div id="showdata">` 由 `showdata()` 异步填充)· 客户端反向工程要点:① warm-up GET 列表页(种 Referer / PHPSESSID)· ② POST `/X/component/showdata.php`(form data: `showdata_numrows=30 / showdata_pages=N / searchdataval=""`)翻页拼接 · ③ 用顶层 `<span>` 深度栈解析(避开 URA hover 嵌套 span 干扰)· ④ 停止条件:返回空 / `id="nodata"` / `len(chunk) < 10` · 任何 MR.ERP 主数据(客户 armas / 商品 stkmas / 供应商 apmas / 仓库 store 等)都走这套

62. **字段对照表 = 后台页 · 不是主入口**(2026-05-11 · v14b 大反思):99% 用户**不**主动进「字段对照表 / 自动化 → ERP 对接 → 字段映射」 · 那是给老司机审计 / 批改用的后台页 · 用户的客户/商品/税码映射应在 **OCR 抽屉推送时按需配**(失败那一刻就地解决) · 任何"先去配置 → 再使用"的 UX 都是失败设计 · mini modal 内联引导 + 智能推荐 + 手动输入备份才是正解

### 本窗口 v15-v17.1 新增(2026-05-11)

63. **模糊匹配子串规则必须有占比闸**(2026-05-11 · v17 边界 fix):`_match_buyer_score` 的 0.85 子串包含规则需加约束:短串占长串 ≥ 50% 才认 0.85 强子串匹配 · 否则降级 SequenceMatcher 兜底。否则会出现「Random XYZ Co」误推荐「XYZ Limited」(3 字符占 9 字符 0.33 触发 0.85)。这条铁律适用任何主数据模糊匹配 ·  客户 / 商品 / 供应商通用。

64. **用户字段必须 SSoT · 顶栏 vs 设置页**(2026-05-11 · v17.1):`/api/me/plan` 是套餐相关字段的权威源 · `_build_user_info` 同样字段必须对齐。两个 endpoint 都要返 `plan_expires_at` / `plan_days_left` / `trial_expires_at` / `trial_days_left` 这一套 · 顶栏走前者 · 设置页走后者 · 双方显示必须完全一致 · 否则会出现「顶栏年付364天 / 设置页月度订阅—」自相矛盾 BUG。

65. **员工继承老板套餐字段必须全套继承**(2026-05-11 · v17.1):`_build_user_info` 检测 `role=member` 查 owner 时 · 不能只继承 `plan` 一个字段 · 还要同时继承 `plan_expires_at` / `trial_expires_at` / `monthly_quota`。否则员工的设置页 / 顶栏跟老板对不齐(员工看到自己注册时的旧数据)。已在 SELECT 多列 + return dict 同步赋值实现。

66. **`admin_upgrade_user` 必须同步 `tenants.subscription_expires_at`**(2026-05-11 · v17.1):铁律 35 写「tenants 表无 plan / max_seats」 · 但 subscription_expires_at 是真存在的列(在 db.py 5659 建 tenant 时写入)· 之前 admin_upgrade_user 漏更新这个列 · 导致 tenant 表过期值永远停在注册时初始值。任何套餐升级 / 降级路径必须同时维护 `users.plan_expires_at` + `tenants.subscription_expires_at`。

67. **tenants 表无 `trial_expires_at` / `plan_expires_at` 列**(2026-05-11 · v17.1):这两个字段只在 users 表 · `get_tenant()` 返回的 dict **不要**引用 `tenant_info["trial_expires_at"]` 这种幽灵字段 · 否则代码误导(实际 always None 走 fallback 到 user 表)。tenants 表能用的过期字段只有 `subscription_expires_at`。

68. **服务器单独覆盖文件清单**(2026-05-11 · v17):有些文件不进 deploy.sh 主流程 · 必须 Zihao 手动 scp 覆盖。当前清单:`mrerp_xlsx_generator.py`(detail 行 product_code 真码注入需要)。新增此类文件时必须在 HANDOVER 显式标出 · 否则部署后功能缺失没人知道。

---

## 🆕 旧铁律清单(累计 58 条 · 见 v27.8.0 收尾时新增 51-58)

旧 1-43 见 v118.26.2.5 HANDOVER · 不变
44-50 不变(本窗口部分修正见下面)

44. **三层 ERP 对接架构永久并存**(2026-05-10):A 后端模拟 + C xlsx 兜底 + D 浏览器扩展 · 任何一层失败自动降级 · A 不是默认
45. **ERP 对接主页 UI 三件套**(2026-05-10):统计 + 连接器卡片 + 推送日志 · 缺一不可(留 v27.8.2 做 · MVP v27.8.1.0 不做)
46. **MR.ERP 反向工程 ✅ 100% 完成**(2026-05-10 本窗口):认证 = 单一 PHPSESSID cookie · 无 CSRF · 无签名 · 全 5 步 endpoint 实测通过
47. **v27.8 真正难点是映射 UI**(2026-05-10):OCR 名字 → MR.ERP code · 必做主数据缓存 + fuzzy match + 用户确认 + 推送预览(留 v27.8.2 做)
48. **真实可达性 60%/90% 不是 100%**(2026-05-10):首次 60% · 重复 90% · 失败必兜底 .xlsx
49. **后端到后端跳过浏览器 JS 校验**(2026-05-10):v27.8 直接 HTTP POST · 不走前端 · 浏览器抓的弹窗错误跟我们无关
50. **MR.ERP idmenu 决定子模块**(2026-05-10):371=现金销售(imparse 路径 · 4 sheet) · 370=赊销(impartran 路径 · 3 sheet) · 各模块 sheet 数 + 路径不同 · v27.8 客户端按 module dispatch

### 本窗口新增 51-58(2026-05-10)

51. **MR.ERP 路径分两套**:`impartran/`(交易类业务单据 · 销售/采购/收付款 import) ≠ `imparse/`(SE 现金销售 + 推测主数据类) ≠ `expartran/`(交易类导出) · 不是单一 endpoint · 同模块名可能跨路径
52. **idus 是 MR.ERP 内部用户 ID**(test01=15 · 不是 username):scrape 来源 = 任意业务页的 `<input type="hidden" name="idus" id="idus" value="N">` · 必须用 BeautifulSoup 解析(name 和 value 之间隔了 id 属性 · 严格正则会漏)
53. **idmenu ≠ selmenu**:idmenu = URL 路由 ID · selmenu = 业务子类型字典(118=ขายเชื่อ-รายได้ขายในประเทศ赊销国内销售)· 同 idmenu 可通过 ชื่อเมนู 下拉切 selmenu(import 和 export 共用同一字典)
54. **MR.ERP 完整 5 步流程铁律**(不可乱序):
    1. GET / 预热(必须 · PHP session 初始化)
    2. POST /login/checklogin.php(`txtusers/txtpasswords/btnsubmit=Submit` 字段名都是复数 · 带 Referer)
    3. GET /login/selectdb.php(选公司页 · 模拟用户流程)
    4. GET /login/mainmenu.php?comidyear=N&seldb=N(激活公司 + 真实判登录成功 · 被踢回 login = 失败)
    5. GET /impartran/formupload.php?idmenu=N(scrape idus)
    6. POST upload → POST formrdpc → POST importpc(实际推送 3 步 · 同 PHPSESSID)
55. **MR.ERP importpc.php 必须 multipart**(虽然字段全是文本)· 服务端不接 form-urlencoded · requests 用 `files=[(name, (None, value))]` 触发
56. **MR.ERP 上传不是 AJAX 是浏览器整页跳转**(uploadexcel.php POST → 浏览器跳到 formrdpc.php)· 但**后端代码不需要模拟跳转** · 直接顺序 POST 即可
57. **MR.ERP checklogin.php 不靠 r.url 判成功**(POST 后永远停在 checklogin.php 自己 · 即使成功也不 redirect)· 真实判定 = 看下一步 GET mainmenu 是否被踢回 login + 看 body 是否含 txtusers
58. **MR.ERP confirm 返回值约定**:数字字符串(如 "2") = 成功 · 表示新 row id · 非数字 = 错误信息(具体格式待 v27.8.2 故意失败 1 次抓样本)· 单号重复行为未确认(实测 690507-001 反复 confirm 都成功 · 可能允许重复)

---

## 当前已知小问题(2026-05-11 v17 / v17.1 更新)

**MR.ERP 主线**:
- v14d 整链路完美闭环 ✅ · Korn 0006 真实推送验证 ✅
- v15 批量上传 500 + plan +300 + admin 999→9999 + auto_push 默认开 ✅
- v16 score=1.0 零点击 + 0.7-0.97 中分 undo toast ✅
- v17 商品对照表 + detail 行真 product_code + 子串闸 fix ✅ **已部署 · 等用户测**
- v17.1 租户管理 6 bug hotfix ⏳ **待部署**
- **服务器需单独 scp 覆盖 `mrerp_xlsx_generator.py`**(detail 行 product_code 真码注入 · 不在 deploy.sh 范围 · 不覆盖则商品映射 v17 链路只生效到映射保存 · xlsx 仍写 `123` 占位)
- **完美匹配场景仍要点 modal 确认**(v16 已解 · 待复测)
- **批量推送缺**(v22 解):50 张要点 50 次
- **凭据失效场景没自动检测**(v20 解)
- **推送失败无自动 xlsx 降级**(v20 解)
- **多客户混合上传归属不准**(v18 智能归属解)
- **重复推送防护缺**(v22 解)
- **字段对照表 product subtab 未做**(v17 BACKLOG 写要做 · 实际未做 · 推到 v18 · 理由:99% 用户从 mini modal 走 · 不阻塞主路径 · 铁律 62 已锁定)

**v14d 实施偏离原 BACKLOG**(已锁定为铁律 62):内存缓存 5 分钟 + 按需拉 + mini modal 显示全部 + 智能推荐排前 · 优于原计划 erp_master_cache 24h + 测试连接预热 + top 3 fuzzy modal。

**v15 实施细节**(本窗口决策):
- plan 上限调整全档单调升:trial 15→30 / monthly 30→500 / yearly 50→800 / lifetime 100→1000 / **admin 999→9999**(铁律:admin >= lifetime · 不能更少)
- 大批量提示阈值 100 张:进度条 IIFE + beforeunload + 首次一次性 toast
- ERP 新建表单 auto_push 默认 true(不动老用户已关的状态)

**v16 实施细节**:
- 客户 mini modal 完美匹配零点击:`_fetchAndRender` 拿 auto_select_code → `_autoApplyPerfect` 静默保存 + onSelected 自动重推
- 中分 0.7-0.97 不弹完整 modal · 弹右下角 undo toast(深色底 + 进度条 · 3 秒倒计时 + [改一下] / [没问题])
- 列表 score 徽章:≥0.7 橙色「推荐」/ ≥0.45 浅黄「可能」
- 后端 `_normalize_buyer_name`(去 4 语公司后缀)+ `_match_buyer_score` + `_rank_customers_for_buyer`

**v16 边界 fix**(本窗口主动发现 · 留 v17 顺手修):
- v16 子串规则只判「buyer 包含 name 或 name 包含 buyer」就给 0.85 · 短串挂中长串假阳性(如 "Random XYZ Co" vs "XYZ Limited" 误推荐)
- v17 加占比闸:短串占长串 ≥ 0.5 才认 0.85 · 否则降级 SequenceMatcher
- 测试验证:Random XYZ Co vs XYZ Limited 从 0.85 降到 0.43(不再误推荐)· 完美匹配 1.0 不受影响

**v17 实施细节**:
- DB:`erp_product_mappings` 表(tenant_id / erp_type / item_name / item_name_norm / erp_code / erp_name) + 4 CRUD + `find_erp_product_mappings_batch`(批量预检用)
- `get_mrerp_mappings_bundle` 加 `products` key
- 后端 stkmas(idmenu=24)抓取 + 5 分钟缓存(走铁律 61 同样 showdata.php pattern)
- 4 endpoints:`GET /api/erp/mrerp/products?item_name=X` / `GET/POST/DELETE /api/erp/mappings/products` / `POST /api/erp/mrerp/products/check`(批量预检)
- 前端 `_pushOne` 顶部 hook `_checkProductsBeforePush` · 多 unmapped item 串行 `_runProductMappingFlow` 逐个弹 product mini modal
- `openMrerpPickProduct` 独立 IIFE(350+ 行 · 接 `{itemName, indexHint, totalHint, onSelected, onSkip, onCancel}`)· 完美匹配零点击短路 + 「第 i/n 个待配」进度提示 + 跳过 + 取消
- 服务器 `mrerp_xlsx_generator.py` 改:加 `_norm_product_name`(re sub 标点 + lowercase · 跟 db.py 一致) + `_build_product_lookup` + `_resolve_product_code` · `build_sales_credit_detail_rows` 循环外建 lookup 一次 · 内循环 O(1) 查 item.name 写入 row 的 `product_code`(找不到 None 下游 `or '123'` fallback)
- 4 语 i18n × 19 词条

**v17.1 实施细节**(用户截图报 + 主动深度排查 6 bug):
- Bug 1:`_build_user_info` 只读老 `users.expires_at` · 没读 `plan_expires_at` → 设置页有效期「—」
- Bug 2:前端 settings 页 plan 分支只覆盖老名 pro/team/firm/enterprise · 新名 monthly/yearly/lifetime 走兜底「月度订阅」
- Bug 3:员工继承老板时只继承 `plan` 字段 · 没继承 `plan_expires_at` / `trial_expires_at` / `monthly_quota` → 员工设置页跟老板对不齐
- Bug 4:`admin_upgrade_user` 漏更 `tenants.subscription_expires_at` → tenant 表过期永远停在注册值
- Bug 5:`_build_user_info` 读 `tenant_info["trial_expires_at"]` 幽灵字段(tenants 表无此列)
- Bug 6:`/api/me/plan` 跟 `_build_user_info` 字段不一致 SSoT 违反 · 修法是后者加 `plan_expires_at` / `plan_days_left` 对齐前者
- 新前端 4 语 × 5 词条(settings-sub-monthly / yearly / lifetime / settings-days-left / settings-lifetime-forever)
- 后续监控点:升级套餐后 顶栏 + 设置页 + 员工 设置页 三处显示是否完全一致

**非 MR.ERP**:
- v118.26.2.5 用户管理/租户连环 BUG 全修通过用户测试 ✅
- `/api/me/plan` 慢 2.5-3.4s(测试中心 api_slow 触发)· 加 5 分钟前端缓存 · 0.2 天 · P2
- `deploy.sh` 不复制 `VERSION` · 顺手补
- **A.1 Git 远程私库 push**(0.5 天)· **公测前必做**
- home.js 死代码 · 0.2 天 · P3
- 老的 `HANDOVER_v118_27_8_1_14e.md` 已过期 · 由 Zihao 删除(铁律 13)
- 新的 `HANDOVER_v118_27_8_1_17_1.md` 给下个窗口接 v18 用 · 必读