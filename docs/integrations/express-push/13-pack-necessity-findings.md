# T0 findings · DBF 直写单「不跑 PACK」是否报表可见

> 派自 `12-t0-pack-necessity-spike.md`。施工窗口在本机真 Express 跑(`D:\_express_audit` 工具链 + DATAT `\\accserver\ACCOUNT\70EXP\test`)。2026-06-22。
> **裁决:不 PACK → 报表看不到 → PACK 必需 → `express_pw` 不能删,T1 加密照做。**

---

## 1. 一句话结论

companion DBF writer 写完一张单(已设 `CMPLAPP='Y'` + per-write `_reindex()` 重建 CDX),**在完全不跑 PACK** 的情况下,会计打开 Express 看进项报表 241,**这张单看不到**;同一张单**跑一次 PACK 后立即可见**。→ 夜间 PACK 是可见性的必要步骤,登录 Express 所需的 `express_pw` 必须保留 → **走 T1(DPAPI 机器+用户双绑加密),不能删字段。**

## 2. 写的单 + 行数 diff(第 3 步)

`partB_write.py` 写两张非存货单进 DATAT(2558 账期,CMPLAPP=Y,per-write reindex,**未 PACK**):

| 单号 | 方向 | ref_no | 税前 / VAT / 含税 | CMPLAPP |
|---|---|---|---|---|
| `IV581220-001` | 销 IV 赊销 | PEARNLY-SVC1 | 10,000 / 700 / 10,700 | Y |
| `RR581220-004` | 进 RR 赊购 | PEARNLY-EXP1 | 5,000 / 350 / 5,350 | Y |

写后 8 表 delta(对基线):ARTRN +1 / APTRN +1 / ISVAT +2 / GLJNL +2 / GLJNLIT +6 / STCRD·APMAS·ARMAS +0。符合 writer 预期(非存货无 STCRD、老供应商客户无新主档)。

## 3. 不 PACK 查报表(第 5 步)· 进项 241

为避开报表数据量大 + 单日 `Message#9106` 怪癖,日期窗收窄到**多日区间 19–21/12/58**(短列表,排序后一眼可判)。报表 `2.รายงานเจ้าหนี้ → 4.ซื้อเงินเชื่อ → 1.เรียงตามเลขที่`(按单号排序)。

**结果:`RR581220-004` 不在报表里。** 序列 `RR581220-001 → -002 → -003 → RR581221-001` 直接跳过 -004;同日基线老单(早已 PACK 过)`RR581220-001/002/003` 全部正常显示。报表结尾合计 = **`รวม 10 ใบ`** / VAT 178,160.39 / 总计 2,723,308.59。

证据图:
- `shots/EVIDENCE_noPACK_241_GAP_no004.png` — 缺口处:-003 直接跳 581221-001。
- `shots/EVIDENCE_noPACK_241_total10.png` — 结尾 `รวม 10 ใบ`。
- `shots/EVIDENCE_noPACK_241_p0_19-21Dec.png` / `_RR581220-001.png` — 同日老单可见(对照,证报表机制本身正常)。

> 销项 141:早一轮脏会话出 `Message#9106 无数据`(月区间,与"新销项单不可见"一致),但本轮把干净的「PACK 前/后对比」资源集中在 241,141 未做同等隔离对比。结论靠 241 决定性证据成立,且 writer 销项/进项共用同一套口径(`write_sale`/`write_purchase` 均 CMPLAPP=Y + per-write reindex),结论可推广到销项。

> 放大镜(单据查询)兜底:报表中心读数已清晰(老单可见、新单按排序位缺失),未额外开放大镜。

## 4. PACK 对照组(第 6 步)· 证差的就是 PACK 那步

同一会话状态下跑 `p32_pack.py`(账套硬闸 PASS:路径 `\\accserver\ACCOUNT\70EXP\TEST` + 公司 บริษัท มานะชัยบริการ จำกัด·Message#5619 完成·~12s 全系统重整),**重出同窄区间 241**:

**结果:`RR581220-004` 转可见,精确填回排序缺口。** `RR581220-003 → RR581220-004 20/12/58 PEARNLY-EXP1 5,000.00 / 350.00 / 5,350.00 → RR581221-001`。报表结尾合计 = **`รวม 11 ใบ`**(+1 张)/ VAT 178,510.39(**+350**)/ 总计 2,728,658.59(**+5,350**)—— 三项增量精确等于该单。

证据图:
- `shots/EVIDENCE_PACK_241_RR581220-004_visible.png` — -004 填入缺口,ref PEARNLY-EXP1、5,350。
- `shots/EVIDENCE_PACK_241_total11.png` — 结尾 `รวม 11 ใบ`、增量 +350 / +5,350。

唯一变量 = PACK。写、CMPLAPP、per-write CDX 重建在 PACK 前已全部到位仍不可见 → **差的就是 PACK 的全系统重整这一步**,不是写错 / 日期错 / 账期错。

## 5. 差的那步具体是什么(给 PM 评估 writer 端能否补齐)

writer 已做:`APTRN.CMPLAPP='Y'` + 每写一张 `_reindex()` 重建涉及表 CDX。仍不可见 → **二者都不足以让 Express 报表引擎认到新行**。PACK(`ระบบจัดการแฟ้มข้อมูล` 全系统)据 `DBINF.DBF` 对所有表/所有 tag 做全量索引重建,这一步才让报表看见。

- **能否 writer 端免登录补齐?** 开放问题、有风险:per-table CDX 重建已做却不够,说明报表读的索引/口径不是 writer 当前重建的那一组;要离线复制 PACK 的「按 DBINF 全 tag 重建」需逆向 PACK 具体动了哪些索引,且离线用 dbf 库重建全索引对真账套有损坏风险。
- **PM 建议**:T1 按原计划做(`express_pw` DPAPI 加密 + 夜间无人值守 PACK 是已证主路)。"writer 端补齐免登录"作为将来优化候选单列,不阻塞 T1。

## 6. 还原核对(第 7 步)

- `Stop-Process ExpressI` → `robocopy <写前备份> \\accserver\ACCOUNT\70EXP\test /MIR`(回滚 110 个被写/PACK 改动的文件)→ 删服务器侧 `test_pearnly_bak_20260622-094636` / `-094732`。
- **8 表行数全部 == 基线**(ARTRN 1739 / APTRN 3247 / ISVAT 4885 / STCRD 12408 / GLJNL 6086 / GLJNLIT 21688 / APMAS 481 / ARMAS 540 · `count8.py` 输出 `ALL_BASELINE`)。DATAT 零污染。

## 7. 裁决

**PACK 必需**(证据见上)→ 删字段方案否决。PM 据此摆出三条:A 加密存+无人值守 PACK / B 不存·会计自跑 PACK(半自动) / C 逆向 PACK 离线复刻(免密码·需再 spike·有伤账套风险)。

**Owner 2026-06-22 拍板:走 A(存,DPAPI 加密)**,理由含前瞻——这把凭证语义是**方法无关的「Express 登录」**,直录用它跑 PACK、未来模拟录入(RPA)用它当登录口,**一处输入、一处加密、双方法共用**。详见 `11-production-readiness-dispatch.md` T1(已按此重写,含 `secret_store.load_express_login()` 统一收口 + 单输入框扩展性)。C 作为将来"免密码"优化候选单列,不阻塞 T1。
