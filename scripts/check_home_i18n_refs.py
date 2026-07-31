#!/usr/bin/env python3
"""/home 词典引用闸 —— 取词引到的键必须真在 window.I18N 里,否则界面永远不翻译。

出身:src/home/core.ts:109 的 t() 跟 /ai 的 at() 是同一个回落 ——

    let s = (I18N[currentLang] && I18N[currentLang][key]) || key;

取不到就把 key 原样返回。/ai 那边正因为没人查引用,at('intake_failed_batch_n') 把下划线
标识符印在了 402 余额不足卡上,而 check_i18n --strict 同时报「4 语 各 4969 keys · 0
missing」—— 那道闸只对拍四个语言块之间齐不齐,从没问过"这 4969 条有没有人引、引的人
写对没有"。/home 有一模一样的洞,还大 3 倍(3400+ 处引用)。

两种落空、两种症状,都是同一个缺陷:
  · t('没定义的键') → 界面上直接印出这个标识符。
  · data-i18n="没定义的键" → applyLang 的 `if (I18N[lang][key])` 守卫不成立,元素被跳过,
    模板里写死的中文原地不动 —— 泰语用户永远看中文,而且一声不吭。

本闸只管一件事:**引用得到定义**。
  · 定义 = static/i18n-data.js 的 window.I18N 四个语言块里任意一块出现过这个键。
  · 不查四语齐全 —— 那是 check_i18n --strict 的活,两道闸各管一层,混在一起谁都说不清。
  · 只认字面量键。t('bill_st_' + status) 这类拼出来的键静态查不了,由调用方自己的测试兜。

常量键表(2026-07-31 补进射程):`const _DUP_FIELD_I18N: Record<string, string> =
{ doc_date: 'erp-dup-field-date', ... }` 这种把键名存进表、再 `t(表[变量] || '兜底键')`
取出来的写法。兜底键那半截建闸当天就看得见(erp-log-card.ts 漏补 erp-dup-field-other
就是这么抓到的),表里的键此前完全在射程外 —— 实测 16 张表 117 个键,不是原先估的 6 张 56 个。
判据见 table_keys() 的注释:不靠命名猜,靠对拍词典,今天 0 落空 0 误报。

取词入口(新增第五个入口时记得同步这里):
  · 全局 t(key, params) —— core.ts 定义 + `window.t = t`,62 个文件写 `/* global t */` 裸调。
  · 本地包装 _t / _bt / T —— 各模块自己的轻桥,转发 window.t。⚠️ 它们大多写成
    `window.t(k) || fb`,而 window.t 取不到时返回的是 key 本身(真值)→ fb 永远轮不上,
    症状跟裸调 t() 完全一样。只有 kbT / workspace-switcher 那两个判了 `s !== key`。
  · 共享包装 kbT(key, fallback) —— knowledge-api.ts 导出,知识库 6 个模块 import 着用。
  · data-i18n / data-i18n-placeholder 属性 —— 写在 src/home/*.ts 的模板串和 home.html 里,
    由 core-boot.ts 的 applyLang 喂给 I18N;只扫 JS 调用会漏掉大半(本树 702 处属性)。
  · I18N[lang]['字面量'] 直接下标(core-boot.ts 取 lang-name 那种)。

扫源不扫产物:src/home/*.ts 经 vite(esbuild minify)打成 static/dist/main.js,字符串
字面量原样进包,但本地包装函数名会被压掉(_t/T/kbT 全变单字母)—— 在产物上认取词入口
只能靠猜。源是人改的地方,也是唯一能给出可修行号的地方;产物由「build+dist 一致」那道
闸保证跟源同步,不必在这里重扫一遍。static/{recon-mapping,recon-review,erp-mrerp-connect,
erp-log-enhance}.js 虽然也打进 home 页的 pre/post bundle,但它们各带各的自含字典
(erp-mrerp-connect 的 T[key]),不吃 window.I18N,不在本闸射程。

存量基线:建闸时(2026-07-31)全树 3353 处引用里只有 1 处落空
(auto-erp-subtab-connect-only),当天记在 scripts/home_i18n_refs_baseline.txt 里免罪 ——
补它要写 4 语文案,属用户可见改动,不混进建闸那一笔。**同日补齐并配了真浏览器四语验收,
基线随之删除,本闸现在是 0 容忍**;--update-baseline 的机制留着,但用它免罪要同步改掉
tests/unit/test_home_i18n_refs_gate.py 里那条 0 容忍断言,免不成默默的。

用法: python scripts/check_home_i18n_refs.py [--root .] [--update-baseline]
退出码 0 = 没有基线之外的落空, 1 = 有新增落空(FAIL 模式 · CI lint job)。
反证测试 tests/unit/test_home_i18n_refs_gate.py:每种引用形状都喂一个不存在的键,断言闸真会红。
"""

import argparse
import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from js_key_scan import (  # noqa: E402
    DICT_KEY_DEF,
    call_keys,
    in_comment,
    line_of,
    read_string,
    skip_comment,
)

# 报告是中文的,而 Windows 控制台默认码页(本机 cp874)编不了 —— 不接管 stdout 的话第一行
# print 就 UnicodeEncodeError 退 1,跟真 FAIL 同一个退出码,分不出是闸红还是环境崩。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "scripts" / "home_i18n_refs_baseline.txt"

# /home 的键带连字符和点:dxb-up-title / agent.ok.notifications / set-group-about。
# ⚠️ 跟 /ai 那道闸(键只有 [A-Za-z_]\w*)不同,别互抄。
_KEY = re.compile(r"^[A-Za-z_$][\w.$-]*$")

_GLOBAL_GETTER = "t"
_WRAPPERS = ("_t", "_bt", "kbT", "T")

_HEAD_TPL = r"(?<![\w.$])(?:(?:window|self|globalThis)\.)?(?:%s)\("
_GLOBAL_HEAD = re.compile(_HEAD_TPL % _GLOBAL_GETTER)

# 「这个函数是取词的吗」:函数体开头不远处转发给 window.t,或直接读 I18N(core.ts 的
# t() 本尊就是这种)才算。同名不同物的局部函数不能一并当取词入口 —— 尤其 T 在 TS 里
# 还是泛型参数的常用名。
_GETTER_BODY = ("window.t", "w.t(", "root.t(", "I18N[")
_BODY_WINDOW = 240

_ATTR = re.compile(r"data-i18n(?:-placeholder)?=(?:\"([^\"]*)\"|'([^']*)')")
# 词典本尊的两层下标 I18N[lang]['键']。左边的 (?<![\w.$]) 是为了不把 erp-log-card.ts 的
# _EXPRESS_REASON_I18N[code] 这类同后缀的常量表当成词典读。
_I18N_INDEX = re.compile(
    r"(?<![\w.$])(?:window\.)?I18N\[[^\]\n]+\]\[\s*(?:'([^']+)'|\"([^\"]+)\")\s*\]",
)
_IMPORT_NAMES = re.compile(r"import\s*\{([^}]*)\}\s*from")

# 常量键表:具名对象字面量,冒号右边放词条键,再 t(表[变量]) 取出来。
_TABLE_DECL = re.compile(r"\b(?:const|let|var)\s+[A-Za-z_$][\w$]*\s*(?::[^=\n]*)?=\s*\{")
_TABLE_VALUE = re.compile(r":\s*'([^'\n]*)'")
_TABLE_MIN_KEYS = 2
# 判据取自真词典(4993 条):最短的键 4 个字符,没有一条不含小写字母。
_KEY_MIN_LEN = 4


def source_files(root):
    home = root / "src" / "home"
    files = sorted(p for p in home.rglob("*.ts") if p.is_file())
    files += sorted(p for p in home.rglob("*.js") if p.is_file())
    index = root / "home.html"
    if index.is_file():
        files.append(index)
    return files


def defined_keys(root):
    src = root / "static" / "i18n-data.js"
    if not src.is_file():
        return set()
    text = src.read_text(encoding="utf-8")
    return {m.group(1) or m.group(2) for m in DICT_KEY_DEF.finditer(text)}


def _defines_getter(text, name):
    """文件里有没有一个真取词的 `function name(`(转发 window.t 或直接读 I18N)。"""
    for m in re.finditer(r"(?:export\s+)?function\s+%s\s*\(" % re.escape(name), text):
        if any(f in text[m.end() : m.end() + _BODY_WINDOW] for f in _GETTER_BODY):
            return True
    return False


def documents(root):
    """[(相对路径, 正文)] · 全树读一遍。

    下面两趟(先找共享取词桥、再收引用)吃的是同一份正文;各读各的等于把 3MB 的 src/home
    读两遍,而第二趟拿到的还可能是中途被改过的另一个版本。
    """
    return [
        (p.relative_to(root).as_posix(), p.read_text(encoding="utf-8")) for p in source_files(root)
    ]


def exported_getters(docs):
    """全树扫一遍:哪些名字是 `export function` 出去的取词桥(今天只有 kbT)。"""
    names = set()
    for _rel, text in docs:
        for name in _WRAPPERS:
            exported = re.search(r"export\s+function\s+%s\s*\(" % re.escape(name), text)
            if exported and _defines_getter(text, name):
                names.add(name)
    return names


def _active_getters(text, shared):
    """这个文件里,哪些名字算取词入口。"""
    active = set()
    # 全局 t:除非本文件用一个同名局部函数把它遮了,而那个函数并不取词。
    if not re.search(r"function\s+t\s*\(", text) or _defines_getter(text, "t"):
        active.add(_GLOBAL_GETTER)
    imported = set()
    for m in _IMPORT_NAMES.finditer(text):
        for raw in m.group(1).split(","):
            imported.add(raw.strip().split(" as ")[0].strip())
    for name in _WRAPPERS:
        if _defines_getter(text, name) or (name in shared and name in imported):
            active.add(name)
    return active


def _looks_like_key(value):
    """值本身长得像不像 /home 的词条键(字符集 + 长度 + 含小写)。

    排掉的是键表里混放的非键值:archive-settings.ts 的 FIELD_META 同时存着 'YYYY-MM-DD'
    和 '_',它俩过得了字符集,过不了「最短 4 字符 + 含小写」。
    """
    return (
        bool(_KEY.match(value)) and len(value) >= _KEY_MIN_LEN and any(c.islower() for c in value)
    )


def _object_body(text, open_at):
    """从左花括号读到配对的右花括号;字符串与注释里的括号不计数。"""
    depth = 0
    i = open_at
    while i < len(text):
        char = text[i]
        if char == "/":
            after = skip_comment(text, i)
            if after != i:
                i = after
                continue
        if char in "'\"`":
            _, i = read_string(text, i)
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[open_at : i + 1], open_at
        i += 1
    return "", open_at


def table_keys(text, known):
    """常量键表里的键 → [(下标, 键)]。

    「这张表是不是键表」不靠命名猜 —— 全树 16 张里只有 4 张叫 *_I18N,按命名收只能收到
    四分之一;而反过来按命名收又会把 `const STORAGE_KEYS = {token:'mrpilot_token'}` 这类
    非 i18n 的表当词条报。判据改成对拍词典:一张具名对象字面量里至少两个像键的值、且至少
    一个真在 window.I18N 里,才当键表,表里其余对不上的值就是落空。
    实测这条在本树上是干净二分:66 张具名表里 50 张一个都对不上、16 张全对上,没有中间态。

    刻意不放宽到数组字面量与匿名对象:那些地方 i18n 键跟状态码/字段名/CSS 类混在一起
    (`[cond ? 'stw-done' : 'matched', ...]`),实测放宽后 87 个字面量里 47 个会报出假落空 ——
    交一个会误报的闸比不交更糟。这一块仍在射程外,谁要扩得先拿出新判据的实测数。
    """
    out = []
    for m in _TABLE_DECL.finditer(text):
        open_at = m.end() - 1
        if in_comment(text, open_at):
            continue
        body, base = _object_body(text, open_at)
        values = [(base + v.start(1), v.group(1)) for v in _TABLE_VALUE.finditer(body)]
        values = [(pos, val) for pos, val in values if _looks_like_key(val)]
        if len(values) < _TABLE_MIN_KEYS or not any(val in known for _, val in values):
            continue
        out.extend(values)
    return out


def key_references(root, known=None):
    """[(相对路径, 行号, 键)] · 按文件、行号排。

    known(词典键集合)只给常量键表那一路用 —— 它得先对拍词典才能判「这张表是不是键表」。
    """
    docs = documents(root)
    known = defined_keys(root) if known is None else known
    shared = exported_getters(docs)
    refs = []
    for rel, text in docs:
        names = _active_getters(text, shared)
        # 空集合拼进 (?:%s) 会变成"匹配任何左括号",把 ('GET') 这种普通字面量当键报出来。
        if names:
            head = (
                _GLOBAL_HEAD
                if names == {_GLOBAL_GETTER}
                else re.compile(_HEAD_TPL % "|".join(sorted(names)))
            )
            for m in head.finditer(text):
                if in_comment(text, m.start()):
                    continue
                for pos, key in call_keys(text, m.end(), _KEY):
                    refs.append((rel, line_of(text, pos), key))
        for m in _ATTR.finditer(text):
            key = m.group(1) if m.group(1) is not None else m.group(2)
            # 拼出来的属性值(选择器 '[data-i18n="' + from + '"]')过不了键的字符集,自动出局。
            if _KEY.match(key) and not in_comment(text, m.start()):
                refs.append((rel, line_of(text, m.start()), key))
        for m in _I18N_INDEX.finditer(text):
            if not in_comment(text, m.start()):
                refs.append((rel, line_of(text, m.start()), m.group(1) or m.group(2)))
        for pos, key in table_keys(text, known):
            refs.append((rel, line_of(text, pos), key))
    return sorted(set(refs))


def dangling(root):
    known = defined_keys(root)
    return [r for r in key_references(root, known) if r[2] not in known]


def load_baseline(path):
    if not path.is_file():
        return set()
    pairs = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rel, _, key = line.partition("\t")
        if key:
            pairs.add((rel, key))
    return pairs


_BASELINE_HEAD = """\
# /home 词典引用闸的存量基线(scripts/check_home_i18n_refs.py)
#
# 每行 = 一处"引用了 window.I18N 里没有的键"的存量债,格式 `相对路径<TAB>键`。
# data-i18n 落空的症状:applyLang 的 `if (I18N[lang][key])` 守卫不成立 → 元素被跳过 →
# 模板里写死的中文原地不动,泰语用户看中文且没有任何报错。
#
# ⚠️ 本闸现在是 0 容忍,正常情况下这个文件不该存在(建闸时唯一那处存量已还清)。
# 它躺在树上就意味着有人拿 --update-baseline 免了一笔债 —— 那笔债得在 PR 里写明理由,
# 并同步改掉 tests/unit/test_home_i18n_refs_gate.py 的 0 容忍断言,否则单测先红。
#
# 只许降不许升:新增一处闸就红。修好了跑
#   python scripts/check_home_i18n_refs.py --update-baseline
# 收紧本文件;收到 0 处时把文件删掉,别留个空壳。
"""


def write_baseline(path, pairs):
    body = "".join(f"{rel}\t{key}\n" for rel, key in sorted(pairs))
    # newline="" 关掉 Windows 的 \n → \r\n 翻译:基线要进 git,跨机器重跑 --update-baseline
    # 不该只因为行尾就出一整屏 diff(本仓的 CRLF 坑)。
    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(_BASELINE_HEAD + body)


def main(argv=None):
    ap = argparse.ArgumentParser(description="/home 词典引用闸(取词的字面量键必须有定义)")
    ap.add_argument("--root", default=str(ROOT), help="仓库根(测试用临时树时改)")
    ap.add_argument("--baseline", default=None, help="存量基线文件")
    ap.add_argument("--update-baseline", action="store_true", help="把当前落空写回基线(收紧)")
    args = ap.parse_args(argv)

    root = Path(args.root)
    baseline_path = Path(args.baseline) if args.baseline else BASELINE

    known = defined_keys(root)
    refs = key_references(root, known)
    live = {(rel, key) for rel, _, key in refs if key not in known}
    base = load_baseline(baseline_path)

    if args.update_baseline:
        write_baseline(baseline_path, live)
        print(f"基线已更新: {baseline_path} · {len(live)} 处存量")
        return 0

    added = sorted(r for r in refs if r[2] not in known and (r[0], r[2]) not in base)
    fixed = sorted(base - live)

    print("=" * 70)
    print("/home 词典引用闸(t()/_t()/kbT()/data-i18n 的字面量键 → 必须在 window.I18N 里)")
    print("=" * 70)
    if added:
        for rel, line, key in added:
            print(f"  [X] {rel}:{line} 引用了 window.I18N 里没有的键 `{key}`")
        print("\n      落空的后果:t() 把 key 原样返回印上屏;data-i18n 则整个跳过,")
        print("      模板里写死的那句中文原地不动 —— 泰语界面永远不翻译,还不报错。")
        print(f"\n结果: FAIL - {len(added)} 处新增引用落空(基线 {len(base)} 处存量已免罪)")
        return 1
    print(f"结果: PASS - {len(refs)} 处字面量取词,除基线 {len(base)} 处存量外条条查得到定义")
    if fixed:
        print(f"提示: 基线里有 {len(fixed)} 处已经修好,跑 --update-baseline 收紧:")
        for rel, key in fixed:
            print(f"  · {rel}\t{key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
