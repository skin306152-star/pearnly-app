#!/usr/bin/env python3
"""E2E 桩回包契约闸 —— 桩不许比真后端少给键。

出身(2026-07-30/31 两天栽两次,第三处躺在仓库里当验收证据):
  · _f1_steward_attach_local 把 GET /sessions/{id} 桩成 {messages: []},真后端逐条带
    attachments 投影 → 换真栈就红,查了半天。
  · _b2m1_steward_local 把 GET /status 桩成 {enabled: gate},真后端**无条件**回
    attachments: limits() → 回形针按钮与输入区说明在那 14 条用例里从来没渲染过,
    而那批截图是当验收证据提交进仓库的。少一个键 = 拍的是产品里不存在的界面。

判据是「顶层键集合不得少于真后端」,外加一条:登记为 not_null 的键不许写成 null /
undefined 字面量 —— attachments: null 键在值不在,前端 `resp && resp.attachments` 照样
拿不到限额,回形针照样不画,跟漏键一个后果。

「怎么知道真后端回什么」这一问不靠通用静态分析(判据做不准就会误报,误报的闸会被 skip
掉,等于没装):登记表写在下面的 CONTRACTS,配 tests/unit/test_e2e_stub_contract_gate.py
三道锁 ——
  ① 防漂:用 ast 读 routes/steward_routes.py 里处理函数的**无条件**返回字面量,断言它与
     登记表逐键相等(后端加一个键,测试当场红,逼登记表跟着改)。
  ② 覆盖率:登记表里每个端点都必须真被至少一个 spec 桩过(否则表烂了没人发现)。
  ③ 反证:喂故意少键 / 写成 null 的桩,断言这道闸真会红。

只登记「无条件返回固定键」的端点。tasks/{id} 与 messages 的投影带条件分支
(error_code / authorization / loop 按任务状态出现),照抄进登记表会对合法的桩误报,
留给各自 spec 的断言兜。

用法: python scripts/check_e2e_stub_contracts.py [--dir tests/e2e] [--quiet] [--list]
退出码 0 = 每处桩都不比真后端少给, 1 = 有桩少给键(FAIL 模式 · CI lint job + pre-push)。
"""

import argparse
import io
import json as jsonlib
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
E2E_DIR = ROOT / "tests" / "e2e"
BACKEND = "routes/steward_routes.py"

PRESENT = "present"  # 键必须在
NOT_NULL = "not_null"  # 键必须在,且值不许是 null / undefined 字面量

# enabled 只判在:false 是闸关时的真值。attachments 判到值:限额是前端画不画回形针的唯一
# 依据(ai-steward.js probe),写 null 与漏键同罪。
CONTRACTS = [
    {
        "id": "GET /api/ai/steward/status",
        "handler": "get_status",
        "path": re.compile(r"/steward/status$"),
        "keys": {"enabled": PRESENT, "attachments": NOT_NULL},
    },
    {
        "id": "POST /api/ai/steward/sessions",
        "handler": "create_session",
        "path": re.compile(r"/steward/sessions$"),
        "keys": {"session_id": NOT_NULL},
    },
    {
        "id": "GET /api/ai/steward/sessions/{id}",
        "handler": "get_session",
        "path": re.compile(r"/steward/sessions/[^/]+$"),
        "keys": {"session_id": NOT_NULL, "messages": NOT_NULL},
    },
]

_IDENT = re.compile(r"[A-Za-z_$][\w$]*")
_CALL = re.compile(r"^([A-Za-z_$][\w$]*)\s*\(")
_BARE = re.compile(r"^[A-Za-z_$][\w$]*$")
_STRINGIFY = re.compile(r"JSON\.stringify\s*\(")
# 一行内的字符串字面量(URL 不跨行);模板串一并收,${} 归一成通配。
_STR = re.compile(
    r"'([^'\n\\]*(?:\\.[^'\n\\]*)*)'"
    r"|\"([^\"\n\\]*(?:\\.[^\"\n\\]*)*)\""
    r"|`([^`\n\\]*(?:\\.[^`\n\\]*)*)`"
)
# 正则字面量当路由判据:/\/steward\/sessions\/[^/]+$/.test(p)
# 字符组要整块吃掉 —— [^/] 里那个裸斜杠不是正则的收尾,漏了这一条就一处正则判据都认不出。
_RE_TEST = re.compile(r"/((?:\\.|\[[^\]\n]*\]|[^/\n])+)/[a-z]*\s*\.test\s*\(")
# 桩点判据:从路径字面量到 fulfill/json 之间只许有胶水(箭头函数壳、return、await)。
# 隔着别的语句就不是这条路径的回包 —— p.endsWith('/steward/sessions') 后面接计数、
# posts.filter(...) 里的路径比较,都在这里被挡掉,不当桩点看。
_GLUE = re.compile(
    r"^[\s,)\]}{]*(?:async\s*)?(?:\([^()]*\)\s*=>\s*)?[\s{]*(?:return\s+)?(?:await\s+)?$"
)
_HEAD = re.compile(r"(?:[\w$]+\.)?(fulfill|json)\s*\(")
_HEAD_WINDOW = 400
_QUOTES = "'\"`"
_SKIP = "skip"  # 故障注入(非 2xx)· 不当契约看


class Site:
    """一处桩点。keys 为 None = 回包形状读不出(报出来,不当绿);
    loose = 路径判据跟不到回包(分支里先做了别的事),不判红也不算覆盖,只在汇总里点数。"""

    def __init__(self, rel, line, contract, keys, loose=False):
        self.rel, self.line, self.contract = rel, line, contract
        self.keys, self.loose = keys, loose


def _read_string(text, i):
    quote = text[i]
    j = i + 1
    while j < len(text):
        if text[j] == "\\":
            j += 2
            continue
        if text[j] == quote:
            return text[i + 1 : j], j + 1
        j += 1
    return None, len(text)


def _skip_comment(text, i):
    nxt = text[i + 1 : i + 2]
    if nxt == "/":
        end = text.find("\n", i)
        return len(text) if end < 0 else end
    if nxt == "*":
        end = text.find("*/", i)
        return len(text) if end < 0 else end + 2
    return i


def _skip_ws(text, i):
    while i < len(text):
        if text[i].isspace():
            i += 1
            continue
        if text[i] == "/":
            j = _skip_comment(text, i)
            if j != i:
                i = j
                continue
        return i
    return i


def _skip_value(text, i):
    """从值起点扫到顶层的 , 或收尾括号 —— 三元里的 : 不算断点(值可以是 a ? b : c)。"""
    depth = 0
    while i < len(text):
        c = text[i]
        if c == "/":
            j = _skip_comment(text, i)
            if j != i:
                i = j
                continue
        if c in _QUOTES:
            _, i = _read_string(text, i)
            continue
        if c in "([{":
            depth += 1
        elif c in ")]}":
            if depth == 0:
                return i
            depth -= 1
        elif c == "," and depth == 0:
            return i
        i += 1
    return i


def entries(text, i):
    """i 指向 { → [(键, 值起, 值止)];展开运算符/计算键读不出时返 None。"""
    if i >= len(text) or text[i] != "{":
        return None
    out = []
    j = i + 1
    while True:
        j = _skip_ws(text, j)
        if j >= len(text):
            return None
        if text[j] == "}":
            return out
        if text.startswith("...", j):
            return None
        if text[j] in "'\"":
            key, j = _read_string(text, j)
            if key is None:
                return None
        else:
            m = _IDENT.match(text, j)
            if not m:
                return None
            key, j = m.group(0), m.end()
        j = _skip_ws(text, j)
        if j < len(text) and text[j] in ",}":  # 简写属性 { session_id, }
            out.append((key, j - len(key), j))
            if text[j] == "}":
                return out
            j += 1
            continue
        if j >= len(text) or text[j] != ":":
            return None
        start = _skip_ws(text, j + 1)
        j = _skip_value(text, start)
        out.append((key, start, j))
        j = _skip_ws(text, j)
        if j < len(text) and text[j] == ",":
            j += 1


def object_keys(text, i):
    ent = entries(text, i)
    return None if ent is None else {k: text[s:e].strip() for k, s, e in ent}


def _decl_keys(text, name):
    m = re.search(r"\b(?:const|let|var)\s+" + re.escape(name) + r"\s*=\s*\{", text)
    return object_keys(text, text.rindex("{", m.start(), m.end())) if m else None


def _function_keys(text, name):
    """function NAME(...) 的第一个能读出对象的 return —— 中间 return 数组/别的先跳过。"""
    m = re.search(r"\bfunction\s+" + re.escape(name) + r"\s*\(", text)
    if not m:
        return None
    body = text[m.end() :]
    for r in re.finditer(r"\breturn\b", body):
        keys = expr_keys(body, r.end(), _skip_value(body, r.end()))
        if keys is not None:
            return keys
    return None


def expr_keys(text, start, end):
    """一段表达式 → 顶层键;字面量直读,标识符/函数调用在同文件里回溯一层。"""
    i = _skip_ws(text, start)
    expr = text[i:end].strip().rstrip(";")
    if not expr:
        return None
    if expr.startswith("{"):
        return object_keys(text, i)
    m = _CALL.match(expr)
    if m:
        return _function_keys(text, m.group(1))
    if _BARE.match(expr):
        return _decl_keys(text, expr)
    return None


def _args(text, paren):
    """paren 指向 ( → 各顶层实参的 (起, 止)。"""
    out = []
    i = paren + 1
    while i < len(text):
        start = i
        i = _skip_value(text, i)
        out.append((start, i))
        if i >= len(text) or text[i] != ",":
            break
        i += 1
    return out


def _json_string_keys(literal):
    try:
        obj = jsonlib.loads(literal)
    except ValueError:
        return None
    if not isinstance(obj, dict):
        return None
    return {k: ("null" if v is None else "x") for k, v in obj.items()}


def _fulfill_keys(text, paren):
    """r.fulfill({status, json, body}) → 回包键;非 2xx 是故障注入,返 _SKIP。"""
    ent = entries(text, _skip_ws(text, paren + 1))
    if ent is None:
        return None
    by_key = {k: (s, e) for k, s, e in ent}
    status = text[slice(*by_key["status"])].strip() if "status" in by_key else ""
    if status.isdigit() and not 200 <= int(status) < 300:
        return _SKIP
    if "json" in by_key:
        return expr_keys(text, *by_key["json"])
    if "body" in by_key:
        start, end = by_key["body"]
        m = _STRINGIFY.match(text, start)
        if m:
            return expr_keys(text, m.end(), _skip_value(text, m.end()))
        if text[start] in _QUOTES:
            body, _ = _read_string(text, start)
            return _json_string_keys(body) if body else None
    return None


def _norm(raw):
    """路径字面量 → 可比路径:正则转义、模板插值、单段通配、尾锚、查询串一并抹平。"""
    s = raw.replace("\\", "")
    s = re.sub(r"\$\{[^}]*\}", "*", s)
    s = s.replace("[^/]+", "*")
    return s.rstrip("$").split("?", 1)[0]


def _in_comment(text, pos):
    line_start = text.rfind("\n", 0, pos) + 1
    prefix = _STR.sub("", text[line_start:pos])
    return "//" in prefix or prefix.lstrip().startswith(("*", "/*"))


def _carriers(text):
    """(路径判据结束下标, 归一化路径) —— 字符串与 /re/.test() 两种写法都收。"""
    for m in _STR.finditer(text):
        raw = m.group(1) or m.group(2) or m.group(3) or ""
        if "/steward" in raw and not _in_comment(text, m.start()):
            yield m.end(), _norm(raw)
    for m in _RE_TEST.finditer(text):
        if "steward" in m.group(1) and not _in_comment(text, m.start()):
            yield _skip_value(text, m.end()) + 1, _norm(m.group(1))


def scan(path, rel):
    text = path.read_text(encoding="utf-8")
    sites = []
    for end, url in _carriers(text):
        contract = next((c for c in CONTRACTS if c["path"].search(url)), None)
        if not contract:
            continue
        line = text.count("\n", 0, end) + 1
        head = _HEAD.search(text, end, end + _HEAD_WINDOW)
        if not head or not _GLUE.match(text[end : head.start()]):
            # 跟不到回包:可能是计数分支、断言里的路径比较,也可能是先做了别的事才 fulfill。
            # 分不清就不判 —— 宁可漏一处,也不能误报把闸弄成噪音源。
            sites.append(Site(rel, line, contract, None, loose=True))
            continue
        paren = head.end() - 1
        if head.group(1) == "fulfill":
            keys = _fulfill_keys(text, paren)
        else:
            args = _args(text, paren)
            keys = expr_keys(text, *args[1]) if len(args) > 1 else None
        if keys == _SKIP:
            continue
        sites.append(Site(rel, line, contract, keys))
    return sites


def all_sites(e2e_dir):
    root = Path(e2e_dir)
    out = []
    for path in sorted(root.rglob("*.spec.js")):
        out.extend(scan(path, path.relative_to(root.parent.parent).as_posix()))
    return out


def failures(sites):
    out = []
    for s in sites:
        if s.loose:
            continue
        head = f"{s.rel}:{s.line} 桩了 {s.contract['id']}"
        if s.keys is None:
            out.append(f"{head},回包形状读不出 —— 写成对象字面量(或同文件里的常量/函数)")
            continue
        for key, mode in s.contract["keys"].items():
            if key not in s.keys:
                out.append(
                    f"{head},漏了真后端无条件回的 `{key}`" f"({BACKEND}::{s.contract['handler']})"
                )
            elif mode == NOT_NULL and s.keys[key] in ("null", "undefined"):
                out.append(f"{head},`{key}` 写成 {s.keys[key]} —— 键在值不在,前端拿到的跟漏键一样")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="E2E 桩回包契约闸(桩的顶层键不得少于真后端)")
    ap.add_argument("--dir", default=str(E2E_DIR), help="E2E 目录")
    ap.add_argument("--quiet", action="store_true", help="绿时不打表头")
    ap.add_argument("--list", action="store_true", help="列出扫到的每一处桩点")
    args = ap.parse_args(argv)

    e2e_dir = Path(args.dir)
    if not e2e_dir.is_dir():
        print(f"[X] 目录不存在: {e2e_dir}")
        return 1

    sites = all_sites(e2e_dir)
    fails = failures(sites)
    loose = [s for s in sites if s.loose]
    if args.list:
        for s in sites:
            if s.loose:
                shown = "跟不到回包(不判)"
            else:
                shown = "读不出" if s.keys is None else ",".join(sorted(s.keys))
            print(f"  {s.rel}:{s.line}  {s.contract['id']}  → {shown}")
    if fails:
        print("=" * 70)
        print("E2E 桩回包契约闸(桩给的顶层键 → 不得少于真后端该端点的无条件投影)")
        print("=" * 70)
        for f in fails:
            print(f"  [X] {f}")
        print(f"\n结果: FAIL - {len(fails)} 处桩比真后端少给(截图会拍到产品里不存在的界面)")
        return 1
    if not args.quiet:
        tail = f"(另有 {len(loose)} 处路径判据跟不到回包 · --list 看)" if loose else ""
        print(
            f"E2E 桩回包契约闸: PASS - {len(sites) - len(loose)} 处桩点,"
            f"键集合都不少于真后端{tail}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
