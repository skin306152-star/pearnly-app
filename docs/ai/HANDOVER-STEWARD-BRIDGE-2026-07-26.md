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

## 三、2026-07-27 凌晨进展(接手先读这节 · 上面第一、二节是 07-26 的历史)

**⚠️ 接手第一件事:跑 `git log --oneline -15` 两仓,以 git 为准。下面的清单可能又落后了。**

### 已入库(pearnly-app,基线 `accc94db` 之后)

| commit | 内容 |
|---|---|
| `927fa029` | 桥写路云端侧:job kind 白名单 + 写桥角色闸 + 写门面(`services/erp/bridge/write_gate.py`) |
| `08977074` | Express 写载荷键契约冻成常量(mapper 加键忘登记不再静默熄火) |
| `99539044` | 超时不再吞在途写活(expired ≠ 其实已写进账套) |
| `8bdffa7d` | **B5 #16 设置页计费区上线**:OCR 余额 + 三步充值 + 充值记录(`static/ai/ai-billing*.js`,22 单测 + 8 条真浏览器 E2E,截图在 `_artifacts/b5_billing/`) |
| `1ddc1036` | **B3 第一段:管家长任务异步化**(`services/steward/worker.py` + 任务状态机 + `GET tasks/{id}` + `POST tasks/{id}/cancel` + 迁移 0089,111 例绿) |
| `6fcad45d` | `startup.py` 拆分:git-deploy.sh 模板抽 `services/deploy_script.py`(挂管家工人后撞 500 行硬闸) |

### 已入库(pearnly-companion,基线 `50fb300` 之后)

`eeb097c` 写路库上桥 → `4684781` 落批骨架收拢单份 → `ab4f18e` 云端写分支上桥(v0.3.0)→ `df01f6f` 写事务持盘上互斥 → `b6fa974` **HP 现购落 APBAL 的 HP 桶而非 RR 桶(桥+小助手两份同修)** → `f5c4443` bump 1.1.56。

桥仓 318 例绿;小助手 385 例绿。**两仓均未 push。**

### 桥 P2-A 真账 E2E 结果(用真账镜像不是合成账套)

四单别全部落盘,**117 项只读读回校验零失败**;幂等重放跳过且不多行;会计删单后重推落新号;三种「不该写」场景全拦且零写盘。审查 11 条→复核确认 6 条→全部修完。

### 🛑 未闭环(优先级从高到低)

1. **小助手 1.1.56 未发版** —— 修的是**现役生产 bug**(现购应付记进赊购月桶,HP 桶恒 0)。Zihao 07-27 拍板:**等 Accserver 开机、TEST 靶场复验过再发**。发版三步:靶场真写验 → `packaging/release.ps1` → 验在用小助手真更新。
2. **P2-A 三条会计口径未修**(真账 E2E 揪出,上真靶场前必须处理):① 非 1 月起账的账套月桶会全错 ② 年结跨年票期间会错 ③ 写单不看关账锁期。
3. **P2-A 修复后没在真账重跑 E2E**;云端有一笔提交卡格式类硬闸,push 前须补一笔。
4. **B3 收官在跑中**(授权卡 + 成本硬封顶 + 前端 running 态/授权卡/主动汇报 + 真浏览器截图验收)。若中断,脚本在 `workflows/scripts/steward-b3-closeout-wf_90ac005f-b88.js`。
5. **P2-B 四类新单据未开工**(收款/付款/手工凭证/库存调整),脚本已存 `bridge-p2b-new-doctypes-wf_ac469445-e7d.js`,第一步是拿真账镜像逐列核对逆向文档再定表(合成规格骗过我们一次)。
6. **B4 管家工具全量** 未开工。

### /ai 浅评审揪出的真缺口(Zihao 要求:管家闭环后再动)

1. 🔴 点「开当期工单」失败时页面零反应(唯一静默失败)
2. 🟠 OCR 余额不足只报通用错误,失败卡没接「去充值」(钱包已做好,差一条链接)
3. 🟠 审核/交付包空态说「请先在其它入口开单」却不点名旁边的工单 tab、不给按钮
4. 🟡 一批页内小分区空态干瘪「暂无 X」,分不清没跑/没料/失败
5. ⚪ 未指定过账去向的票仍是死胡同 —— Zihao 07-26 拍板挂起,非遗忘

**前向约定**:B3 授权卡上线时,管家页面「这一版只读,管家只查不改数」两条文案必须同步改(四语),否则产品在撒谎。

### 闭环判据(Zihao 07-27 拍板 · 已写入长期记忆 `visual-acceptance-with-real-corpus`)

**功能必须真浏览器跑通 + 截图为证 + 视觉验收合格才算完成**,且喂真语料不喂造的数据。
语料库 `C:\Users\skin3\Desktop\Pearnly-产品语料测试数据`;选料单与 E2E 跑法/坑清单见 scratchpad `visual_prep/ACCEPTANCE-BRIEF.md`(金标:`SM/A_客户给的原料/IMG_2640–2650` 11 张进项票 → 答案 `input_vat 29,263.28 / purchase 418,046.86`;销项锚 60,114.61)。

### 本地资产(断网期靠这个)

- 真账镜像 `D:\pearnly-erp-lab\_mirror_20260726\`(EXP69 全 7 套 + BANKREC 测试套 + EXP68 若干,约 285MB)
- 本地真栈:FastAPI `127.0.0.1:7860` + docker `pearnly-db`,测试号 `stw_e2e` / `StwVerify#2026`(entry=ai)

## 四、剩余批次(按序 · 已完成的见第三节)

1. ~~桥 P2-A 写路原语~~ **已完成**(六条缺陷已修,三条会计口径待补)
2. B3 管家:~~异步化~~ 已完成;授权卡 + 成本封顶 + 前端**进行中**
3. 桥 P2-B:新单据菜谱(收款/付款/手工凭证/库存调整)
4. B4:管家工具全量(所有云端能力接进管家)
5. /ai 浅评审的 4 条真缺口(管家闭环后做)
6. **全功能真浏览器视觉验收**(喂真语料,桌面+移动+四语截图,逐张目检)
7. 收官:`/simplify` → 两仓 push → 盯 CI 到绿 → 更新 STATE 顶部状态卡

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
