# P2 修订 · 复活 pearnly-companion 当 Agent(RPA)+ DBF 直写(两条都做)

> 起因:发现既有项目 **`D:\pearnly-companion`**(独立 repo)——一个比 P2a 强得多的本地 Agent,图像识别 RPA(pyautogui+OpenCV 模板匹配+SIFT+Tesseract OCR 回验),自动定位字段、自动校准、有假 Express 开发台、45 测试过。当初**卡在没有真 Express 测**(现已解除:Owner 机器上 Express 开着)。
> Owner 拍板(2026-06-20):**按新方向走 = 复活 companion 接我们后端**;**DBF 直写也要,不许漏**。
> 本文取代旧 `03-phase2-local-agent.md` 的"从零搭 RPA"路线。P2a(`feat/express-agent`)降级为参考(白名单/幂等思路可借)。

## 0. companion 现状(PM 已读真码)
- **路径**:图像识别 RPA(非硬编码键序)。`strategy/{local,rdp,mock}.py` 按窗口标题 `Express Accounting` 识别;`field_engine.py`(模板+SIFT+verify);`calibration.py`+`calibration_ui.py`(首跑自动定位字段存 calibration.json·DPI 自适应);`input_executor.py`(录入+等业务联动);`ocr_verifier.py`(Tesseract 泰文读屏回验·铁律#9);`main.py`(health→calibrate→poll loop→ack·`--mock/--debug/--dry-run`);`tools/fake_express.py`(PySide6 假 Express 开发台)。
- **针对销项**(`ขายเงินเชื่อ` IV·字段 customer_code/单据号/日期/item_code/qty)。**我们要进项**(`ซื้อเงินเชื่อ` RR·供应商/票号/日期/明细/金额)——架构照搬,**模板+字段映射重做**。
- **DBF 直写:companion 里零**(纯 GUI RPA)。我们 P2a 也没做。→ 全新建。
- **队列契约**(`queue_client.py`):`POST /api/companion/poll {companion_id}`→`{item:{id,invoice_no,payload,attempt_count}}`;`/ack {id,success,extracted_invoice_no|error,error_code}`;Bearer token。

## 1. 接线:companion 队列 → 我们 P1 真后端(已上线 prod)
我们 P1 Agent API:`/api/erp/agent/heartbeat`、`/lease {max}`→`{jobs:[{log_id,history_id,invoice_no,payload}]}`、`/ack {log_id,result,express_docnum,error}`(Bearer=`config.agent_token_hash`,flag `ERP_PUSH_ENABLED`)。
- **改 `queue_client.py`**:`poll()`→调 `/lease {max:1}` 取首个 job(`task.id=log_id`,`task.payload=job.payload`);`ack_success(extracted_invoice_no)`→`/ack {result:'success',express_docnum}`;`ack_failure`→`/ack {result:'failed',error}`;`health`→`/heartbeat`。契约小适配,其余 companion 模块不动。
- **payload 适配**:我们 P1 出的是采购载荷(`doctype RR/HP·supplier{code,name,tax_id,prename,supplier_new}·lines[]·base/vat/total·docdate_be/vat_period_be·ref_no`)。`field_engine` 现读销项 customer_code/items → 写**进项字段映射**把我们的 payload 喂进采购页字段。
- **安全沿用 P1+P2a**:账套白名单只 DATAT(companion 端再钉)、ref_no 幂等(录前查重防重录)、OCR 回验不过不 ack success。

## 2. Track A · RPA(复活 companion · 主路径 · 先做)
1. **摸现状**:读 companion 全貌,在能跑的环境跑它 45 测试,确认 mock demo 仍工作(`scripts/run_p27_demo.bat`)。报现状给 PM。
2. **接线**:按 §1 改 `queue_client.py` 指向我们 `/api/erp/agent/*`;payload 适配器(采购)。
3. **进项页模板 + 字段映射**:用 `extract_templates`/calibration 对**采购赊购页**(`1.ซื้อ → 4.ซื้อเงินเชื่อ`,见 [[express-push-project]] 真机情报)做模板;`field_engine` 加进项字段顺序(供应商代码→Tab 带名→票号→日期(佛历·**DATAT 账期 2558–2559**)→明细→VAT→保存读回)。
4. **真 Express 校准验证**(Owner 机器·解除原阻塞):跑校准向导,SIFT 自动定位字段;推一张样例(P1 队列)→ companion lease→录入 DATAT→OCR 回验→ack→Pearnly 翻 success 带 Express 单号。⚠️ 驱动真 Express GUI 需交互桌面;**PM 安排最省事方式(非让 Owner 学 Express)**,真机闭环 Owner 看结果。

## 3. Track B · DBF 直写(也要 · 第二录入法 · 带重护栏)
P3a 向导已支持 `method=dbf`。DBF 直写 = 绕过界面直接写账套 DBF(更快·不依赖 Express 开着)。
- **写哪些**(PM 已逆向·见 [[express-push-project]]):`APTRN`单头 + `ISVAT`进项税 + `GLJNL`+`GLJNLIT`分录(Dr 采购/Dr 进项税=Cr 应付·TRNTYP 0借1贷) + `APBAL`供应商余额(+存货则 `STCRD`);单号推进 `ISRUN`;**重建 `.CDX` 索引**。
- **强制护栏**:写前**自动备份该账套目录** → 单事务 → 写后**校验借贷平衡 + 读回** → 失败**整体回滚**;**账套路径白名单只 DATAT**(`\70EXP\test`);幂等(查 ref_no 防重)。
- **位置**:companion 新模块(如 `src/companion/dbf_writer.py` + 一个 `strategy`/method 选择,与 RPA 并列)。
- **验证**:对 **DATAT 测试套**录一张 RR,Express 打开能看到该单、分录正确、报表(ภ.พ.30/总账)勾稽对;白名单拒非 DATAT;备份+回滚演练。**绝不碰真账套。**

## 4. 边界 / 纪律
- companion 是**独立 repo**(`D:\pearnly-companion`),不进 pearnly-app。接的是 pearnly-app 已上线的 P1 Agent API。
- 每文件<500、≥1 测试、去 AI 味;改动先在分支(`feature/express-companion` 范式);不动主 repo。
- 真机/GUI 步骤交 Owner 机器跑、PM 判;能 headless 的(接线/payload/单测/dry-run)build 窗口跑齐交结果。
- ⚠️ companion 的"45 测试过/mock 验过"是它 2026-05 自述且**从没碰真 Express** → 复活=**先验证再依赖**,别拿来即信。

## 5. 顺序
Track A 先打通(主路径·最快到"真能用")→ Track B DBF 紧接(可另开 worktree 并行)。两条都进 P4 全链路闭环。
