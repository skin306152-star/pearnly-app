# LINE-DMS:拍身份证 → 建 DMS 客户 · 设计(施工前方案)

> 2026-07-02 · loop 能力块。推送主路径,按铁律先报方案。
> 依赖已就绪:LI 意图框架(话先图后)+ M3 确认握手状态机(本块=泛用检查点表首个消费者)。

## 0 · 现状

- **网页流**(routes/dms_routes.py,已上线):`/api/dms/id-card/recognize`(专用身份证
  OCR·id_card_extract·按 1 页计费·余额闸齐)→ 前端面板人工核对/编辑 →
  `/api/dms/id-card/push`(建/改 DMS 客户 · push_idcard_fields_mrerp_dms · 写 erp_push_logs
  trigger=id_card)。**只写客户库,不建订车单**(现行范围)。
- **LINE 今天**:身份证图进费用 OCR 管线 → not_invoice →"不像票据请发费用文件"死胡同
  (与对账单同病,PR#38 只治了对账单)。
- 测试设施:测试号已有 MR.ERP DMS 端点(dc184c06 · 现 disabled,启用即可测);
  身份证语料 = Desktop/单据/身份证.jpg(PII:只上服务器 /tmp,用完删,永不进 git)。

## 1 · 用户场景(若X那么Y)

| X | Y |
|---|---|
| 说"บัตรประชาชนใบต่อไปเข้า DMS / 下一张身份证建 DMS 客户"再发身份证 | 专用身份证识别 → 复述(姓名+证号尾4)→ 回"确认" → 建成 DMS 客户 → ✅人话 |
| 直接发身份证(没说话) | not_invoice 分支认出身份证 → 靶向引导:"这像身份证——要建 DMS 客户就说一声再发" |
| 说了 DMS 但租户没连 DMS 端点 | 诚实引导:去网页「集成」连接 MR.ERP DMS |
| 识别不出证号/姓名(必填) | 不出确认——直接说哪个字段读不出,请拍清晰正面照重试 |
| 复述后 15 分钟没回 / 回别的话 | 检查点过期/让位,不执行(状态机 §2 语义) |
| 回"确认"两次(手滑) | 单发单用,第二次撞幂等诚实说已建过 |

## 2 · 架构(全部复用已有底座)

```
话先图后:plan_incoming_doc goals 收新值 "dms"(别名 dms_customer/id_card_to_dms…)
   ↓ pending {goals:["dms"]}
图到:line_image_ocr 下载后·费用 OCR 之前 → peek 意图=dms →【绕过费用管线】
   ↓ 专用身份证识别(抽 dms_routes._ocr_id_card 的 OCR+计费段到 service 层共用·按 1 页计)
   ↓ 必填校验(people_id+name·网页同口径)
存泛用检查点 line_pending_actions{tool:"dms_push", fields, endpoint_id, mode:"create"}
   ↓ 复述:"将建 DMS 客户:{name}·证号尾4 {tail}·回'确认'执行"
用户回"确认" → confirm_machine resume 闸(扩展:先查泛用检查点,再查 push nonce)
   ↓ 执行 push_idcard_fields_mrerp_dms(网页同一函数)→ insert_push_log(trigger=line_dms)
   ↓ ✅/❌ 人话(错误码走 push_log_friendly,ERR_DMS_* 目录已有四语)
```

- **绕过费用管线的理由**:意图明确=省一次费用 OCR 的钱 + 身份证抽取走专用模型路(准);
  绕过点在 quote 之前,计费只发生在身份证识别那一次(与网页同口径)。
- **line_pending_actions 表**(状态机设计 §3 预留,至此有了首个生产者):
  照 line_pending_intents 范式(tenant+line_user 单活动行 · TTL 15min · take=DELETE
  RETURNING 单发单用 · ensure 自愈)。resume 消费顺序:泛用检查点 > push nonce(检查点
  是"刚复述完等答复",语境最强)。
- **无意图身份证检测**(引导用):not_invoice 分支关键词(บัตรประจำตัวประชาชน /
  Thai National ID / เลขประจำตัวประชาชน)—— 与对账单引导同模式同挂点。

## 3 · 闸与回滚

- 新子闸 `agent_dms_push`,默认关 fail-closed;关 = 身份证图走现状(not_invoice 引导也关?
  否——引导无副作用挂 image_intent 闸下)。回滚=关闸;检查点表留着无害。
- 权限:复用 `_check_push_access` 同口径(套餐 can_push_erp)。

## 4 · 验证

- 单测:检查点表契约 · plan goals=dms 别名/推断 · 绕过点(意图 dms 时费用管线零调用)·
  必填缺失不出确认 · resume 消费顺序 · 幂等。
- 语料:corpus +4(泰/中 说意图、无端点、字段缺)。
- 模拟舱:全链(意图→身份证→复述→确认→DMS 客户)· 出站捕获。
- 在线 E2E:启用测试号 DMS 端点 → 真身份证语料(服务器侧)→ DMS 后台真出客户
  (浏览器取证)→ 清理测试客户。

## 5 · 不做(v1)

- 订车单(booking):网页现行范围就只到客户库,LINE 对齐,不越网页能力。
- 身份证图自动转 DMS(无意图):必须用户说过才动手——建客户是外部写,不静默。
- overwrite/update 模式:v1 只 create;重复证号 DMS 侧会拒,人话引导去网页处理。
