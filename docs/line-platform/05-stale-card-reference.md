# 05 · LINE 旧卡片引用 · 状态闭环设计

> 起因:2026-06-19 Zihao 真机 + 追问 —— LINE 聊天里已发出的卡片气泡改不了(平台限制),是历史快照;
> 但底层单据(purchase_docs)会被改/撤/删。用户引用一张"旧卡片"操作时,系统必须对【那张单据的当前
> 真实状态】负责,绝不悄悄操作别的记录。
> 真 bug(screenshot):引用已删除的 99090 卡 + "金额改为300" → 改成了另一张活记录(150)。

## 0. 铁律

1. **唯一真相 = purchase_docs。** 网页与 LINE 是同一后端的两个前端;改/撤都走确定性引擎写真表,网页恒同步。
2. **卡片气泡 = 历史快照。** 永远不信气泡显示值,每次按 doc_id 重新查当前状态再回应。
3. **用户引用了哪张,只对那张当前状态负责。** 引用单据死了/变了 → 诚实说明 + 给正确出路,
   **绝不 fallback 到"最近活跃单"去操作**(这正是当前 bug)。
4. **永不死路 + 永不物理销毁。** 草稿删=软删(discarded),已入账撤=冲销(void),都可恢复。

## 1. 被引用单据的 4 种状态

按 doc_id 查 purchase_docs + 沿 corrected_from 链判定:

| 状态 | 定义 |
|---|---|
| **LIVE** | status=draft/posted,且无更新版本(链尾活单) |
| **SUPERSEDED** | 本单已 void,但 corrected_from 链上有更新的活单(被"改"过) → 解析到最新活单 |
| **VOIDED** | status=void,链上无活后代(被撤销且没续) |
| **DISCARDED** | 草稿被软删(原物理删改为软删后) |
| **EXPIRED_REF** | line_message_refs 查不到/过期(>90d)→ 引用本身失效 |

## 2. 状态 × 意图 → 正确应对(核心表)

| 引用单据状态 | 改字段(改金额/卖家/日期) | 撤销/删除 | 恢复 | 查看 |
|---|---|---|---|---|
| **LIVE** | 确认→应用(现有) | void/软删 | "这张没被撤销哦" | 显示当前 |
| **SUPERSEDED** | "这张已更新为 ฿X(记录#新)。改当前这张吗?"→对**最新活单**确认应用 | 撤最新活单 | "已是最新,无需恢复" | 显示**当前**版本+提示曾改 |
| **VOIDED** | **不改死单**:"这笔已撤销。要先恢复再改,还是重记一笔?" | "这笔已经撤销了哦"(幂等) | 恢复:克隆数据→新草稿→确认(已结期不可→诚实) | 显示(撤销态) |
| **DISCARDED** | "这张草稿已删除。恢复它,还是重记?" | "已经删掉了哦"(幂等) | 恢复:软删翻回 draft→确认 | 显示(已删态) |
| **EXPIRED_REF** | "记录引用过期了,输入'查明细'选第几笔" | 同左 | 同左 | 同左 |

**绝不出现**:引用一张 → 操作另一张(当前 bug)。引用死单做改/撤 → 必须落到上表对应格,不 fallback。

## 3. 解析算法(任何"引用卡片+动作"前先跑)

```
resolve_quoted(doc_id):
  ref = line_message_refs.lookup(quoted_message_id)
  if not ref: return EXPIRED_REF            # 不 fallback·诚实提示
  doc = load(ref.doc_id, ref.ws)
  if doc is None: return DISCARDED/也可能物理删 → DELETED 同 DISCARDED 文案
  live = follow_corrected_from_to_live_leaf(doc)   # 沿"被谁更正"链找最新活单
  if live and live.id != doc.id and live.status in (draft,posted): return SUPERSEDED(live)
  if doc.status in (draft,posted): return LIVE(doc)
  if doc.status == void: return VOIDED(doc)
  if doc.status == discarded: return DISCARDED(doc)
```

★关键修复点:`line_correct_flow.maybe_clarify_feedback` / `resolve_target` 里
"引用单据 not live → 回落 _active_doc" 的分支,改为按上表分状态诚实处理,**删掉静默回落别的活单**。

## 4. "恢复"意图(新增)

- 触发词:恢复 / 还原 / กู้คืน / restore / undo the cancel。
- VOIDED(已入账撤销):克隆原单数据→新草稿(corrected_from=原·审计链)→确认→可过账。已结期不可恢复→诚实拦。
- DISCARDED(草稿软删):status 翻回 draft→确认。
- LIVE:"这张没被撤销哦"。

依赖:草稿删除从**物理删改软删(status=discarded)**(单条 undo / 批量 undo / 改错删 三处的 delete_doc),
数据留库才可恢复 + 对齐铁律 4。复用 void 冲销 / clone_as_draft / corrected_from(见记忆 purchase-void-reversal-and-correct)。

## 5. 分片施工(账务敏感·分批·每片真机验)

> ★**Slice 编号以 `06 §5`(锚定框架)为唯一权威**;本节随之对齐(原"Slice 2/3"已拆并,避免冲突)。

- **Slice 1(✅ 已上线):诚实的旧卡片解析。** §3 解析 + §2 表"不改死单/不回落别的单/SUPERSEDED 落最新活单"。修掉 screenshot-29 事故。
- **Slice 2a(✅ 已上线):恢复已撤单。** 引用 VOIDED 卡说"恢复"→克隆重建活单(`restored_from`·原死单不动)。
- **Slice 2b(✅ 已上线):草稿软删 + 恢复已删草稿。** delete→discarded 三处统一;引用 DISCARDED 恢复→翻回草稿。
- **(✅ 已上线)裸取消/删除焦点修正:** 无引用的"取消/删除"锚到最近一张卡(草稿优先),不误撤更早的已入账。
- **Slice 3(强锚定·核心·见 06 §1/§5):** 引用即只围绕这张卡,绝不另记一笔/碰别的单(原本节"查看/提示文案打磨"并入此片)。
- **Slice 4(见 06 §2/§3):** 无引用置信度猜目标 + 多张近单列候选追问 + 追问答案继承 pending。

## 6. 设想的场景(≥20·维护见 04 覆盖表 H 段)

引用 LIVE 改/撤/查 ✅;引用 VOIDED 改→不改死单给出路;引用 DISCARDED 改→提示恢复或重记;
引用 SUPERSEDED 改→落最新活单;引用死单"恢复"→克隆/翻回;引用活单"恢复"→无需;链多次更正→恒落最新;
恢复进已结期→诚实拦;引用过期 ref→查明细;跨套账引用→按 ref.ws;引用死单撤销→幂等;
SUPERSEDED 撤销→撤当前;引用 + 模糊意图→问;改成非法值→拦(B8);两人同套账一改一引→落当前真态。
