#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_ai_fail_render.py

/ai 失败态出路守门(缺口①「点开当期工单失败页面零反应」/ 缺口②「上传失败只报通用错误」):

  1. ai-fail-render.js 的 (code, status) → 原因/出路判读:四类失败各自认得出,余额不足
     是唯一带「换个地方点」出路的那类,且落点是设置页计费区的真实深链。
  2. 失败卡 HTML 真把原因说出来(而不是只有一个重传按钮),余额不足那类真出「去充值」。
  3. ai-intake-manifest.js 失败批横幅:多批不同原因逐条列、同原因不重复列、count 照旧。
  4. ai-i18n-fail.js 分片 zh/th key 集合一致 + 每个 fail_ 词条都真被引用(主词典的四语
     一致性测试不装本分片,自己的闸自己带 · 同 ai-i18n-states.js 先例)。
  5. ai-router.js 的 #/settings?focus=billing 深链解析(出路点了要真落在计费区)。

同 test_ai_billing_render.py 的 node subprocess require 手法——真 node 跑源文件。
node 侧无 window.at → t() 回退原 key,HTML 断言直接认 key 字符串。
"""

from __future__ import annotations

import json
import re
import shutil
import unittest
from pathlib import Path

from tests.unit._node_harness import AI_DIR, BAHT, _run_node

FAIL = str(AI_DIR / "ai-fail-render.js")
STATE = str(AI_DIR / "ai-state.js")
API = str(AI_DIR / "ai-api.js")
MANIFEST = str(AI_DIR / "ai-intake-manifest.js")
ROUTER = str(AI_DIR / "ai-router.js")

# failureView 的兜底分支借 AI.api.mapApiErrorKey(不在本文件抄第二份码表),esc 借
# AI.state——先 require 两个依赖挂上 global.AI,再 require 被测文件(同 ai.html 加载顺序)。
PRELUDE = f"""
    global.window = global;
    require({json.dumps(STATE)});
    require({json.dumps(API)});
    const f = require({json.dumps(FAIL)});
    """

_LANGS = ("zh", "th", "en", "ja")


def _require(name: str) -> str:
    return f"require({json.dumps(str(AI_DIR / name))});\n"


# 带真词典 + 真 at() + 真 money() 的变体:402 那几个数要断言用户真读到的那句话和那个金额
# (key 对了金额还能是 "฿ 0.00" 这种假零),不是 key(同 test_ai_blocked_reasons.py 手法)。
REAL_PRELUDE = (
    """
    global.window = global;
    global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
    """
    + "".join(_require(f"ai-i18n-{lang}.js") + _require(f"ai-i18n-{lang}-2.js") for lang in _LANGS)
    + _require("ai-i18n-fail.js")
    + _require("ai-i18n.js")
    + _require("ai-state.js")
    + _require("ai-format.js")
    + _require("ai-api.js")
    + f"const f = require({json.dumps(FAIL)});\n"
)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class FailureViewTests(unittest.TestCase):
    def _view(self, code, status):
        return _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(
                f.failureView({json.dumps(code)}, {json.dumps(status)})
            ));
            """)

    def test_no_code_no_status_is_network_drop(self):
        # fetch TypeError / xhr onerror:请求根本没出去,两样都没有。
        v = self._view(None, 0)
        self.assertEqual(v["reasonKey"], "fail_network")
        self.assertIsNone(v["actionKey"])

    def test_401_says_session_expired(self):
        self.assertEqual(self._view("generic", 401)["reasonKey"], "fail_auth")

    def test_5xx_says_server_error_not_generic(self):
        self.assertEqual(self._view("generic", 500)["reasonKey"], "fail_server")

    def test_workorder_not_found_says_out_of_scope(self):
        # 越权/闸关/单已删后端一律收在这个码上,对用户是同一件事。
        self.assertEqual(self._view("workorder.not_found", 404)["reasonKey"], "fail_no_access")

    def test_insufficient_balance_code_gives_topup_way_out(self):
        v = self._view("insufficient_balance", 402)
        self.assertEqual(v["reasonKey"], "fail_credits")
        self.assertEqual(v["actionKey"], "fail_topup_btn")
        self.assertEqual(v["href"], "#/settings?focus=billing")

    def test_bare_402_without_code_still_gives_topup_way_out(self):
        self.assertEqual(self._view("generic", 402)["actionKey"], "fail_topup_btn")

    def _per_file(self, status, detail):
        return _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify(
                f.isPerFileReject({json.dumps(status)}, {json.dumps(detail)})
            ));
            """)

    def test_422_with_named_file_is_a_per_file_reject(self):
        # IN-0a 两段法:整批 422 该批零落盘,拿掉点名那件重传其余才安全。
        self.assertTrue(
            self._per_file(422, {"code": "workorder.intake.pdf_password_required", "filename": "a"})
        )

    def test_402_with_structured_detail_is_not_a_per_file_reject(self):
        # 只看 detail.code 分派的老写法会把计费闸的 402 当成"某一件坏料"逐个剥,
        # 于是整批被判拒收、真原因一句没说。
        self.assertFalse(self._per_file(402, {"code": "insufficient_balance"}))

    def test_bare_string_detail_is_not_a_per_file_reject(self):
        self.assertFalse(self._per_file(413, None))

    def test_known_error_code_reuses_existing_dictionary(self):
        # 已有 err_* 词条的码走 ai-api.js 既有映射,不在失败层另起一套文案。
        v = self._view("workorder.file_too_large", 413)
        self.assertEqual(v["reasonKey"], "err_workorder_file_too_large")
        self.assertIsNone(v["actionKey"])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class FailHtmlTests(unittest.TestCase):
    def _html(self, expr):
        return _run_node(f"""
            {PRELUDE}
            process.stdout.write(JSON.stringify({expr}));
            """)

    def test_reason_line_names_the_step_and_the_why(self):
        html = self._html("f.reasonHtml('fail_step_open_order', null, 0)")
        self.assertIn("fail_step_open_order", html)
        self.assertIn("fail_network", html)
        self.assertIn('role="alert"', html)

    def test_no_extra_button_when_retry_is_the_only_way_out(self):
        # 调用方自己已有重试入口(开单按钮回可点 / 失败批「重传」),这里不再摆第二个。
        self.assertEqual(self._html("f.actionHtml(null, 0)"), "")
        self.assertEqual(self._html("f.actionHtml('generic', 500)"), "")

    def test_topup_action_is_a_real_deep_link(self):
        html = self._html("f.actionHtml('insufficient_balance', 402)")
        self.assertIn('href="#/settings?focus=billing"', html)
        self.assertIn("fail_topup_btn", html)

    def test_note_html_pairs_reason_with_way_out(self):
        html = self._html("f.noteHtml('fail_step_open_order', 'insufficient_balance', 402)")
        self.assertIn("fail_credits", html)
        self.assertIn("needs-paths", html)

    def test_note_html_without_way_out_has_no_empty_action_row(self):
        html = self._html("f.noteHtml('fail_step_open_order', null, 0)")
        self.assertNotIn("needs-paths", html)

    def test_reason_key_override_replaces_the_computed_why(self):
        # 失败发生在「已经做成的一步之后」时(开单成功、刷列表 500),(code,status) 推出来的
        # 「服务器出错了」是误导:用户要知道的是单已经开出来了。
        html = self._html(
            "f.noteHtml('fail_step_reload_orders', 'generic', 500,"
            " {reasonKey: 'fail_created_but_stale'})"
        )
        self.assertIn("fail_step_reload_orders", html)
        self.assertIn("fail_created_but_stale", html)
        self.assertNotIn("fail_server", html)

    def test_reason_key_override_suppresses_the_computed_button(self):
        # 覆盖原因时出路写在文案里;再挂一个按 (code,status) 算出来的按钮会把人指错地方。
        html = self._html(
            "f.noteHtml('fail_step_reload_orders', 'insufficient_balance', 402,"
            " {reasonKey: 'fail_created_but_stale'})"
        )
        self.assertNotIn("needs-paths", html)
        self.assertNotIn("fail_topup_btn", html)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class CreditsFactsTests(unittest.TestCase):
    """402 的三个数上屏(handover §3.10):此前失败卡只说「OCR 余额不足」,后端明明把
    余额 / 这批要花多少 / 本月已识别几页都送到浏览器了,前端一个都没说。

    产地只有一处 —— services/workorder/steps/ocr_balance.batch_denial(+ shortfall「还差
    多少」)。另有六个端点同码返 402 但不带这些数,所以每一句都必须能单独消失。"""

    def _text(self, detail, file_count=0, lang="zh"):
        """渲染后用户真读到的那段话(剥标签,与浏览器 textContent 同口径)。"""
        html = _run_node(f"""
            {REAL_PRELUDE}
            global.atSetLang({json.dumps(lang)});
            process.stdout.write(JSON.stringify(
                f.creditsFactsHtml({json.dumps(detail)}, {json.dumps(file_count)})
            ));
            """)
        return {"html": html, "text": re.sub(r"<[^>]+>", "", html)}

    # 真实体:ocr_balance.batch_denial 的五键(余额 0 / 一件一页 ฿1.50 / 本月已识别 12 页)。
    _FULL = {
        "code": "insufficient_balance",
        "balance": 0.0,
        "estimated_cost": 1.5,
        "pages_used_this_month": 12,
        "shortfall": 1.5,
    }

    def test_all_three_numbers_reach_the_card(self):
        out = self._text(self._FULL, file_count=1)
        self.assertIn("1 个文件", out["text"])
        self.assertIn(f"{BAHT}1.50", out["text"])  # 这批要花多少 / 还差多少
        self.assertIn(f"{BAHT}0.00", out["text"])  # 账上还有多少(真零,不是缺数)
        self.assertIn("至少充", out["text"])
        self.assertIn("12 页", out["text"])
        self.assertNotIn("{", out["text"])  # 占位符没漏上屏

    def test_thai_card_says_the_same_numbers(self):
        out = self._text(self._FULL, file_count=1, lang="th")
        self.assertIn("ยอดคงเหลือ", out["text"])
        self.assertIn(f"{BAHT}1.50", out["text"])
        self.assertIn("เดือนนี้อ่านไปแล้ว 12 หน้า", out["text"])
        self.assertNotIn("balance", out["text"])

    def test_unknown_file_count_drops_only_the_count(self):
        out = self._text(self._FULL)
        self.assertIn(f"{BAHT}1.50", out["text"])
        self.assertNotIn("个文件", out["text"])

    def test_body_without_shortfall_degrades_instead_of_inventing_one(self):
        # 另外六个 402 端点(recon / vat_excel / knowledge …)不带 shortfall。
        body = dict(self._FULL)
        del body["shortfall"]
        out = self._text(body, file_count=1)
        self.assertIn(f"{BAHT}1.50", out["text"])
        self.assertNotIn("至少充", out["text"])
        for ghost in ("undefined", "NaN", "—", "{"):
            self.assertNotIn(ghost, out["text"], f"缺 shortfall 时渲染出了 {ghost}")

    def test_null_shortfall_is_the_same_as_absent(self):
        # 余额够却仍被拒时后端给 null(batch_denial),不是 0。
        out = self._text(dict(self._FULL, shortfall=None), file_count=1)
        self.assertNotIn("至少充", out["text"])
        self.assertNotIn("undefined", out["text"])

    def test_zero_pages_this_month_says_nothing(self):
        # 「这个月已经识别了 0 页」是零信息,占一行还让人以为出了什么事。
        out = self._text(dict(self._FULL, pages_used_this_month=0), file_count=1)
        self.assertNotIn("这个月", out["text"])
        self.assertIn("至少充", out["text"])

    def test_missing_balance_drops_the_sentence_rather_than_printing_a_fake_zero(self):
        # money(null) 吐 ฿ 0.00(Number(null)===0):把「不知道余额」说成「余额是零」。
        out = self._text(dict(self._FULL, balance=None), file_count=1)
        self.assertNotIn("账上还有", out["text"])
        self.assertNotIn(f"{BAHT}0.00", out["text"])
        self.assertIn("至少充", out["text"])  # 还差多少照说

    def test_string_numbers_are_not_trusted(self):
        # 后端给的是 JSON number;是串就说明这不是那条契约,别硬渲染。
        out = self._text({"balance": "0", "estimated_cost": "1.5"}, file_count=1)
        self.assertEqual(out["html"], "")

    def test_no_numbers_at_all_renders_nothing(self):
        self.assertEqual(self._text({"code": "insufficient_balance"}, file_count=2)["html"], "")
        self.assertEqual(self._text(None)["html"], "")

    def _note(self, code, status, opts):
        return _run_node(f"""
            {REAL_PRELUDE}
            process.stdout.write(JSON.stringify(
                f.noteHtml('fail_step_upload', {json.dumps(code)}, {json.dumps(status)},
                    {json.dumps(opts)})
            ));
            """)

    def test_note_html_carries_the_numbers_and_the_way_out_together(self):
        html = self._note("insufficient_balance", 402, {"detail": self._FULL, "fileCount": 1})
        self.assertIn("余额不足", html)
        self.assertIn(f"{BAHT}1.50", html)
        self.assertIn('href="#/settings?focus=billing"', html)

    def test_non_credit_failures_never_show_money(self):
        html = self._note("generic", 500, {"detail": self._FULL, "fileCount": 1})
        self.assertNotIn("฿", html)

    def test_reason_key_override_suppresses_the_numbers_too(self):
        # 覆盖场景 = 前一步其实已经成了,这时报「这批要花多少」同样是误导。
        html = self._note(
            "insufficient_balance",
            402,
            {"reasonKey": "fail_created_but_stale", "detail": self._FULL, "fileCount": 1},
        )
        self.assertNotIn("฿", html)
        self.assertNotIn("needs-paths", html)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class FailedBatchBannerTests(unittest.TestCase):
    """收料失败批横幅:此前只有「N 个文件上传失败 + 重传」,原因被整个吞掉。"""

    def _banner(self, batches):
        return _run_node(f"""
            {PRELUDE}
            global.at = (k, v) => (v ? k + ' ' + Object.values(v).join(' ') : k);
            const m = require({json.dumps(MANIFEST)});
            process.stdout.write(JSON.stringify(
                global.AI.intakeManifest.failedBatchesHtml({json.dumps(batches)})
            ));
            """)

    def test_empty_when_nothing_failed(self):
        self.assertEqual(self._banner([]), "")

    def test_states_reason_and_keeps_the_count(self):
        html = self._banner([{"files": [{"name": "a.pdf"}, {"name": "b.pdf"}], "status": 500}])
        self.assertIn("fail_step_upload", html)
        self.assertIn("fail_server", html)
        self.assertIn("intake_failed_batch_n 2", html)
        self.assertIn("ik-retry-failed", html)

    def test_credits_failure_offers_topup_next_to_retry(self):
        html = self._banner([{"files": [{"name": "a.pdf"}], "code": "insufficient_balance"}])
        self.assertIn("fail_credits", html)
        self.assertIn('href="#/settings?focus=billing"', html)

    def test_distinct_reasons_each_get_a_line(self):
        html = self._banner(
            [
                {"files": [{"name": "a.pdf"}], "status": 500},
                {"files": [{"name": "b.pdf"}], "status": 401},
            ]
        )
        self.assertIn("fail_server", html)
        self.assertIn("fail_auth", html)
        self.assertIn("intake_failed_batch_n 2", html)

    def test_same_reason_twice_is_not_repeated(self):
        html = self._banner(
            [
                {"files": [{"name": "a.pdf"}], "status": 500},
                {"files": [{"name": "b.pdf"}], "status": 500},
            ]
        )
        self.assertEqual(html.count("fail_server"), 1)
        self.assertIn("intake_failed_batch_n 2", html)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class UploadDetailReachesTheCardTests(unittest.TestCase):
    """整条链跑真模块:api 抛的 402 → 队列事件 → session.failedBatches → 卡上的字。

    渲染层单独测绿是不够的 —— 这三个数在浏览器里躺了一个月没上屏,断点就在队列层把
    err.detail 丢了(渲染函数写得再对也没数可渲染,见 memory:verify-target-must-be-real-content)。
    这里连 ai-intake-queue.js / ai-intake-render.js / ai-intake-manifest.js 一起真 require,
    只有 api 是替身。"""

    _BODY = {
        "code": "insufficient_balance",
        "balance": 0.0,
        "estimated_cost": 1.5,
        "pages_used_this_month": 12,
        "shortfall": 1.5,
    }

    def _upload_failing_with(self, err_props):
        """跑一趟真上传(api 直接拒),返回落进会话的失败批 + 横幅 HTML。"""
        return _run_node(f"""
            {REAL_PRELUDE}
            {_require("ai-intake-render.js")}
            {_require("ai-intake-manifest.js")}
            {_require("ai-intake-queue.js")}
            const session = {{
                api: {{ addMaterials: function () {{
                    return Promise.reject(Object.assign(new Error('x'), {json.dumps(err_props)}));
                }} }},
                orderId: 'wo-1',
                manifest: {{ accepted: 0, rejected: [], zipExpanded: 0 }},
                failedBatches: [],
            }};
            const actions = global.AI.intakeQueue.create(() => session, () => {{}});
            actions.upload([{{ name: 'a.pdf', size: 10 }}]).then(function () {{
                process.stdout.write(JSON.stringify({{
                    batches: session.failedBatches,
                    html: global.AI.intakeManifest.failedBatchesHtml(session.failedBatches),
                }}));
            }});
            """)

    def test_the_402_body_survives_the_queue_and_lands_on_the_card(self):
        out = self._upload_failing_with(
            {"code": "insufficient_balance", "status": 402, "detail": self._BODY}
        )
        self.assertEqual(out["batches"][0]["detail"], self._BODY)  # 队列没把 detail 丢掉
        html = out["html"]
        self.assertIn("OCR 余额不足", html)
        self.assertIn(f"{BAHT}1.50", html)  # 这批要花多少 / 还差多少
        self.assertIn("1 个文件", html)
        self.assertIn("12 页", html)
        self.assertIn('href="#/settings?focus=billing"', html)

    def test_a_402_with_no_body_still_renders_a_clean_card(self):
        # 别的端点的 402(recon / vat_excel / knowledge)不带这些数:少说几句,不出空壳。
        out = self._upload_failing_with({"code": "insufficient_balance", "status": 402})
        html = out["html"]
        self.assertIsNone(out["batches"][0]["detail"])
        self.assertIn("OCR 余额不足", html)
        self.assertIn('href="#/settings?focus=billing"', html)
        for ghost in ("฿", "undefined", "NaN", "{"):
            self.assertNotIn(ghost, html, f"没有数的 402 卡上出现了 {ghost}")

    def test_a_non_money_failure_never_grows_a_money_line(self):
        out = self._upload_failing_with({"code": "generic", "status": 500})
        self.assertNotIn("฿", out["html"])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class FailI18nShardTests(unittest.TestCase):
    """zh/th key 一致 + 被引用 key 必须真实存在(分片不在主四语一致性测试的装载清单里,
    自己的闸自己带 · 同 ai-i18n-states.js 先例)。"""

    def _shard_keys(self):
        return _run_node(f"""
            global.window = global;
            global.__AI_I18N_ZH__ = {{}};
            global.__AI_I18N_TH__ = {{}};
            require({json.dumps(str(AI_DIR / "ai-i18n-fail.js"))});
            process.stdout.write(JSON.stringify({{
                zh: Object.keys(global.__AI_I18N_ZH__).sort(),
                th: Object.keys(global.__AI_I18N_TH__).sort(),
            }}));
            """)

    def test_zh_and_th_key_sets_identical(self):
        keys = self._shard_keys()
        self.assertTrue(keys["zh"], "分片 zh 词条为空")
        self.assertEqual(keys["zh"], keys["th"], "th 词典 key 集合与 zh 不一致")

    def test_every_fail_key_is_referenced_and_every_reference_exists(self):
        zh = set(self._shard_keys()["zh"])
        referenced = set()
        for name in ("ai-fail-render.js", "ai-client.js", "ai-intake-manifest.js"):
            text = (AI_DIR / name).read_text(encoding="utf-8")
            referenced |= set(re.findall(r"\bfail_[a-z0-9_]+", text))
        missing = sorted(k for k in referenced if k not in zh)
        self.assertEqual(missing, [], f"代码引用了词典里不存在的 key: {missing}")
        unused = sorted(k for k in zh if k not in referenced)
        self.assertEqual(unused, [], f"词典里有没人引用的死 key: {unused}")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class SettingsFocusDeepLinkTests(unittest.TestCase):
    def _parse(self, hash_str):
        return _run_node(f"""
            const r = require({json.dumps(ROUTER)});
            process.stdout.write(JSON.stringify(r.parseHash({json.dumps(hash_str)})));
            """)

    def test_focus_billing_survives_the_hop(self):
        self.assertEqual(
            self._parse("#/settings?focus=billing"),
            {
                "name": "settings",
                "focus": "billing",
            },
        )

    def test_plain_settings_has_no_focus(self):
        self.assertEqual(self._parse("#/settings"), {"name": "settings", "focus": None})


class SettingsFocusWiringTests(unittest.TestCase):
    """路由解析出 focus 还不够——ai.js 得把它递给 ai-settings.js。深链断在中间一节是老坑
    (见 memory:verify-target-must-be-real-content)。

    注意本类只是接线存在性的 grep 闸,「真滚到了」它验不了(源码里字符串在就绿)。滚没滚、
    滚到哪里由 tests/e2e/_fail_ways_out_local.spec.js 在 390×844 真浏览器里断言
    scrollY>0 + 充值按钮整颗在视口内 —— 别再拿这里的绿当落点验收。"""

    def test_router_focus_reaches_settings_mount(self):
        self.assertIn("focus: route.focus", (AI_DIR / "ai.js").read_text(encoding="utf-8"))

    def test_settings_retries_the_scroll_until_content_lands(self):
        # 计费区挂载那一刻还是骨架、页面撑不出滚动条 → scrollIntoView 被 clamp 成 no-op。
        # 单滚一次 = 手机上永远停在页顶(D1),必须有补滚。
        text = (AI_DIR / "ai-settings.js").read_text(encoding="utf-8")
        self.assertIn("applyFocus", text)
        self.assertIn("stBillingWrap", text)
        self.assertIn("scrollIntoView", text)
        self.assertIn("FOCUS_RETRY_MS", text)


class TopupBranchWiringTests(unittest.TestCase):
    """「去充值」这条出路不许再退回休眠:后端真有一处会返 402 + insufficient_balance,
    前端的说明也得指得到它。前身是 DormantTopupBranchTests(断言收料【没有】计费闸),
    2026-07-27 收料上闸后翻面——两边一起改,别让「验过了」和「用得上」再错位
    (memory:verify-target-must-be-real-content)。真扣费/真停机的契约在
    tests/unit/test_workorder_billing.py。"""

    def test_materials_endpoint_really_raises_402_insufficient_balance(self):
        root = Path(AI_DIR).parents[1]
        text = (root / "routes" / "workorder_routes.py").read_text(encoding="utf-8")
        self.assertIn("ocr_balance.batch_denial", text)
        self.assertIn("HTTPException(402, detail=denial)", text)
        gate = (root / "services" / "workorder" / "steps" / "ocr_balance.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('STUCK_REASON = "insufficient_balance"', gate)

    def test_fail_render_points_at_the_real_402_source(self):
        text = (AI_DIR / "ai-fail-render.js").read_text(encoding="utf-8")
        self.assertNotIn("休眠分支", text)
        self.assertIn("ocr_balance.batch_denial", text)


class BundleWiringTests(unittest.TestCase):
    """新模块不进 bundle / 新词典不进 ai.html = 上线即死代码。"""

    def test_fail_render_is_in_the_ai_bundle(self):
        root = Path(AI_DIR).parents[1]
        text = (root / "scripts" / "build-home-js.mjs").read_text(encoding="utf-8")
        self.assertIn("'ai/ai-fail-render.js'", text)

    def test_fail_dictionary_is_loaded_by_ai_html(self):
        self.assertIn("ai-i18n-fail.js", (AI_DIR / "ai.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
