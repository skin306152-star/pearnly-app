# -*- coding: utf-8 -*-
"""LINE 对话 Agent 模拟器(自测验收台)。

不经 LINE API,直接以某真实账号的身份驱动 services.agent.loop.handle_turn,把模型撰写的自然
语言回复打出来。用于跨全部现有能力做端到端验收:查询/汇总/余额/用量/通知/闲聊/产品问答/
超范围引导,以及记账/改错(应 defer=None → 交旧确定性路)。

用法(在 prod 上跑,env 有 qwen 端点 + DB):
    ./venv/bin/python scripts/agent_sim.py --user <user_id> [--ws <workspace_client_id>]
"""

from __future__ import annotations

import argparse

from core import db
from services.agent.contracts import AgentContext
from services.agent.loop import handle_turn

# (标签, 消息)。覆盖现有 5 只读工具 + 闲聊/产品问答/超范围 + 记账/改错(期望 defer)。
BATTERY = [
    ("闲聊·泰", "สวัสดีครับ"),
    ("产品问答·中", "你能帮我做什么"),
    ("历史列表·泰", "ดูประวัติ"),
    ("张数汇总·泰", "สแกนกี่ใบ"),
    ("本月花费·中", "本月花了多少"),
    ("余额·泰", "เครดิตเหลือเท่าไหร่"),
    ("用量·中", "这个月用了多少页"),
    ("通知·泰", "มีแจ้งเตือนอะไรบ้าง"),
    ("英文查询", "how many receipts did I scan"),
    ("含关键词过滤", "找一下 7-11 的单据"),
    ("超范围·改密码", "ช่วยเปลี่ยนรหัสผ่านให้หน่อย"),
    ("记账(期望 defer)", "กาแฟ 50 บาท"),
    ("改错(期望 defer)", "แก้รายการล่าสุดเป็น 80"),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    ap.add_argument("--ws", type=int, default=None)
    args = ap.parse_args()

    user = db.find_user_by_id(args.user)
    if not user:
        raise SystemExit(f"user not found: {args.user}")
    ctx = AgentContext(
        user=user,
        tenant_id=str(user.get("tenant_id")) if user.get("tenant_id") else None,
        workspace_client_id=args.ws,
        line_user_id=f"sim:{args.user}",
    )
    print(f"=== agent_sim · user={args.user} · tenant={ctx.tenant_id} ===\n")
    for label, msg in BATTERY:
        try:
            reply = handle_turn(msg, ctx, history=[])
        except Exception as e:  # 模拟器要看到崩没崩,不吞
            reply = f"[EXCEPTION] {type(e).__name__}: {e}"
        shown = reply if reply is not None else "[defer -> 旧确定性路(记账/改错/兜底)]"
        print(f"[{label}]\n  USER: {msg}\n  BOT : {shown}\n")


if __name__ == "__main__":
    main()
