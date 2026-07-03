# 语音转写(泰语 STT)· 设计 + 施工(方案:复用网关 Gemini·零新供应商)

> 2026-07-03 · P2 backlog 第三件。现状:LINE 语音消息(`message.type=audio`)落
> `unsupported` 兜底直接回"不支持"(`line_webhook_routes.py` 其他类型分支),泰国用户语音占比高。

## 选型(不阻塞的成本决策)

**复用 `ai_gateway.multimodal_to_json`**:provider 的 Part 构造对音频与图片同构
(`vertex.py:267 Part.from_bytes(mime)`),Gemini 2.5 flash 原生收 `audio/aac`——
**零新供应商、零新密钥、零网关改动**,账单进现有 A 账号(Vertex),`task=line_voice_stt`
独立记账口径(ai_usage 带 tenant/user 可归属)。成本:音频 ≈32 token/秒,60 秒语音
≈2K input token,单条 << ฿0.1。**v1 不向用户收费**(同大脑调用先例;量大再议)。
落选:GCP Speech-to-Text/Whisper = 新 API 面/新供应商,收益无差。

## 流程(v1)

```
audio 事件 → 闸 agent_voice_stt(默认关·关=unsupported 现状逐字节不变)
  → 绑定校验(未绑定=现状) → 时长闸(>120s 诚实拒·防成本/超时)
  → line_client.download_message_content(与图片同 API)
  → multimodal_to_json(逐字转写 prompt·JSON {"text"}·audio/aac)
  → 空/听不清 → 诚实回"听不清请再说"(四语 inline 同 _PLAN_ACK 先例)
  → push 回显「🎤 转写原文」(钱路诚实:用户先看到机器听到了什么)
  → 转写文本喂现有 _handle_line_text(与打字完全同路:agent 循环/记账/改错/查询全套)
```

- **不另造大脑路**:转写=打字。金额接地/confirm-first/撤销改错等既有钱闸全部天然生效;
  听错金额与打错字同风险面,入账出卡可撤可改。
- **注入式挂钩**:webhook 只加一个 audio 分支调 `services/expense/line_voice.try_handle_audio`
  (text_handler 注入,不让 service 反向 import routes)。返回 False(闸关/未绑)= 落现状兜底。

## 风险闸

- 闸 `agent_voice_stt` 默认关 → 金丝雀(skin+163)→ 真机泰语人类门 → 放量。
- 转写失败/异常一律诚实回复,绝不静默吞;时长/转写长度双上限。
- 回显在前:机器听到什么用户先看到,记账卡在后,数字可核。

## 验收

- 单测:闸关现状不变/成功路(回显+同路转发)/网关失败诚实拒/超长拒。
- 真机(人类门):泰语说「กาแฟ 50」→ 回显+记账卡金额 50;泰语问「เดือนนี้กี่ใบ」→ 正常查询作答。
