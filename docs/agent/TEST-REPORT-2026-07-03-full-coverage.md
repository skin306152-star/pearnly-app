# Pearnly LINE 对话 Agent 全覆盖测试报告

日期: 2026-07-03  
基线: `master` @ `ec98d7d9`

## 1. 执行摘要

- 本地 Agent/LINE 相关单测: `1362 passed`
- Agent 覆盖率: `services/agent` 总体 `91.8%`
- JSONL 语料: `530` 条,其中文本对话 `514` 条
- 混沌压测: `1000` 轮,`seed=7`,四不变量 `0` 违例
- 能力登记审计: `92` 功能区 / `516` 入口,全部分类且 A 档声明完整
- prod 只读模拟器:测试账号 `skin306152@gmail.com` 对应 user id 跑默认 17 条,无 crash,无写入

## 2. 覆盖率

最终命令:

```bash
PYTHONUTF8=1 python -m coverage run -m pytest tests/unit -q -k agent
PYTHONUTF8=1 python -m coverage report -m services/agent/*.py
```

结果: `340 passed`, `services/agent` 总覆盖 `91.8%`。

低于 90% 的文件:

- `services/agent/dms_push.py`: `84.9%`
- `services/agent/executor.py`: `85.3%`
- `services/agent/push_confirm.py`: `89.2%`
- `services/agent/slots.py`: `84.9%`
- `services/agent/agent_i18n.py`: `88.9%`

这些主要是外部失败分支、异常兜底、少量 schema/slot 边界。当前没有为了刷覆盖写低价值断言,后续建议围绕真实事故样本补。

## 3. 路由指标

新增 `scripts/agent_corpus_metrics.py`,读取 `tests/agent_corpus/*.jsonl`:

- 总语料: `530`
- suite 分布: `loop=498`, `entry=16`, `image=16`
- 语言分布: `th=181`, `zh=127`, `en=108`, `ja=98`
- 主要类目: `matrix-query=288`, `matrix-record=24`, `matrix-edit=24`, `matrix-guard=24`, `matrix-slot-guard=24`

离线 scripted 基线:

- route accuracy: `100.00%`
- false defer rate: `0.00%`
- wrong tool rate: `0.00%`
- wrong record rate: `0.00%`

说明:这是“管道/护栏/接地闸”离线指标,不是线上真模型准确率。线上真模型仍需用 `scripts/agent_sim.py` 或真 LINE 人工评分。

## 4. 发现的问题

### P2 · 混沌压测不兼容图片语料

- 文件: `scripts/agent_stress.py`
- 复现:加入 `suite="image"` 语料后执行 `python scripts/agent_stress.py --rounds 1000 --seed 7`
- 实测:脚本假设每行都有 `text`,遇图片语料直接 `KeyError: 'text'`
- 修复:压测消息池改为读取目录下所有 JSONL,但只采样有 `text` 的行
- 回归:扩容后 `1000` 轮 `0` 违例

### P2 · entry harness 子闸 fake 不完整

- 文件: `tests/unit/_agent_entry_harness.py`
- 复现:压测时 confirm/chips/recon 子闸会查询真实 feature flag 配置,本地无 `DATABASE_URL` 时输出大量 fail-closed 日志
- 期望:离线 harness 应完整 fake Agent 闸,不碰真实配置库
- 修复:补齐 `agent_confirm_enabled_for` / `agent_dms_enabled_for` / `agent_recon_intake_enabled_for` / `agent_native_fc_enabled_for` / `agent_quick_chips_enabled_for`

### P3 · 真机 LINE/视觉截图未执行

- 范围:quick-reply chips、确认卡、真手机 LINE 通道
- 原因:本轮未发送真实 LINE 消息,未做任何写操作;只跑了 prod 只读模拟器
- 风险:离线与 prod dry-run 不能替代真 LINE UI 截图
- 建议:下一轮用测试 LINE 号补 7 条真机评分表,写操作仅限 test01/TEST2019

## 4.1 P3 status update: real LINE visual acceptance

This update supersedes the P3 "not executed" note above.

- Test LINE account: `18685123459@163.com`
- Test user id: `0ac26816-d529-40b2-a5f2-eee9d5d3331f`
- Tenant: `ed9a0d5a-473d-4565-9c96-a77f3692dba0`
- Workspace client id: `69`
- LINE user id: `U26139c19f754b12408413d074acb47fe`

Real LINE messages sent on 2026-07-03:

- Quick chips: `ok_quick=True`. Sent a real LINE push message with `quickReply` payload from `services.agent.quick_chips.quick_reply(...)`. The message rendered in the real LINE desktop chat. LINE Desktop does not display mobile quick-reply chips, so this proves send/payload, not phone visual rendering.
- Confirm card: `ok_card=True`. Sent a real LINE confirm card for history `e7457c0a-aa8f-405d-85ac-a8ab0f0da54a` (`PS2-0702`, amount `456.00`) to endpoint `dc184c06-c749-4190-afe0-6bdc3ea78353` (`MR.ERP DMS`). The card rendered in the real LINE desktop chat.
- Manual click: clicked the LINE card confirm button (`ยืนยันส่ง`) in the real LINE client. The bot returned the ACK and then the execution result message.
- Backend proof: nonce `mgO1e2TeAPeNbxrNUrmfmrLs` was consumed at `2026-07-03 08:20:43+00`; `erp_push_logs` row `1edefbc4-6042-4c82-9ff0-1ad26ac14e0d` was created with `trigger='line_agent'`, `status='failed'`, `http_status=0`, `error_msg='ERR_DMS_NOT_INVOICE_ENDPOINT'`. This is an expected adapter-level failure for the selected DMS endpoint, and proves the postback/nonce/execution path reached the backend.

Phone visual check:

- Windows Phone Link was connected to physical device `皮皮` (battery `68%` observed).
- Phone Link exposed only `SMS`, `Calls`, and notification-permission screens. It did not expose `Apps`, `Photos`, `Phone screen`, or any screen-mirroring entry in the accessibility tree or visible UI.
- User-supplied physical phone screenshot `照片 1.jpg` confirms the real mobile LINE chat rendered the confirm card, the manual confirm click result ACK, and the final ERP failure reply.
- The same screenshot shows the quick-chips test message on mobile, but not the quickReply chip buttons themselves. Because later confirm-card/result messages arrived after that message, LINE can hide older quickReply buttons. Result: quick chips send/payload is proven, but true mobile chip-button visual acceptance still needs a fresh screenshot immediately after sending the quick chips message and before any later bot message.

## 5. prod 只读结果

命令在 prod `/opt/mrpilot` 执行,未传 `--write`:

```bash
./venv/bin/python scripts/agent_sim.py --user 468b50c1-5593-4fd6-990d-515ce8085563
```

结果摘要:

- 闲聊/情绪/问候:正常 `reply`
- 历史/汇总/余额/通知/搜索/套账列表:正常 `reply`
- 记账 `กาแฟ 50 บาท`: `defer_record`
- 改错 `แก้รายการล่าสุดเป็น 80`: `defer_edit`
- 未发生 crash,未落库

## 6. 新增测试资产

- `tests/agent_corpus/generated_matrix.jsonl`:新增 `384` 条矩阵语料
- `tests/unit/test_agent_corpus.py`:离线 runner 改为读取 `tests/agent_corpus/*.jsonl`
- `scripts/agent_stress.py`:读取所有 JSONL 文本语料,跳过图片专用语料,并静音预期 crash 日志
- `tests/unit/_agent_entry_harness.py`:补齐 Agent 子闸 fake
- `scripts/agent_corpus_metrics.py`:新增语料覆盖与离线指标统计脚本

## 7. 验证命令

```bash
PYTHONUTF8=1 python -m pytest tests/unit -q -k "agent or line or webhook or native_fc or quick_chips or turn_log"
PYTHONUTF8=1 python -m pytest tests/unit/test_agent_corpus.py tests/unit/test_agent_image_intent.py tests/unit/test_agent_single_decider.py -q
PYTHONUTF8=1 python scripts/agent_capability_audit.py
python scripts/check_line_ratchet.py --quiet && python scripts/check_new_debt.py
PYTHONUTF8=1 python scripts/agent_stress.py --rounds 1000 --seed 7
PYTHONUTF8=1 python scripts/agent_corpus_metrics.py
```
