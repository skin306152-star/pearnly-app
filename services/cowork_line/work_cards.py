"""Native LINE cards: buttons, keyboard editing and date/time picker."""

from urllib.parse import parse_qs, urlencode

# Each row follows the existing Cowork LINE language contract.
COPY = {
    "language": ("编辑语言", "Editor language", "ภาษาแก้ไข", "編集言語"),
    "home": ("工作协调", "Work coordination", "ประสานงาน", "仕事の調整"),
    "new": ("安排工作", "Assign work", "มอบหมายงาน", "仕事を依頼"),
    "attention": ("需要我处理", "Needs my decision", "รอฉันดำเนินการ", "対応が必要"),
    "all": ("查看全部工作", "All work", "งานทั้งหมด", "すべての仕事"),
    "boards": ("选择看板", "Choose board", "เลือกบอร์ด", "ボードを選択"),
    "create_board": ("新建工作看板", "Create work board", "สร้างบอร์ดงาน", "仕事ボードを作成"),
    "board_name": ("请输入看板名称", "Enter board name", "กรอกชื่อบอร์ด", "ボード名を入力"),
    "title": ("工作内容", "Work title", "หัวข้องาน", "仕事の内容"),
    "description": ("完成要求", "Requirements", "สิ่งที่ต้องส่งมอบ", "完了条件"),
    "assignee": ("负责人", "Assignee", "ผู้รับผิดชอบ", "担当者"),
    "due": ("截止时间", "Due", "กำหนดส่ง", "期限"),
    "confirm": ("确认保存", "Confirm save", "ยืนยันบันทึก", "保存を確定"),
    "dispatch": ("确认派发", "Confirm assignment", "ยืนยันมอบหมาย", "依頼を確定"),
    "cancel": ("取消本次操作", "Cancel this edit", "ยกเลิกการแก้ไข", "今回の操作を取消"),
    "back": ("返回工作台", "Back to work", "กลับหน้าหลักงาน", "仕事のホームへ"),
    "resume": ("继续未完成草稿", "Resume draft", "แก้ไขฉบับร่างต่อ", "下書きを再開"),
    "edit": ("修改安排", "Edit assignment", "แก้ไขงาน", "依頼を変更"),
    "comment": (
        "回复／询问进展",
        "Reply / ask progress",
        "ตอบ / ถามความคืบหน้า",
        "返信・進捗を確認",
    ),
    "history": ("查看记录", "View history", "ดูประวัติ", "履歴を見る"),
    "attachment": ("添加附件", "Add attachment", "เพิ่มไฟล์แนบ", "添付を追加"),
    "files": ("查看附件", "View attachments", "ดูไฟล์แนบ", "添付を見る"),
    "upload": (
        "请发送图片或文件（最多 10 MB），附件将加入当前任务。",
        "Send an image or file (max 10 MB) for this task.",
        "ส่งรูปหรือไฟล์ (ไม่เกิน 10 MB) สำหรับงานนี้",
        "この仕事の画像・ファイル（最大10 MB）を送信してください。",
    ),
    "input": ("请输入新内容：", "Enter the new value:", "กรอกข้อมูลใหม่:", "新しい内容を入力："),
    "empty": ("暂无记录", "No records", "ยังไม่มีรายการ", "記録なし"),
    "unset": ("未设置", "Not set", "ยังไม่ระบุ", "未設定"),
    "saved": ("已保存到工作协作。", "Saved to Work.", "บันทึกในงานแล้ว", "仕事に保存しました。"),
    "failed": (
        "未能确认操作结果，请重新打开任务核对。不会自动重复写入。",
        "Result not confirmed. Reopen the task to check; no automatic repeat.",
        "ยังยืนยันผลไม่ได้ เปิดงานเพื่อตรวจสอบ ระบบจะไม่เขียนซ้ำอัตโนมัติ",
        "結果を確認できません。仕事を開き直してください。自動再実行はしません。",
    ),
    "forbidden": (
        "此入口需要有效的老板账号和看板管理权限。",
        "An active owner account and board admin access are required.",
        "ต้องใช้บัญชีเจ้าของที่ใช้งานได้และสิทธิ์ผู้ดูแลบอร์ด",
        "有効なオーナーアカウントとボード管理権限が必要です。",
    ),
    "expired": (
        "这个按钮已过期，请使用最新卡片。",
        "This button expired. Use the latest card.",
        "ปุ่มนี้หมดอายุ โปรดใช้การ์ดล่าสุด",
        "このボタンは期限切れです。最新のカードを使用してください。",
    ),
    "invalid": (
        "内容无效或过长，请重新输入。",
        "Invalid or too long. Please try again.",
        "ข้อมูลไม่ถูกต้องหรือยาวเกินไป โปรดกรอกใหม่",
        "内容が無効または長すぎます。再入力してください。",
    ),
    "required": (
        "请填写工作内容并选择负责人。",
        "Enter a title and select an assignee.",
        "กรอกหัวข้องานและเลือกผู้รับผิดชอบ",
        "内容と担当者を指定してください。",
    ),
    "next": ("下一页", "Next", "ถัดไป", "次へ"),
    "previous": ("上一页", "Previous", "ก่อนหน้า", "前へ"),
    "pending": ("待处理", "To do", "รอดำเนินการ", "未着手"),
    "doing": ("进行中", "In progress", "กำลังดำเนินการ", "進行中"),
    "blocked": ("遇到问题", "Blocked", "ติดปัญหา", "問題あり"),
    "review": ("待验收", "Awaiting review", "รอตรวจรับ", "確認待ち"),
    "done": ("已完成", "Done", "เสร็จแล้ว", "完了"),
    "cancelled": ("已取消", "Cancelled", "ยกเลิกแล้ว", "取消済み"),
    "overdue": ("已逾期", "Overdue", "เกินกำหนด", "期限超過"),
    "accept": ("确认完成", "Accept completion", "ยืนยันเสร็จงาน", "完了を承認"),
    "return": ("退回补充", "Return for changes", "ส่งกลับให้แก้ไข", "修正を依頼"),
    "reason": ("原因／意见", "Reason / feedback", "เหตุผล / ความเห็น", "理由・意見"),
    "stop": ("取消任务", "Cancel task", "ยกเลิกงาน", "仕事を取消"),
    "status": ("调整状态", "Change status", "เปลี่ยนสถานะ", "状態を変更"),
    "search": ("搜索工作", "Search work", "ค้นหางาน", "仕事を検索"),
    "people": ("按负责人查看", "Filter by assignee", "ดูตามผู้รับผิดชอบ", "担当者で絞込"),
    "team": ("加入团队成员", "Add team member", "เพิ่มสมาชิกทีม", "チームメンバーを追加"),
    "add_member": (
        "确认加入看板",
        "Confirm board access",
        "ยืนยันเพิ่มเข้าบอร์ด",
        "ボードへの追加を確定",
    ),
    "setup": (
        "设置状态对应列表",
        "Map status to lists",
        "จับคู่สถานะกับรายการ",
        "状態とリストを対応",
    ),
    "setup_hint": (
        "请选择对应列表；不会移动现有任务。",
        "Choose the matching list; existing tasks stay in place.",
        "เลือกรายการที่ตรงกัน งานเดิมจะไม่ถูกย้าย",
        "対応するリストを選択。既存の仕事は移動しません。",
    ),
    "new_board_hint": (
        "将创建私人看板及六个工作状态列表。",
        "Create a private board with six work status lists.",
        "สร้างบอร์ดส่วนตัวพร้อมรายการสถานะงาน 6 รายการ",
        "非公開ボードと6つの状態リストを作成します。",
    ),
    "notification_failed": (
        "任务已保存，但 LINE 通知未送达或负责人未绑定。",
        "Task saved; LINE notice failed or assignee is not connected.",
        "บันทึกงานแล้ว แต่ส่ง LINE ไม่สำเร็จหรือผู้รับผิดชอบยังไม่เชื่อมต่อ",
        "保存済みですが、LINE通知未達または担当者が未連携です。",
    ),
    "notification": (
        "工作安排有更新",
        "Work assignment updated",
        "มีการอัปเดตงาน",
        "仕事の依頼が更新されました",
    ),
    "limit": (
        "记录过多，请选择较小的看板。",
        "Too many records. Select a smaller board.",
        "รายการมากเกินไป โปรดเลือกบอร์ดที่เล็กลง",
        "記録が多すぎます。小さいボードを選択してください。",
    ),
}

STATES = ("pending", "doing", "blocked", "review", "done", "cancelled")


def t(lang, key):
    return COPY[key][{"zh": 0, "en": 1, "th": 2, "ja": 3}.get(lang, 2)]


def button(label, command, nonce="", **params):
    return {
        "type": "button",
        "height": "sm",
        "action": {
            "type": "postback",
            "label": label[:40],
            "displayText": label[:300],
            "data": urlencode({"a": "work", "c": command, "n": nonce, **params}),
        },
    }


def edit_button(lang, field, nonce, current=""):
    item = button(t(lang, field), "field", nonce, f=field)
    if field == "due":
        item["action"].pop("displayText", None)
        item["action"].update(type="datetimepicker", mode="datetime")
    else:
        item["action"].update(inputOption="openKeyboard", fillInText=str(current)[:300])
    return item


def card(lang, title, lines, buttons):
    primary = []
    quick = []
    labels = {
        "save": "ยืนยัน",
        "apply": "ยืนยัน",
        "confirm_board": "ยืนยัน",
        "add_member": "ยืนยัน",
        "accept": "ยืนยัน",
        "edit": "แก้ไข",
        "editor": "แก้ไข",
        "discard": "ยกเลิก",
        "cancel": "ยกเลิก",
        "stop": "ยกเลิก",
        "home": "กลับ",
        "detail": "กลับ",
    }
    for item in buttons:
        action = dict(item["action"])
        command = parse_qs(action.get("data", "")).get("c", [""])[0]
        if command in labels and len(primary) < 4:
            action["label"] = labels[command]
            action["displayText"] = labels[command]
            primary.append({**item, "action": action})
        else:
            action["label"] = action["label"][:20]
            quick.append({"type": "action", "action": action})
    if len(quick) > 13:
        raise ValueError("LINE quick reply exceeds 13 actions")
    result = {
        "type": "flex",
        "altText": title[:400],
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": title[:1000] or t(lang, "home"),
                        "weight": "bold",
                        "wrap": True,
                    },
                    *[
                        {
                            "type": "text",
                            "text": str(line)[:2000] or "—",
                            "size": "sm",
                            "wrap": True,
                        }
                        for line in lines
                    ],
                ],
            },
            **(
                {"footer": {"type": "box", "layout": "horizontal", "contents": primary}}
                if primary
                else {}
            ),
        },
    }
    if quick:
        result["quickReply"] = {"items": quick}
    return result
