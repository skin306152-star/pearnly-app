# 交接单 · 智能管家 + Express 桥(2026-07-26)

> 换账号/换窗口后从这里接。**目标判据**:打开 `/ai`,在对话里派活,能看见 Express 真账,
> 写操作弹授权,全所可用。达到即闭环。

## 一、已完工并入库(commit 均未 push)

| 批次 | 内容 | commit | 验收 |
|---|---|---|---|
| B1 | 状态语言底座:`ai-states.css` 八色令牌 + 徽章/六进度/五动画/按钮七态 + `#/states` 词典页 + `docs/design-system/STATE-LANGUAGE.md` | `3d990af1` | 真浏览器 8/8,新旧逐属性对比零串味 |
| 清单 | `docs/ai/OLD-SITE-PARITY-CHECKLIST.md` 26 项能力退役闸(含吸收方式四级:自动/配置/对话/界面) | `db1f0308` `c4bcc3e5` | — |
| 桥 P0 | pearnly-companion `bridge/`:只读桥(账套发现/全表查询/密钥门/快照缓存) | `a558f45` | 7 真账套只读冒烟,42 测绿 |
| 桥 P1 云 | `routes/erp_bridge_routes.py` + `services/erp/bridge/*` + 迁移 `0087` | `d5225490` `d8f3b48f` | 62 测绿 |
| 桥 P1 端 | companion `bridge/cloud_client.py` + `cloud_jobs.py`,VERSION 0.2.0 | `0ebb571` | 74 测绿 |
| 桥 P1 联调 | 云端经桥读真账:6902ASC 客户 552 / ARTRN 2026Q1=139(与直连同源)、写桥唯一闸生效、共享今日 0 文件被改 | — | 全项 PASS |
| B2 后端 | `services/steward/*` 六只读工具 + `routes/steward_routes.py` + 迁移 `0088` | `de908290` `a66afa9d` | 84 测绿 |
| B2 前端 | `static/ai/ai-steward*.js/css` 命令条 + `#/steward` 双栏 | `3eaca780` | 见下,**需返工** |

### 追加(22:5x 全部交付完成,两仓工作树干净)

| 批次 | 内容 | commit |
|---|---|---|
| 逆向文档 | `docs/integrations/express-push/40~44` 四类单据只读逆向(收款 1077 单 / 付款 2761 单 / 手工凭证 3284 张 / 库存调整 193 张 OU+ZZ) | `5c460751` |
| B2 返工 | 三缺陷全修 + 复验 PASS(表格反证过 · 8 个 chip 中泰全出结果 · 待审数与矩阵逐数对上);**`app.py` 499→150 行**,路由清单搬 `routes/registry.py`,639 条逐条全等 | `7fc26523` |
| 桥兼容性 | 单 exe 绿色包 11.6MB + 首次配置向导 + 自动找账套(真机扫出 18 个数据根)+ 开机自启/计划任务;123 测绿 | companion `82a7a4f` |
| 桥 BOM 修 | 手填 config.json 带 BOM 起不来 → 改收 utf-8-sig(+反证测试),124 测绿 | companion `50fb300` |

**⚠️ 待办状态(2026-07-27 凌晨更新)**

1. **共享半恢复**:`\\192.168.0.212\pas212`(数据盘)已恢复;`\\Accserver\d$`(程序+TEST 靶场)仍关机不可达。桥 P2 的真靶场写冒烟继续等 Accserver 开机。
2. ~~桥兼容性「7 套账 552 客户」补验~~ **已闭环(2026-07-27)**:经 212 的 `2569\EXP69` 数据根用桥快照真跑——7 套账 / 6902ASC ARMAS 活行 552 / ARTRN 2026Q1=139,三数全中。证据在 session scratchpad `lan_sweep\`。
3. **新资产**:关网前已镜像 `D:\pearnly-erp-lab\_mirror_20260726\`(EXP69 全 7 套 + BANKREC 测试套 61 表/1.92MB + EXP68 候选,共约 285MB)——离线开发/E2E 用这里。Express 程序包只在 Accserver(212 全盘无 exe),「本地跑 Express」等它开机后从 `d$\ACCOUNT\69EXP` 拷。
3. 桥 exe 当前是 3.11 构建 = **Win10+**;要覆盖 Win7 需在装 32 位 Python 3.8 的机器上跑 `build_bridge.ps1 -RequireLegacyWindows`,依赖侧已独立核实通过,PyInstaller 侧官方只承诺 Win8+,未实测。

## 二、B2 验收揪出的三缺陷(已全部修复 · `7fc26523` · 复验 PASS)

1. **P0 产物表格全废**:后端发 `columns:[{key,label}]`+dict 行,前端 `ai-steward-render.js:168-193` 按旧形状渲染 → 页面全是 `[object Object]`。**假绿根源**:前端 E2E 桩 `_b2m1_steward_local.spec.js:76-81` 用了产品里不存在的旧形状自证。
2. **P1 期间词**:`services/front_desk/interpret.py:123-130` 的 `_THIS_MONTH_WORDS` 不认「本期/本月/当期/งวดนี้」→ 产品自带 4 个 chips 有 2 个停在追问。
3. **P1 工单过滤**:`services/steward/copy.py:96-99` 回复不带过滤条件;且工具 `status='review'` 与矩阵「待审」口径分裂(矩阵含 stuck),答「0 张」而矩阵写「待审 2」。

顺带硬化:探针 401 与闸关不可区分(管家静默消失);`app.py` 顶到 499/500 需腾空间。

## 三、被打断需重跑的三队

用 Workflow 重派即可(脚本已存,**换 session 后 resumeFromRunId 失效,直接重跑**):

- B2 返工 + 复验:`workflows/scripts/b2-rework-wf_2da99a4a-765.js`
- 桥兼容性(Py3.8/单 exe/免安装/自动找账套):`bridge-portability-wf_4ba18f93-682.js`
- 四类单据逆向(收款/付款/手工凭证/库存调整,纯只读):`express-doctype-recon-wf_ddb44123-d75.js`

## 四、剩余批次(按序)

1. 桥 P2-A:写路原语(从小助手搬安全落批骨架,抽通用编排器)+ 已有四种菜谱上云
2. B3:授权卡(复用 LINE 侧 nonce 机制)+ 管家主动汇报 + 成本硬封顶;**长任务需异步化**(M1 是同步返回,左窗 running 态在真链路不出现)
3. 桥 P2-B:新单据菜谱(收款/付款/手工凭证/库存调整),靠逆向队产出的落表结构
4. B4:管家工具全量(所有云端能力接进管家)
5. B5:老站对齐清单 6 项「待排」
6. 收官:`/simplify` → 两仓 push → 盯 CI 到绿 → 更新 STATE 顶部状态卡

## 五、必须知道的现场事实(已写入长期记忆 `express-topology-and-bridge-deploy`)

- **Accserver = 192.168.0.11** 跑 Express 程序,是 **Windows Server 2003**(连 .NET 都没装)→ 桥装不上去,也不需要。
- **192.168.0.212**(S 盘)= 生产账套数据,只开 445,无管理通道 → 同样装不了。
- **桥装第三台常开 Win 机**,经 SMB 读写。跨网写 DBF 已被现役小助手生产实证。
- **TEST 靶场账套**(Zihao 授权可读写删):`\\Accserver\d$\ACCOUNT\69EXP\test`,公司 บริษัท ซินเซียร์ไอซ์ จำกัด/0105546015062,规模小(ARMAS 7/APMAS 691/ARTRN 8/APTRN 0)。桥 P2 写路闭环拿它验,不碰生产账套。
- 唯一需要 Zihao 拍板的关卡:**第一次往生产账套真写**。TEST 靶场验证不用问。

## 六、纪律提醒

- 两仓均**未 push**;共享工作树,`git commit --only` 显式列文件,禁 `add -A`/reset/rebase/stash。
- 别的窗口同时在动 `services/workspace/purge*`、`static/ai/ai-purge.js`,不要捎带。
- `test_file_crypto` / `test_agent_capability_audit` 在本机是 cp874 假红,CI Linux 绿,不用追。
