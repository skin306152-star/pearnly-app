# -*- coding: utf-8 -*-
"""管家工具注册表 —— 闭集插头目录(照 services/agent/manifest.py 范式)。

闭集:大脑只能从 TOOLS 里选,表外的名字物理调不到(tools.run 按本表查执行器,查不到直接
拒;planner 解析时枚举外一律归 out_of_scope)。加一个能力 = 加一个 StewardTool + tools.py
里一个薄封装函数,提示词自动跟着变(catalog() 从本表现生成)。

参数槽复用 services.agent.contracts.SlotSpec —— 接地闸 services/agent/slots.py 逐字节复用
(source=user_text 的值必须出现在用户原话里,编造值进 rejected 绝不流到执行)。为什么不直接
用 manifest.ToolSpec:它的 bucket/confirm/writes/gate 是 LINE 写工具的语义(M1 全只读用不上),
desc_th 字段名钉死泰文而管家提示词走中文(同 front_desk.interpret 先例,同一个 /ai 面、同一
条 taxops.intent 车道)—— 硬塞会让字段名说谎。槽契约共用,工具契约各自诚实。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional

from services.agent.contracts import SlotSpec
from services.sales.dates import bangkok_today

# 风险等级(B3 授权闸的判据面):read 直接执行;write 落数据、danger 落数据且难撤销
# (推 ERP/删单据)。非 read 一律要求人批的授权令牌 —— 执行层物理拒,不是前端不显示。
RISK_READ = "read"
RISK_WRITE = "write"
RISK_DANGER = "danger"
RISK_LEVELS = (RISK_READ, RISK_WRITE, RISK_DANGER)

# 工具名(单一事实源:planner/tools/copy 一律 import 这些常量,不各打字符串)。
MATRIX_OVERVIEW = "matrix_overview"
CLIENT_STATUS = "client_status"
WORKORDER_LIST = "workorder_list"
PUSH_LOG_QUERY = "push_log_query"
HISTORY_QUERY = "history_query"
CLIENT_LOOKUP = "client_lookup"
DUE_SOON = "due_soon"
REVIEW_QUEUE = "review_queue"
TAX_NUMBERS = "tax_numbers"
BANK_RECON_STATUS = "bank_recon_status"
INVOICE_DETAIL = "invoice_detail"
TODAY_BRIEF = "today_brief"
CLOSE_READINESS = "close_readiness"
DELIVERABLES_LIST = "deliverables_list"
VAT_CALC = "vat_calc"
TAX_MATRIX = "tax_matrix"
PERIOD_INVOICES = "period_invoices"
ERP_PUSH = "erp_push"
FILE_CONVERT = "file_convert"
VAT_REPORT_CHECK = "vat_report_check"

# 吃这一轮附件的工具(万能口)。哪个文件配哪个工具由代码按 kind 过滤,模型只挑工具不挑文件
# ——模型选文件会挑错,且挑错无痕。判据单一事实源在这里,orchestrator/planner 一律读本表。
ATTACHMENT_TOOLS: frozenset = frozenset({FILE_CONVERT, VAT_REPORT_CHECK})

# 识别类工具比只读查询慢一个量级(整份 PDF 解析 + 可能过模型),按 5 分钟的通用任务超时会在
# 还在正常干活时被砍成 failed。照 ERP_PUSH_TIMEOUT_S 先例单独声明,入队时定格进任务行。
FILE_TOOL_TIMEOUT_S = 600

# 经桥写 Express 是分钟级(桥端备份账套 → 写 DBF → 重建 CDX,全程跨 SMB),按只读工具的
# 5 分钟任务超时会在桥还在正常干活时把任务砍成 failed。定格进任务行,见 store.create_task。
ERP_PUSH_TIMEOUT_S = 900


@dataclass(frozen=True)
class StewardTool:
    """一个管家能调的能力。风险等级是授权闸的唯一判据:readonly 从 risk 推导而非独立字段
    ——两个字段会漂(readonly=True 而 risk=write 的工具就是后门),单一事实源杜绝。"""

    name: str
    desc: str  # 中文:这个工具干嘛(进提示词,大脑据此挑)
    slots: tuple[SlotSpec, ...]
    handler: str  # services/steward/tools.py 里的函数名
    risk: str = RISK_READ
    timeout_s: Optional[int] = None  # 本工具的任务超时(缺省走 store.default_timeout_s)

    def __post_init__(self) -> None:
        if self.risk not in RISK_LEVELS:
            raise ValueError(f"steward tool {self.name}: unknown risk {self.risk!r}")

    @property
    def readonly(self) -> bool:
        return self.risk == RISK_READ


def requires_authorization(tool: StewardTool) -> bool:
    """写/危险工具必须持人批的授权令牌才准执行(闸在 tools.run,物理拒)。"""
    return tool.risk != RISK_READ


def _period_slot() -> SlotSpec:
    """期间线索槽(共 3 个工具用同一份定义,避免三处各写一遍描述后漂)。

    source=model_freeform:期间允许模型从「上个月」这类相对词换算,但换算结果不作数——
    真正的接地在 orchestrator:线索经 front_desk.interpret.parse_period_hint 解析成公历,
    再经 obligation_engine.be_period_from_ce 折成佛历账期,解不出就追问,绝不猜一个期。
    """
    return SlotSpec(
        "period",
        required=False,
        source="model_freeform",
        desc_th="ช่วงเวลาที่ผู้ใช้พูดถึง เช่น มิ.ย.69 / เดือนที่แล้ว / 2026-06",
        desc_zh="期间线索原文(如「上个月」「6月」「2569-06」)· 没提到给 null",
    )


def _keyword_slot(desc_th: str, desc_zh: str) -> SlotSpec:
    """票据关键词槽。source=user_text 同客户名槽:模型编一个单号会把人指到另一张票上。"""
    return SlotSpec("keyword", required=True, source="user_text", desc_th=desc_th, desc_zh=desc_zh)


def _client_name_slot(required: bool) -> SlotSpec:
    """客户名槽。source=user_text:名字必须出现在用户原话里(接地闸拦编造),
    随后还要在真实名录里命中才作数(tools 侧二次接地)—— 挂错账套是红线。"""
    return SlotSpec(
        "client_name",
        required=required,
        source="user_text",
        desc_th="ชื่อลูกค้าตามที่ผู้ใช้พิมพ์ (คัดจากข้อความผู้ใช้เท่านั้น)",
        desc_zh="客户名(必须原样出自用户原话·不许改写不许猜)",
    )


TOOLS: tuple[StewardTool, ...] = (
    StewardTool(
        name=TODAY_BRIEF,
        desc=(
            "今天先从哪下手:逾期几项 / 等你审几张 / 推 ERP 失败几条 / 缺料几家一次数完,"
            "再按紧急度给最急的几条 · 会计问「今天先干哪个」「有什么要紧的」时用 · "
            "不点名客户、不点名单张票;只要一期的家数统计用 matrix_overview"
        ),
        slots=(_period_slot(),),
        handler="today_brief",
    ),
    StewardTool(
        name=MATRIX_OVERVIEW,
        desc="查某一期的事务所矩阵总览:多少家客户、缺料/待审/进行中/未开单各多少家",
        slots=(_period_slot(),),
        handler="matrix_overview",
    ),
    StewardTool(
        name=CLIENT_STATUS,
        desc="查某一家客户某一期的进度:工单状态、当前步骤、还缺什么材料",
        slots=(_client_name_slot(required=True), _period_slot()),
        handler="client_status",
    ),
    StewardTool(
        name=WORKORDER_LIST,
        desc="列工单:某一期的工单有哪些,可按口径筛(缺料/进行中/待审/已冻结)",
        slots=(
            _period_slot(),
            # 口径词而非引擎态:用户说的「还没审完」在矩阵里是 stuck+review 两态合成的
            # 「待审」。让大脑挑口径词、由 engine.resolve_status_filter 展开成引擎态,
            # 答复才与同屏矩阵数得起来(引擎态原词执行器也认,归到所属口径)。
            SlotSpec(
                "status",
                required=False,
                source="model_freeform",
                desc_th="ขอบเขต: missing_materials/in_progress/pending_review/frozen",
                desc_zh=(
                    "筛选口径(missing_materials 缺料 / in_progress 进行中 / "
                    "pending_review 待审 / frozen 已冻结)· 执行器再验"
                ),
            ),
        ),
        handler="workorder_list",
    ),
    StewardTool(
        name=PUSH_LOG_QUERY,
        desc="查推 ERP 的成败:近几天推了多少、失败几条、失败原因是什么",
        slots=(
            SlotSpec(
                "days",
                required=False,
                source="model_freeform",
                desc_th="ย้อนหลังกี่วัน (ตัวเลข ค่าเริ่มต้น 7)",
                desc_zh="回看天数(数字·缺省 7)",
            ),
            SlotSpec(
                "status",
                required=False,
                source="model_freeform",
                desc_th="กรองสถานะ: success / failed",
                desc_zh="状态过滤(success/failed)· 只问失败时给 failed",
            ),
            _client_name_slot(required=False),
        ),
        handler="push_log_query",
    ),
    StewardTool(
        name=HISTORY_QUERY,
        desc="在识别记录里找某张票(按店名/单号/文件名关键词)",
        slots=(
            _keyword_slot(
                "คำค้น เช่น ชื่อร้านหรือเลขใบเสร็จ (คัดจากข้อความผู้ใช้เท่านั้น)",
                "关键词(店名/单号/文件名·必须出自用户原话)",
            ),
        ),
        handler="history_query",
    ),
    StewardTool(
        name=DUE_SOON,
        desc="查某一期还没交完的申报义务和截止日:哪几家、什么表、还剩几天、有没有逾期",
        slots=(_period_slot(),),
        handler="due_soon",
    ),
    StewardTool(
        name=REVIEW_QUEUE,
        desc="查等人审的工单队列:有什么等我审、哪些卡住待判、可按客户或严重度筛",
        slots=(
            _period_slot(),
            _client_name_slot(required=False),
            SlotSpec(
                "severity",
                required=False,
                source="model_freeform",
                desc_th="ระดับความรุนแรง: crit(ร้ายแรง) / warn(เตือน)",
                desc_zh="严重度(crit 严重 / warn 提醒)· 只问严重的才给 crit,否则 null",
            ),
        ),
        handler="review_queue",
    ),
    StewardTool(
        name=TAX_NUMBERS,
        desc="查某家某期算出来的税额:销项/进项/销项税/进项税/应交多少",
        slots=(_client_name_slot(required=True), _period_slot()),
        handler="tax_numbers",
    ),
    StewardTool(
        name=TAX_MATRIX,
        desc=(
            "一张表列全所每家客户本期的税额:销项/进项/销项税/进项税/应交,一家一行带合计 · "
            "会计问「所有客户/每家/全所这个月该交多少」「税额列个表」时用 · "
            "只问一家用 tax_numbers;只要家数统计不要钱用 matrix_overview"
        ),
        slots=(_period_slot(),),
        handler="tax_matrix",
    ),
    StewardTool(
        name=PERIOD_INVOICES,
        desc=(
            "列某家某期收到的进项票,逐张标推进 Express 了没,可只看还没推的 / 待判的 · "
            "会计问「还有几张票没推进去」「把这期的票列一下我核有没有漏」时用 · "
            "查单张票用 invoice_detail;只统计推过的成败用 push_log_query(没推的票不在它里面)"
        ),
        slots=(
            _client_name_slot(required=True),
            _period_slot(),
            SlotSpec(
                "filter",
                required=False,
                source="model_freeform",
                desc_th="ตัวกรอง: not_pushed(ยังไม่ได้ส่งเข้า Express) / pending_review(รอตัดสิน) / all",
                desc_zh=(
                    "筛选(not_pushed 还没推进去 / pending_review 待判 / all 全部)· "
                    "问「还有几张没推」给 not_pushed,问「还有什么要判」给 pending_review,"
                    "只说「把票列一下」给 null"
                ),
            ),
        ),
        handler="period_invoices",
    ),
    StewardTool(
        name=BANK_RECON_STATUS,
        desc="查某家某期的银行对账进度:对上几笔、缺票几笔、有票无流水几笔、差多少钱",
        slots=(_client_name_slot(required=True), _period_slot()),
        handler="bank_recon_status",
    ),
    StewardTool(
        name=INVOICE_DETAIL,
        desc="查某一张票的详情:识别成什么、过账去向、推进 ERP 了没、失败原因是什么",
        slots=(
            _keyword_slot(
                "ระบุใบที่จะดู เช่น เลขที่ใบกำกับหรือชื่อร้าน (คัดจากข้อความผู้ใช้เท่านั้น)",
                "要看的那张票(单号/店名/文件名·必须出自用户原话)· 系统据此定位唯一一张",
            ),
        ),
        handler="invoice_detail",
    ),
    StewardTool(
        name=CLOSE_READINESS,
        desc=(
            "这家这期能不能签批收官:税额算了没 / 银行对上没 / 待判清了没 / 交付包出了没 / "
            "签批态,五项逐项过一遍并直说没过的差什么 · 会计问「能签了吗」「还差什么才能收」时用 · "
            "只问跑到哪一步用 client_status,只要税额数字用 tax_numbers"
        ),
        slots=(_client_name_slot(required=True), _period_slot()),
        handler="close_readiness",
    ),
    StewardTool(
        name=DELIVERABLES_LIST,
        desc=(
            "某家某期的交付物/报表包清单:ภ.พ.30 草稿、进销底稿、月度报表等各出了没,"
            "出了的直接给下载链 · 会计问「报表好了没」「把文件/草稿发我」时用 · "
            "只问能不能签用 close_readiness"
        ),
        slots=(_client_name_slot(required=True), _period_slot()),
        handler="deliverables_list",
    ),
    StewardTool(
        name=CLIENT_LOOKUP,
        desc="按名字或税号模糊查客户名录(用户提的客户名不确定是哪一家时先用它对一下)",
        slots=(
            SlotSpec(
                "keyword",
                required=True,
                source="user_text",
                desc_th="ชื่อลูกค้าหรือเลขผู้เสียภาษี (คัดจากข้อความผู้ใช้เท่านั้น)",
                desc_zh="客户名或税号片段(必须出自用户原话)",
            ),
        ),
        handler="client_lookup",
    ),
    StewardTool(
        name=VAT_CALC,
        desc=(
            "现场算 VAT:会计自己报一个数,在含税/税前/税额之间互算(泰国 7%),她报了预扣税率就"
            "一并算预扣和实付 · 只在数字出自她嘴里时用;要查某家某期账上已经算好的税额用 tax_numbers"
        ),
        slots=(
            SlotSpec(
                "amount",
                required=True,
                source="user_text",
                desc_th="จำนวนเงินที่ผู้ใช้พูด (คัดจากข้อความผู้ใช้เท่านั้น ลอกมาทั้งจุดทั้งคอมม่า)",
                desc_zh="会计报的那个金额(原样抄她说的数字·带逗号小数点也照抄·不许换算不许四舍五入)",
            ),
            # 方向判错 = 答案照样是两位小数、看不出错的假数,所以宁可追问也不给缺省:
            # required=True 让判不出来的 null 走系统追问,不在提示词里塞一个「默认含税」。
            SlotSpec(
                "basis",
                required=True,
                source="model_freeform",
                desc_th="ตัวเลขนี้รวม VAT แล้วหรือยัง: inclusive(รวมแล้ว) / exclusive(ยังไม่รวม)",
                desc_zh=(
                    "这个数含不含税(inclusive 含税 / exclusive 未含税)· "
                    "「含税的/รวมแล้ว」给 inclusive,「税前/ยังไม่รวม」给 exclusive · 看不出来给 null 让系统问"
                ),
            ),
            # 该扣几个点是税务判断不是算账:会计没把率说出口就一律 null,工具不替她挑。
            SlotSpec(
                "wht_rate",
                required=False,
                source="user_text",
                desc_th="อัตราหัก ณ ที่จ่าย เฉพาะเมื่อผู้ใช้บอกเอง เช่น 3 (คัดจากข้อความผู้ใช้เท่านั้น)",
                desc_zh="预扣税率百分点(会计自己说了几个点才填,如 3)· 她没说一律 null,绝不替她挑",
            ),
        ),
        handler="vat_calc",
    ),
    StewardTool(
        name=ERP_PUSH,
        desc=(
            "把一张已识别的票推进 Express 账套(会真写客户的账 · 必须人批准后才执行)· "
            "会计明确说要推/过账/记进 Express 时才用"
        ),
        slots=(
            _keyword_slot(
                "ระบุใบที่จะส่ง เช่น เลขที่ใบกำกับหรือชื่อร้าน (คัดจากข้อความผู้ใช้เท่านั้น)",
                "要推的那张票(单号/店名/文件名·必须出自用户原话)· 系统据此定位唯一一张",
            ),
            SlotSpec(
                "account_set",
                required=False,
                source="user_text",
                desc_th="ชุดบัญชีปลายทางถ้าผู้ใช้ระบุ (คัดจากข้อความผู้ใช้เท่านั้น)",
                desc_zh="目标账套代码(用户说了才填·没说给 null,系统用连接里配的那个)",
            ),
            SlotSpec(
                "direction",
                required=False,
                source="model_freeform",
                desc_th="ทิศทาง: purchase(ซื้อ) / sales(ขาย)",
                desc_zh="方向(purchase 进项 / sales 销项)· 用户没说给 null,系统按税号自己判",
            ),
        ),
        handler="erp_push",
        risk=RISK_WRITE,
        timeout_s=ERP_PUSH_TIMEOUT_S,
    ),
    StewardTool(
        name=FILE_CONVERT,
        desc=(
            "把这一轮传上来的文件转成 Excel 表并做守恒校验(台账/流水核借贷余额链,"
            "普通表核列合计)· 会计说「转成 Excel / 导出成表格 / 帮我转一下这份」时用 · "
            "这一轮没有附件时绝不选它"
        ),
        slots=(),
        handler="file_convert",
        timeout_s=FILE_TOOL_TIMEOUT_S,
    ),
    StewardTool(
        name=VAT_REPORT_CHECK,
        desc=(
            "对这一轮传上来的销项 VAT 报告做三查:发票连号(缺号/乱序/重复/作废)、"
            "买家分组汇总、期间一致性 · 会计说「三查 / 查连号 / 看有没有跳号 / 这份报告核一下」"
            "时用 · 这一轮没有附件时绝不选它"
        ),
        slots=(),
        handler="vat_report_check",
        timeout_s=FILE_TOOL_TIMEOUT_S,
    ),
)

TOOLS_BY_NAME: dict[str, StewardTool] = {t.name: t for t in TOOLS}

# 闭集全集 + 哨兵:planner 解析时枚举外一律归 OUT_OF_SCOPE(诚实拒,绝不装懂)。
ALL_NAMES: tuple[str, ...] = tuple(TOOLS_BY_NAME)
OUT_OF_SCOPE = "out_of_scope"


@dataclass
class ToolContext:
    """工具以此身份执行 —— 复用现成 RLS/权限口径,绝不 bypass。

    allowed_client_ids=None 表示不限(老板/超管/scope_mode='all');给了集合就是被分派成员
    只看分到的账套,与 /api/tax-profile/matrix 的收窄口径同源(路由算好传进来)。

    today 走曼谷日历日:服务器跑 UTC,date.today() 在曼谷 00:00–07:00 还停在昨天,逾期与
    剩余天数会整体差一天(当天到期的义务被说成"还剩 1 天",简报的头条与桶序跟着错)。

    attachment_ids 走执行上下文而非参数槽:附件 id 根本不经过模型,塞进 slots 只会让
    services/agent/slots.py 的接地闸(source=user_text 的值必须逐字节出现在用户原话里)
    报假阳 —— 那道闸是为「模型编了一个客户名」设计的。与 user_id/allowed_client_ids 同层。
    """

    user: dict
    tenant_id: str
    user_id: str
    allowed_client_ids: Optional[frozenset] = None
    lang: str = "zh"
    today: date = field(default_factory=bangkok_today)
    user_text: str = ""
    session_id: str = ""
    attachment_ids: tuple = ()


def get(name: Optional[str]) -> Optional[StewardTool]:
    return TOOLS_BY_NAME.get(name or "")


def is_known(name: Optional[str]) -> bool:
    return (name or "") in TOOLS_BY_NAME


def catalog() -> str:
    """提示词里的工具表(从注册表现生成:加工具即改本表,提示词自动跟着变)。

    写/危险工具在表里带标记:大脑必须看得见「这个会真改客户的账」,才可能只在会计明说时挑它
    —— 提示词里手写一份工具清单迟早与注册表漂,标记也一并从 risk 现算。
    """
    lines = []
    for t in TOOLS:
        slot_names = ", ".join(s.name for s in t.slots) or "无"
        mark = "" if t.readonly else "【会改数据·须人批准】"
        lines.append(f"  - {t.name}: {mark}{t.desc}(参数: {slot_names})")
    return "\n".join(lines)


def slot_hints() -> str:
    """参数说明块(中文 desc_zh),让大脑知道每个参数该填什么、什么时候留空。"""
    lines = []
    for t in TOOLS:
        for s in t.slots:
            lines.append(f"  - {t.name}.{s.name}: {s.desc_zh}")
    return "\n".join(lines)


def public_catalog() -> list[dict[str, Any]]:
    """能力清单(拒绝时告诉用户「目前能帮你查这些」;探针端点也用它对外声明闭集)。"""
    return [{"name": t.name, "desc": t.desc, "readonly": t.readonly} for t in TOOLS]
