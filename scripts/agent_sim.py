# -*- coding: utf-8 -*-
"""LINE 对话 Agent 在线模拟器(prod 验收台 · 真模型真 DB 真账号)。

以某真实账号身份直驱 services.agent.loop.handle_turn(不经 LINE API),打印每轮的
TurnResult 终态与文本,供人眼评"模型判意图"那一半(管道半边由 tests/unit/test_agent_corpus
离线闸守)。语料与离线共用 tests/agent_corpus/corpus.jsonl(忽略 script,真模型决策;
含 online_only 条目)。

写路径默认干跑:--write 启用写工具,record_sink 只打印草稿绝不入账;真机入账验证是人类门。

用法(prod,env 有模型后端 + DB):
    ./venv/bin/python scripts/agent_sim.py --user <user_id> [--ws <id>] [--write]
        [--corpus tests/agent_corpus/corpus.jsonl] [--only <id前缀>]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from core import db
from services.agent.contracts import AgentContext
from services.agent.loop import handle_turn

# 兜底 battery(不给 --corpus 时用):覆盖 5 只读 + 闲聊/情绪/超范围 + 记账/改错。
BATTERY = [
    ("emo-th", "เมียไม่รักผมแล้ว"),
    ("play-th", "5555 วันนี้รถติดมาก"),
    ("greet-th", "สวัสดีครับ"),
    ("cap-zh", "你能帮我做什么"),
    ("hist-th", "ดูประวัติ"),
    ("sum-th", "สแกนกี่ใบ"),
    ("sum-zh", "本月花了多少"),
    ("bal-th", "เครดิตเหลือเท่าไหร่"),
    ("usage-zh", "这个月用了多少页"),
    ("noti-th", "มีแจ้งเตือนอะไรบ้าง"),
    ("search-th", "หาบิล 7-11"),
    ("ws-list-zh", "我有哪些账套"),
    ("oos-th", "ช่วยเปลี่ยนรหัสผ่านให้หน่อย"),
    ("rec-th", "กาแฟ 50 บาท"),
    ("rec-711", "711 น้ำ 20"),
    ("neg-th", "ไม่ต้องบันทึกกาแฟ 50 นะ"),
    ("edit-th", "แก้รายการล่าสุดเป็น 80"),
]


def _corpus_battery(path: str, only: str) -> list:
    items = []
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        c = json.loads(ln)
        if c.get("suite") != "loop":
            continue
        if only and not c["id"].startswith(only):
            continue
        items.append((c["id"], c["text"]))
    return items


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    ap.add_argument("--ws", type=int, default=None)
    ap.add_argument("--write", action="store_true", help="启用写工具(record_sink 干跑打印,不入账)")
    ap.add_argument("--corpus", default="")
    ap.add_argument("--only", default="", help="只跑 id 以此前缀开头的语料")
    args = ap.parse_args()

    user = db.find_user_by_id(args.user)
    if not user:
        raise SystemExit(f"user not found: {args.user}")
    tid = str(user.get("tenant_id")) if user.get("tenant_id") else None
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT line_user_id FROM line_bindings WHERE user_id = %s LIMIT 1", (args.user,)
        )
        row = cur.fetchone()
    line_uid = (row and row.get("line_user_id")) or f"sim:{args.user}"
    ctx = AgentContext(user=user, tenant_id=tid, workspace_client_id=args.ws, line_user_id=line_uid)

    battery = _corpus_battery(args.corpus, args.only) if args.corpus else BATTERY
    drafts: list = []

    def dry_sink(_ctx, tool, data, say=""):
        drafts.append((tool, data))
        draft = (data or {}).get("draft")
        detail = (
            f"amount={draft.amount} vendor={draft.vendor_name!r} note={draft.note!r}"
            if draft is not None
            else repr(data)
        )
        print(f"  SINK: [DRY·不落地] tool={tool} {detail} say={say!r}")
        return "card_sent"

    print(f"=== agent_sim · user={args.user} · tenant={ctx.tenant_id} · write={args.write} ===\n")
    for label, msg in battery:
        try:
            res = handle_turn(
                msg,
                ctx,
                history=[],
                allow_write=args.write,
                write_sink=dry_sink if args.write else None,
            )
            shown = f"<{res.kind}> {res.text}"
        except Exception as e:  # 模拟器要看到崩没崩,不吞
            shown = f"[EXCEPTION] {type(e).__name__}: {e}"
        print(f"[{label}]\n  USER: {msg}\n  BOT : {shown}\n")
    if args.write:
        print(f"--- 干跑写动作共 {len(drafts)} 笔(零落地) ---")


if __name__ == "__main__":
    main()
