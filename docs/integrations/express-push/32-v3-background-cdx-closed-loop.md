# V3 · 后台 CDX 闭环(去 PACK 化 · 默认无人值守)

> 状态:方案锁定(2026-06-25 · Owner 实测 Harbour DBFCDX 可后台重建 + 拍板去 PACK 化)。
> 前序:V1 直接科目行(已上线 1.1.12)· V2 非库存主档 item_mode(代码就位见 doc31)。
> 本文 = V3 施工纲。承重突破 = 后台重建 CDX 不再需要打开 Express 跑 PACK。

## 1. 目标

把 Express 推送从「写 DBF + 之后靠用户/旧 PACK 可见」升级为**完整后台闭环**:
小助手后台写 DBF → 后台重建 CDX → 索引回查 → 回查过才报成功 → 用户在 Express UI 按单号可查。
用户**不需要**打开 Express、不需要手动 PACK、不需要懂 DBF/CDX。

## 2. 实测已证 / 未证(诚实边界)

**已证**(Owner 复制账套 lab · `D:\pearnly-erp-lab\express-harbour-reindex-20260625-160144`):
- `dbf.Table().reindex()` **无效**,不能当真实 CDX 重建;VFPOLEDB 不可靠。
- **Harbour 3.0.0 DBFCDX 可用**:`USE ... VIA "DBFCDX"` 自动打开 Express 现有结构化 CDX,
  `OrdName/OrdKey` 枚举出 Express 同名同 key 标签(STCRD3=DOCNUM+SEQNUM、STMAS1=STKCOD),
  `REINDEX` 重建这些标签,`DbSeek` 回查命中。55 张带 CDX 表全部可后台开+重建,失败 0。
  工具:`D:\pearnly-tools\harbour-cdx-engine-...`(probe exe ~1.2MB 静态独立)。

**Step A 已证(2026-06-25 · 真 DATAT 共享端到端)**:
- ① ✅ 真 `Express.exe` UI 查到 Harbour 重建后的单(IV690625-002 截图:单头+3 行明细+税+总计全对,**未跑 PACK**)。
- ② ✅ 完整单据(ARTRN 单头 / STCRD 明细 / ISVAT / GLJNL+GLJNLIT / ARBAL / STMAS 主档 / ISACC / ISRUN 共 9 表)走新路,REINDEX 0 失败 + 三索引回查命中(ARTRN1=DOCNUM、STCRD3=DOCNUM+SEQNUM、STMAS1=STKCOD)。
- ④ ✅ GTNUL 版 exe 无窗口子进程干净拉起跑通(见下「GTWIN 死穴」)。
- ⑤ ✅ Harbour `USE EXCLUSIVE` 经 SMB1 共享路径可行(ARTRN 独占开 1743 条);**不需要 copy-local-copyback,直接在共享上 REINDEX**。

**仍未直接证(cutover 前补)**:
- ③ Harbour cp874 **纯泰文 key 索引**排序与 Express VFP 完全一致 —— 已知:STMAS 主档(STKCOD ascii key)查到、泰文 stkdes 字节完好;但若有以**泰文文本本身为 key** 的索引(如客户名),collation 排序尚未直对。采购侧(APTRN/APBAL/供应商主档)同构未单独跑。

> **★ GTWIN 死穴(根因 + 生产硬约束)**:原 generic_probe.exe 用 **GTWIN**(Windows console 终端驱动)编译,
> 在**无控制台的后台子进程**里启动即 **hang 死**(抓不到 console)。Owner lab 验证在真终端跑 → 有 console → 成功,
> 掩盖了此坑;Claude 工具 + 生产里 **companion 后台无窗口拉起 runner** 都踩中。
> **修复 = 用 GTNUL(无终端)重编**(bundle 自带 MinGW 工具链 `hb30\comp\mingw\bin\gcc.exe`,
> `hbmk2 xxx.prg -gtnul -static -comp=mingw`)+ 给 PROCEDURE Main 的可选参数加 `IF arg==NIL ; arg:="" ; ENDIF` 防御。
> **component B 的 `cdx_reindex_runner` 必须 GTNUL 编译,否则装到客户机后台拉起一样 hang。**

## 3. 架构(默认 vs 兼容)

**默认(无人值守闭环)**:写 DBF → Harbour 后台重建 touched tables CDX → 索引回查 → 成功/回滚。
不开 Express、不 PACK、不需登录密码。

**兼容模式(高级设置 · 仅 Harbour 失败时启用)**:旧版 GUI PACK runner / RPA fallback。
此时才需要 Express 登录密码。

## 4. 组件

- **`cdx_reindex_runner.exe`**(新 · Harbour DBFCDX · 泛化 generic_probe):
  入参 = 账套目录 + touched tables 列表(+ 回查 key)。逐表 `USE EXCLUSIVE VIA DBFCDX` →
  `REINDEX` → 按关键索引 `DbSeek` 回查 → 输出结构化结果(每表 ok/失败 + 回查命中)。
  随安装包内置(~1.2MB)。替换 companion 现有无效的 `dbf.Table().reindex()`。
  **必须 GTNUL 编译**(`hbmk2 -gtnul -static -comp=mingw`)+ 可选参数 NIL 防御 —— 见 §2「GTWIN 死穴」。
  Step A 的 `gp_nul.prg/exe`(scratchpad/hb_build)= 直接蓝本,泛化为「逐表+结构化输出+回查 key」即可。
- **Harbour 运行时**:GTNUL 静态链接进 exe,干净机免装(✅ Step A 已证后台无窗口可跑)。

## 5. 写入闭环契约(companion · 每单事务)

1. 拉取 Pearnly 推送任务。
2. 校验账套路径、公司名、科目映射、商品策略。
3. **备份** touched tables 的 DBF/CDX/FPT。
4. 写客户/供应商主档、商品主档(V2 非库存)、单头、明细、税表、总账、余额。
5. **Harbour 重建** touched tables 的 CDX(非 PACK)。
6. 用 Express 索引 key **回查**单据 + 明细(见 §7)。
7. **回查全过才 ack success**;任一步失败 → **恢复备份** + ack failed/needs_review。
8. Express 正占用账套(独占失败)→ `waiting_lock`,稍后自动重试(不报失败)。

## 6. 状态模型(后端 erp_push_logs · 去 success/failed 二元)

状态:`queued → leased → writing → indexing → verifying → success` /
`waiting_lock`(等账套释放)/ `failed` / `rolled_back`(已恢复备份)/
`needs_mapping`(缺科目映射)/ `needs_review`(对账失败/疑似重复·见 doc31 3b)。

erp_push_logs 富元数据:小助手版本 · 账套路径 · 单据类型(purchase/sales)· 单号 ·
写入了哪些表 · 是否建客户/供应商 · 是否建商品 · CDX 重建结果 · 索引回查结果 ·
失败原因 · 是否已恢复备份。

**铁律:写了一半/索引失败/未回查过,绝不显示成功。**

## 7. 回查矩阵(verifying 步 · 索引 key 必须命中)

**采购单**:APTRN 按单号/供应商 · STCRD 按 DOCNUM+SEQNUM · ISVAT 按单号 ·
GLJNL/GLJNLIT 按 VOUCHER · 若建商品 STMAS 按 STKCOD。
**销项发票**:ARTRN 按单号/客户 · STCRD 按 DOCNUM+SEQNUM · ISVAT · GLJNL/GLJNLIT ·
若建商品 STMAS 按 STKCOD。

## 8. 托盘状态(companion)

灯:绿=空闲已连 / 黄=处理中 / 橙黄=等 Express 释放 / 红=失败需处理 / 灰=离线。
悬停文案(节选):空闲「等待新的发票/采购单」· 正在录入「采购单 HPxxxx / 发票 IVxxxx」·
正在整理索引「刚录入的数据正在变为可查询」· 等待锁「检测到账套正在被使用,稍后自动整理」·
失败「N 张单据未录入,请打开日志」。
通知:每批完成弹一次;失败立即弹(含"已恢复账套备份");等待锁超 1–2 分钟才提示。

## 9. 首次设置 UI(三段 · 去密码/PACK)

① 连接 Pearnly(配对码)② 选择 Express 账套(自动识别下拉)③ 确认科目映射(销项收入/应收/
销项税 · 进项采购/应付/进项税)。底部:开机自启 + 「Express 可见性:后台整理已开启」(只读状态)。

**高级设置(折叠)**:ERP 写入人(默认 BIT9·= DBF USERID/CREBY 审计字段·原"登录账号")·
兼容模式开关(旧版 PACK 整理)· Express 登录密码(仅兼容模式需要)· 关闭后台整理(不建议)。

「录完自动整理进 Express」文案改 →「后台整理索引,让 Express 立即可查」,默认开、标推荐,
主界面只显状态,关闭挪进高级。

## 10. 施工分期

- **A**(本期·先验):复制/测试账套完整单 → Harbour 重建 → Express UI 查到 + 泰文 key seek + 干净机跑 exe。
- **B**:`cdx_reindex_runner`(泛化 generic_probe · 重建 + 回查 + 结构化结果);companion 写盘后调它替换 `_reindex`,回查过才 ack、失败恢复备份。
- **C**:后端状态模型 11 态 + erp_push_logs 富元数据;ack/lease 扩展。
- **D**:companion 首次设置 UI 三段 + 密码进高级 + ERP 写入人 + 自动整理文案。
- **E**:托盘状态细化 + 通知策略。
- **F**:前端真实状态展示(集成页/异常页 · 含 items_mismatch 人话)。
- **G**:cutover — 默认走新路,旧 PACK/RPA 降兼容模式;companion 发版(验过才发)。

## 11. 风险

- 泰文 key 索引 collation(Harbour cp874 vs Express VFP)→ A 步专验一个泰文 key seek。
- 独占锁仍在(Express 正开着该套表 → Harbour EXCLUSIVE 失败)→ `waiting_lock` + 重试。
- Harbour 经 SMB 共享路径独占开(lab 是本地盘)→ A 步验。
- 打包:cdx_reindex_runner 干净机免装 Harbour → A 步验静态链接。
