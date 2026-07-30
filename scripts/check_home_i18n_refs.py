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

已知照不到的一块(说清楚,别让人以为查过了):常量键表 —— `const _DUP_FIELD_I18N:
Record<string, string> = { doc_date: 'erp-dup-field-date', ... }` 这种把键名存进表、再
`t(表[变量] || '兜底键')` 取出来的写法。兜底键那半截本闸看得见(2026-07-31 就是这么抓到
erp-log-card.ts 漏补 erp-dup-field-other 的),表里那 56 个键看不见。没顺手扩进来的理由是
判据不干净:光靠命名(*_I18N / *_KEYS)会把 `const STORAGE_KEYS = {token:'mrpilot_token'}`
这类非 i18n 的键表也当词条报,而误报会让人把闸静音,等于没有。要扩就得先有个准判据。

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

存量基线:2026-07-31 建闸时全树 3353 处引用里只有 1 处落空,记在
scripts/home_i18n_refs_baseline.txt 里免罪 —— 补它要写 4 语文案,属用户可见改动,得配真
浏览器验收,不混进建闸这一笔。基线只许降不许升:新增一处即红,修好了跑 --update-baseline 收紧。

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

from js_key_scan import call_keys, in_comment, line_of  # noqa: E402

# 报告是中文的,而 Windows 控制台默认码页(本机 cp874)编不了 —— 不接管 stdout 的话第一行
# print 就 UnicodeEncodeError 退 1,跟真 FAIL 同一个退出码,分不出是闸红还是环境崩。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "scripts" / "home_i18n_refs_baseline.txt"

# window.I18N 是两层:`    zh: {` 之下全是 `'key': '文案',`。⚠️ 别按缩进认键 —— 一行里挤
# 着两条词条的地方有的是(i18n-data.js:1073 就是 'help-modal-title' 和 'help-modal-tip'
# 同行),按行首认会漏掉后一条,于是闸把一个明明有定义的键报成落空。建闸时正是这么假红了
# 8 处。判据 = 前面是 { 或 , 或行首、后面紧跟冒号,charset 按真源(只有 - . _ 三种非字母)。
# tests 里有 node eval 交叉验证锁着这条正则:多认一个少认一个,那条测试先红。
_DEF = re.compile(
    r"(?:^|[{,])\s*(?:'([A-Za-z_$][\w.$-]*)'|\"([A-Za-z_$][\w.$-]*)\")\s*:",
    re.M,
)

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
    return {m.group(1) or m.group(2) for m in _DEF.finditer(text)}


def _defines_getter(text, name):
    """文件里有没有一个真取词的 `function name(`(转发 window.t 或直接读 I18N)。"""
    for m in re.finditer(r"(?:export\s+)?function\s+%s\s*\(" % re.escape(name), text):
        if any(f in text[m.end() : m.end() + _BODY_WINDOW] for f in _GETTER_BODY):
            return True
    return False


def exported_getters(files):
    """全树扫一遍:哪些名字是 `export function` 出去的取词桥(今天只有 kbT)。"""
    names = set()
    for path in files:
        text = path.read_text(encoding="utf-8")
        for name in _WRAPPERS:
            if re.search(r"export\s+function\s+%s\s*\(" % re.escape(name), text):
                if _defines_getter(text, name):
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


def key_references(root):
    """[(相对路径, 行号, 键)] · 按文件、行号排。"""
    files = source_files(root)
    shared = exported_getters(files)
    refs = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(root).as_posix()
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
    return sorted(set(refs))


def dangling(root):
    known = defined_keys(root)
    return [r for r in key_references(root) if r[2] not in known]


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
# auto-erp-subtab-connect-only:推送日志从集成页拆成独立 tab 后,「连接」按钮改指了这个新
# 键,词典没跟上(旧键 auto-erp-subtab-connect = "连接 & 推送日志" 还在,但文案已经不对了)。
# 补法是照旧键的四语砍掉后半截:zh 连接 / en Connections / th การเชื่อมต่อ / ja 接続。
# 是用户可见文案改动,要配真浏览器四语验收,不混进建闸这一笔。
#
# 只许降不许升:新增一处闸就红。修好了跑
#   python scripts/check_home_i18n_refs.py --update-baseline
# 收紧本文件(顺手把这行债从账上划掉)。
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

    refs = key_references(root)
    known = defined_keys(root)
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
