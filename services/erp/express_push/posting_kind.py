"""本批过账去向(服务 / 库存)的唯一解析口径。

解析优先级:显式传参 > 票上的声明 > None。None = 没人声明过,不是「选了服务」——下游销项/
进项两个 mapper 据此走既有画像路径,未声明的票行为与本模块引入前逐字一致。

**声明跟着票走,不跟着推送走。** 推送有四条腿(手动推 / 识别后自动推 / 失败重试 / 批量
分拣),此前只有手动推带得上 posting_kind,同一批票记法因此不一致。改成上传时写进
ocr_history.posting_kind 后,另外三条腿手里都有 history,零改动即读得到。

**故意没有账套级默认这一层。** 两个 mapper 都把「有 posting_kind」当作用户对本批的显式
决定,据此绕过「永续客户 + 库存路未开 → 交会计」的 escalate;一个常驻的账套级默认不是
本批决定,配上等于把那道安全网对该端点长期关闭。邮件收料 / LINE 这类没有向导会话的入口
因此解析出 None,维持既有 escalate 不变 —— C6 打通采购入库后,声明过的票两侧都真动库存,没声明的仍交会计。
"""

from typing import Any, Dict, Optional

POSTING_KIND_SERVICE = "service"
POSTING_KIND_STOCK = "stock"
VALID_POSTING_KINDS = (POSTING_KIND_SERVICE, POSTING_KIND_STOCK)


def normalize(value: Any) -> Optional[str]:
    """认不出的值一律 None —— 不猜。

    脏值(前端传了空串 / 旧客户端拼错 / 手工改库)当「没声明」处理,回落到下一优先级,绝不
    静默当成 stock:错记成库存会真扣客户库存并结转 COGS,不可逆。
    """
    if not isinstance(value, str):
        return None
    v = value.strip().lower()
    return v if v in VALID_POSTING_KINDS else None


def resolve_posting_kind(
    explicit: Any,
    history: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """解析这张票该按什么去向过账。

    explicit:调用方显式指定(手动推 /api/erp/push 的每批开关)。
    history:票记录 · 读 posting_kind 列(上传时写入的本批声明)。
    """
    return normalize(explicit) or normalize((history or {}).get("posting_kind"))
