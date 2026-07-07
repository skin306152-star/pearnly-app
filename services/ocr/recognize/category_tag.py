"""识别科目标签:把 OCR 结果归到【本套账费用分类树】(泰语),而非模型自由文本(可能中文)。

归类顺序(纯 CPU·无 LLM·不加识别耗时):
  ① 卖方名 + 品名 → 关键词规则(category_ai.classify_rules)匹配你的科目树
  ② 不中则拿模型那个分类词跨语言映射(category_ai.match_user_category)
  ③ 都不中 → None(留空,让用户在抽屉里选;绝不落模型的原始中文)

仅产出【展示标签】。不影响推送——MR.ERP 推送不消费 category_tag(科目由科目映射/商品解析,
见 mrerp_xlsx_purchase),故匹配与否都不会卡推送。
"""

from typing import Any, Dict, List, Optional

from services.expense import category_ai


def item_descriptions(fields: Dict[str, Any]) -> str:
    """票面品名拼成一段文本(喂关键词规则的 descs)。无 items → 空串(仍可靠卖方名匹配)。"""
    items = fields.get("items") if isinstance(fields, dict) else None
    if not isinstance(items, list):
        return ""
    return " ".join(
        str(it.get("name") or it.get("description") or "") for it in items if isinstance(it, dict)
    )


def _name_in_tree(tree: List[Dict[str, Any]], cid: Any, sid: Any) -> Optional[str]:
    """(大类id, 子类id) → 树里的名字(子类优先,无子则大类名)。"""
    for parent in tree or []:
        if parent.get("id") == cid:
            for child in parent.get("children") or []:
                if child.get("id") == sid:
                    return child.get("name")
            return parent.get("name")
    return None


def resolve_tag(fields: Dict[str, Any], tree: List[Dict[str, Any]]) -> Optional[str]:
    """归到本套账分类 → 返回该分类名(泰语·子类优先);不中 → None(留空)。"""
    if not (isinstance(fields, dict) and tree):
        return None
    vendor = str(fields.get("seller_name") or "")
    descs = item_descriptions(fields)
    cid, sid, _layer = category_ai.classify_rules(vendor, descs, tree)
    if not cid:
        cid, sid = category_ai.match_user_category(str(fields.get("category") or ""), tree)
    if not cid:
        return None
    return _name_in_tree(tree, cid, sid)


def sanitize_learned(word: Optional[str], tree: List[Dict[str, Any]]) -> Optional[str]:
    """净化"同卖方学习"到的旧科目值:是本套账真实分类名(预置/自定义)→ 原样保留;否则(旧
    模型自由文本,如中文'化妆品')→ 跨语言映射到本套账分类,映射不上 → None(不回灌非本套账中文)。
    无树(无套账/载树失败)→ 原样保留(回落·不误伤)。调用方仅在返回真值时才覆盖,None 不清空。
    """
    if not word:
        return None
    if not tree:
        return word
    w = str(word).strip()
    for parent in tree:
        if parent.get("name") == w:
            return w
        for child in parent.get("children") or []:
            if child.get("name") == w:
                return w
    cid, sid = category_ai.match_user_category(w, tree)
    return _name_in_tree(tree, cid, sid) if cid else None
