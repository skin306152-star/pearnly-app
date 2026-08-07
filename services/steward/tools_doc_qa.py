# -*- coding: utf-8 -*-
"""读文问答(S2 工具箱)—— 只答文件里写了什么,不算账、不编数字。

取明文字节走 tool_scope.single_attachment(与 table_generate/file_convert 同一套租户/会话/
防穿越三锚);「问题是什么」走 tool_scope.attached_message_text(见下)。文本提取按格式分流:
  PDF(有文字层) services.fileconv.text_layer.extract_pages,纯函数,零成本,绝不落 OCR;
  PDF(无文字层)/图片  与 file_convert 同一条 OCR 计费轨(services.fileconv.convert.
               convert_pdf/convert_image,tenant_id 传入归因)——但只在 args.model_ok 为真
               时才碰这一支,没这张「人点过头」的凭据绝不悄悄烧一次模型钱(见 _ocr_pages);
               没 model_ok 时返回 ERR_NEEDS_MODEL,与 attach_turn 弹计费卡同一套机制
               (tools_file.vat_report_check 的模型回退闸先例),不新开一条计费口子;
  xlsx/xlsm/xls services.fileconv.excel_in.convert_excel 转文本网格(一张 sheet = 一"页");
  csv/tsv/txt  按常见编码级联原样解码成文本(单一"页")。
  其余格式(docx 等)诚实拒绝,拒绝文案里说清目前支持哪些。

问题不经模型槧参数:附件工具的参数是文件,file 根本不经过 slots 接地(registry_slots
顶注的「附件走执行上下文而非参数槧」),于是「问题是什么」也拿不到槧值——改从挂着这份附件
的那条用户消息(attachment.message_id)原样取回,同一次 handle_message 落的,不新开一条
「附件也是槧」的机制(见 store.message_text)。

命门(两条不许违反的红线,单测 PromptContractTests 断言逐条写死在提示词里):
  ① 只答文中写了的内容,文中没有的数不许算不许编 —— 会计要算数就引导去 table_generate;
  ② 每句结论标出第几页,citations 的 quote 必须是原文里真找得到的片段(_parse_answer 会
     逐条核对,quote 在对应页的原文里搜不到就丢掉那条引用,不当模型的概括直接端上桌)。
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Optional

from services.agent import reply_guard
from services.agent.contracts import ToolResult
from services.steward import tool_scope
from services.steward.registry import ToolContext

logger = logging.getLogger(__name__)

TASK = "steward_doc_qa"

ERR_NEEDS_MODEL = "steward.doc_qa_needs_model"
ERR_UNREADABLE_TABLE = "steward.doc_qa_unreadable"
ERR_UNSUPPORTED_TYPE = "steward.doc_qa_unsupported_type"
ERR_NO_QUESTION = "steward.doc_qa_no_question"
ERR_MODEL_FAILED = "steward.doc_qa_model_failed"

_TABLE_EXTS = (".xlsx", ".xlsm", ".xls")
_RAW_TEXT_EXTS = (".csv", ".tsv", ".txt")
# 与 tools_file._IMAGE_EXTS 同一份小常量各自持有(两个模块的取件路各自独立,不为四个扩展名
# 拉一条跨模块 import)。
_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")
SUPPORTED_EXTS = (".pdf",) + _IMAGE_EXTS + _TABLE_EXTS + _RAW_TEXT_EXTS

# 常见编码级联(同 services.recon.bank_table_io._load_csv_sheets 的顺序:UTF-8 BOM → UTF-8 →
# 泰文 cp874 → 中文 gbk → latin-1 兜底),纯文本没有 openpyxl 那样的结构探针,只能按序试解码。
# 不并轨 services.knowledge.ingest.TEXT_DECODE_ORDER:那份序刻意不含 gbk,语义不同。
_TEXT_ENCODINGS = ("utf-8-sig", "utf-8", "cp874", "gbk", "latin-1")

# 提示词预算:整份文一次性喂给模型的字符上限。电子台账/长合同动辄十几万字,原样塞满一是撑爆
# 模型上下文窗口,二是每字都算 token 钱;而一个问题通常只落在其中一两页,所以走「按关键词
# 命中排序、优先保留最相关页」而不是无差别砍尾——砍尾会砍掉刚好问的那页(结论/关键条款常在
# 文档中段甚至末段)。24000 字符 ≈ 中文一万余字,覆盖多数合同/台账单份问答且留足输出预算。
MAX_PROMPT_CHARS = 24000
_MODEL_TIMEOUT_S = 45
_MAX_CITATIONS = 8
_MAX_QUOTE_LEN = 300

_SPACE = re.compile(r"\s+", re.UNICODE)

PROMPT = """你是泰国代账事务所的文档问答助手。下面是一份文件逐页提取的文字,每页前面标了页码。
会计问了一个问题,你只能依据下面这份文字回答。

铁律(不许违反):
1. 只答这份文字里明确写了的内容,一个字都不能是文字之外的常识或猜测。
2. 文字里没有的数字绝不能编、绝不能算。这份文字如果没写会计要的那个数,直说"没找到",
   不要凑一个像是对的答案。
3. 会计要你计算、汇总、按条件筛选统计——这些活不归你做,直说"这个要用 table_generate
   处理,我这里只能读文中原句"。
4. 每句结论后面标出自第几页,citations 数组的 quote 必须是原文里能找到的一句话或一个
   片段,不是你的概括。
5. 只输出一个 JSON 对象,不带任何其他文字。

文件内容:
{pages}

会计的问题:{question}

输出 JSON 形状:
{{"answer": "...", "citations": [{{"page": 1, "quote": "原文中的一句话"}}]}}"""


def doc_read_qa(ctx: ToolContext, args: dict) -> ToolResult:
    """读文问答的执行入口:取件 → 取问题 → 抽文本 → 挑相关页 → 问模型 → 核对引用。"""
    row, err = tool_scope.single_attachment(ctx)
    if err:
        return err
    name = row.get("original_name") or "file"
    question = tool_scope.attached_message_text(ctx, row)
    if not question:
        return ToolResult(
            ok=False, error_code=ERR_NO_QUESTION, data=tool_scope.attachment_name(row)
        )
    pages, err = _pages_of(row, name, args=args, ctx=ctx)
    if err:
        return err
    kept = select_pages(pages, question, max_chars=MAX_PROMPT_CHARS)
    outcome = ask_model(_build_prompt(kept, question), ctx=ctx)
    if not outcome.ok:
        return ToolResult(
            ok=False, error_code=ERR_MODEL_FAILED, data=tool_scope.attachment_name(row)
        )
    parsed = parse_answer(outcome.data, kept)
    if parsed is None:
        return ToolResult(
            ok=False, error_code=ERR_MODEL_FAILED, data=tool_scope.attachment_name(row)
        )
    return ToolResult(
        ok=True,
        data={
            "filename": name,
            "question": question,
            "answer": parsed["answer"],
            "citations": parsed["citations"],
            "page_count": len(pages),
            "pages_used": sorted(no for no, _ in kept),
        },
    )


# ── 取文本(逐页,citations 的页码单位) ──────────────────────


def _decode_text(content: bytes) -> Optional[str]:
    for enc in _TEXT_ENCODINGS:
        try:
            return content.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return None


def _table_text(table) -> str:
    """一张 Table → 一段可读文本(表头 + 逐行,tab 分隔)——喂给问答模型看的是文字,
    不是结构化网格,所以这里只管"读起来像原表",不追求可反解析。"""
    lines = ["\t".join(str(c) for c in table.columns)]
    lines.extend("\t".join("" if c is None else str(c) for c in row) for row in table.rows)
    return "\n".join(lines)


def _pages_of(
    row: dict, name: str, *, args: dict, ctx: ToolContext
) -> tuple[Optional[list], Optional[ToolResult]]:
    """字节 → 逐页文本。表格族/有文字层的 PDF 走本地纯函数,零成本;扫描件 PDF/图片走
    _ocr_pages(与 file_convert 同一条 OCR 计费轨,但要先有 model_ok 这张凭据)。认不出的
    格式(docx 等)一律诚实拒绝,不猜。"""
    from services.fileconv import text_layer
    from services.fileconv.excel_in import convert_excel
    from services.fileconv.model import REJECT_STATUSES

    content = row["content"]
    ext = Path(name).suffix.lower()
    if ext == ".pdf":
        pages = text_layer.extract_pages(content)
        if text_layer.has_text_layer(pages):
            return pages, None
        return _ocr_pages(content, name, row, args, ctx, is_image=False)
    if ext in _IMAGE_EXTS:
        return _ocr_pages(content, name, row, args, ctx, is_image=True)
    if ext in _TABLE_EXTS:
        result = convert_excel(content, source_name=name)
        if result.status in REJECT_STATUSES or not result.tables:
            return None, ToolResult(
                ok=False,
                error_code=ERR_UNREADABLE_TABLE,
                data={**tool_scope.attachment_name(row), "status": result.status},
            )
        return [_table_text(t) for t in result.tables], None
    if ext in _RAW_TEXT_EXTS:
        text = _decode_text(content)
        if text is None:
            return None, ToolResult(
                ok=False, error_code=ERR_UNREADABLE_TABLE, data=tool_scope.attachment_name(row)
            )
        return [text], None
    return None, ToolResult(
        ok=False,
        error_code=ERR_UNSUPPORTED_TYPE,
        data={**tool_scope.attachment_name(row), "ext": ext or "(none)"},
    )


def _ocr_pages(
    content: bytes, name: str, row: dict, args: dict, ctx: ToolContext, *, is_image: bool
) -> tuple[Optional[list], Optional[ToolResult]]:
    """扫描件 PDF / 图片的取文本路:convert_pdf/convert_image 与 file_convert 同参数同姿势
    (tenant_id=ctx.tenant_id 归因)——计费走的是既有 OCR 桥,本工具不另开收费点。

    args.model_ok 是「人在计费卡上点过『会过一次模型』」的凭据(attach_turn.decide 落的,
    同 tools_file.vat_report_check 的模型回退闸一个纪律):没有这张凭据绝不调 convert_*,
    直接返回 ERR_NEEDS_MODEL 让上层弹卡等一次点击(钱路防线①②)。

    ConvertResult 通常只出一张合并过的 Table(扫描多页会被 ocr_bridge 按台账/流水链拼成一张,
    或按 generic 网格逐页拼行)——「一张 Table = 一'页'」,与 _TABLE_EXTS 分支「一张 sheet
    = 一'页'」同一约定,citations 的页号因此多半落在 1,这是已知的简化,不是 bug。
    """
    if not args.get("model_ok"):
        return None, ToolResult(
            ok=False, error_code=ERR_NEEDS_MODEL, data=tool_scope.attachment_name(row)
        )
    from services.fileconv.convert import convert_image, convert_pdf
    from services.fileconv.model import REJECT_STATUSES

    convert = convert_image if is_image else convert_pdf
    result = convert(content, source_name=name, tenant_id=ctx.tenant_id)
    if result.status in REJECT_STATUSES or not result.tables:
        return None, ToolResult(
            ok=False,
            error_code=ERR_UNREADABLE_TABLE,
            data={**tool_scope.attachment_name(row), "status": result.status},
        )
    return [_table_text(t) for t in result.tables], None


# ── 相关页截断 ──────────────────────────────────────────────


def _shingles(text: str) -> list[str]:
    """问题 → 2 字符滑窗(bigram)。中文/泰文没有空格分词,regex `\\w+` 会把整句问题揉成
    一个词(CJK/泰文连续字符全落在 \\w 范围内),"关键词命中"就名存实亡——两页里各出现
    一次"付款期限"也判不出谁更相关,因为词表里根本没有这个词,只有一整句问题。2-gram
    不需要分词器,对中/泰/英三种脚本一致有效,足够撑起"谁更相关"这种粗粒度排序
    (不追求语义,只追求页与问题的字面重叠密度)。"""
    cleaned = _SPACE.sub("", (text or "").lower())
    if len(cleaned) < 2:
        return [cleaned] if cleaned else []
    return [cleaned[i : i + 2] for i in range(len(cleaned) - 1)]


def _score(text: str, shingles: list[str]) -> int:
    low = text.lower()
    return sum(low.count(s) for s in shingles)


def select_pages(pages: list, question: str, *, max_chars: int) -> list[tuple[int, str]]:
    """页优先级截断(纯函数):含问题字面重叠越多的页越先留,直到撑满预算;单页超预算
    就地截断那一页。命中数全等(常见于跨语种问答,问题词面在文中根本不出现)时靠 Python
    sort 的稳定性回落成「从头保留」,不是随机——原文顺序本身就是最合理的默认优先级。"""
    if not pages:
        return []
    shingles = _shingles(question)
    ranked = sorted(enumerate(pages, start=1), key=lambda kv: -_score(kv[1], shingles))
    budget = max_chars
    kept: list[tuple[int, str]] = []
    for page_no, text in ranked:
        if budget <= 0:
            break
        piece = text[:budget]
        if piece:
            kept.append((page_no, piece))
        budget -= len(piece)
    kept.sort(key=lambda kv: kv[0])
    return kept


def _render_pages(kept: list[tuple[int, str]]) -> str:
    return "\n\n".join(f"[第 {no} 页]\n{text}" for no, text in kept)


def _build_prompt(kept: list[tuple[int, str]], question: str) -> str:
    return PROMPT.format(pages=_render_pages(kept), question=question)


# ── 模型调用与输出核对 ──────────────────────────────────────


ask_model = tool_scope.make_ask_model(TASK, _MODEL_TIMEOUT_S)


def _as_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_answer(data: Any, kept: list[tuple[int, str]]) -> Optional[dict]:
    """模型输出 → 校验过的 {answer, citations}。形状不对/答案失控 → None(调用方据此判
    ERR_MODEL_FAILED)。citations 逐条核对:page 必须在送去的页里,quote 必须能在那一页的
    原文里搜到——搜不到就丢掉那一条,不把编出来的一句"听起来像"端给会计核对页码。"""
    if not isinstance(data, dict):
        return None
    answer = str(data.get("answer") or "").strip()
    if not answer or not reply_guard.sane(answer):
        return None
    valid_pages = dict(kept)
    citations = []
    for raw in (data.get("citations") or [])[:_MAX_CITATIONS]:
        if not isinstance(raw, dict):
            continue
        page = _as_int(raw.get("page"))
        quote = str(raw.get("quote") or "").strip()
        if not quote or page not in valid_pages:
            continue
        if quote.lower() not in valid_pages[page].lower():
            continue
        citations.append({"page": page, "quote": quote[:_MAX_QUOTE_LEN]})
    return {"answer": answer, "citations": citations}
