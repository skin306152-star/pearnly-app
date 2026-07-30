# -*- coding: utf-8 -*-
"""查重闸「同钥匙内容不同」的跨仓库接缝:小助手一个字节都没写,会计得看懂差在哪。

场景是万能口的主场景:会计核完复核表把改过的数字塞回来说「推这批」。票号没动,金额动了。
小助手的幂等钥匙只有 REFNUM+SUPCOD+RECTYP,金额不在钥匙里 —— 于是它判为重复,回
DUPLICATE_CONTENT_DIFFERS,并把「账上是多少 / 你这份是多少」逐字段放进回执的 meta.duplicate。

云端到 2026-07-31 为止一个字都不认这个码,后果与 PRIOR_DOC 当年一模一样(见
test_prior_doc_seam):掉进 other → 卡上原样显示小助手那句**写死中文**。而这句比上一条更坏,
它末尾写着「确认要再落一张就带 duplicate_confirmed=true 重推」—— 产品里没有任何地方能带这个
参数,泰国会计既读不懂也照做不了。

故这里从「小助手 ack 上来的真实形状」压到前端要读的键。形状变了当场红。
"""

import json
import os
import re
import unittest
from pathlib import Path

from services.erp.push_exception_classify import (
    DUPLICATE_DIFFERS_CODE,
    classify_push_exception,
    derive_duplicate_fix,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DOCNUM = "HP690715-001"
# 小助手 queue_client.ack_failure 的真实格式:f"[{error_code}] {error}",正文即
# duplicate_gate.differs_message 那句写死中文。云端只准拿它认码,不准拿它当数据。
ACK_ERROR = (
    f"[{DUPLICATE_DIFFERS_CODE}] 这张票之前推过,ERP 里是 {DOCNUM}(税前金额 1,070.00 → "
    f"2,140.00)· 本次一个字节都没写 · 确认要再落一张就带 duplicate_confirmed=true 重推;"
    f"想改原单请在 Express 里改 {DOCNUM}"
)
# agent_store._build_response_body 落库的形状:meta.duplicate = duplicate_gate.differs_meta。
RESPONSE_BODY = {
    "ok": False,
    "express_docnum": None,
    "meta": {
        "stage": "needs_review",
        "companion_version": "1.1.58",
        "written": False,
        "duplicate": {
            "reason": "content_differs",
            "docnum": DOCNUM,
            "confirm_param": "duplicate_confirmed",
            "fields": [
                {
                    "field": "base_amount",
                    "label": "税前金额",
                    "in_erp": "1,070.00",
                    "incoming": "2,140.00",
                }
            ],
        },
    },
}


def _companion_dir() -> Path:
    return Path(
        os.environ.get("PEARNLY_COMPANION_DIR") or PROJECT_ROOT.parent / "pearnly-companion"
    )


class DuplicateDiffersSeam(unittest.TestCase):
    def test_code_matches_the_bridge_constant(self):
        """两仓库共用这一个串。桥改了名而这里没跟,分类就静默掉回 other。"""
        self.assertEqual(DUPLICATE_DIFFERS_CODE, "DUPLICATE_CONTENT_DIFFERS")

    def test_code_is_verbatim_the_one_the_writer_emits(self):
        """有桥仓的机器上逐字比一次 —— 上一条只锁住我们自己写的字面量,锁不住对面。"""
        src = _companion_dir() / "bridge" / "writepath" / "duplicate_gate.py"
        if not src.exists():
            self.skipTest(f"桥仓不在 {_companion_dir()}")
        text = src.read_text(encoding="utf-8")
        hit = re.search(r'ERR_DUPLICATE_DIFFERS\s*=\s*"([^"]+)"', text)
        self.assertIsNotNone(hit, "桥端 ERR_DUPLICATE_DIFFERS 的字面量找不到了")
        self.assertEqual(hit.group(1), DUPLICATE_DIFFERS_CODE)

    def test_classified_into_its_own_bucket_not_other(self):
        """掉进 other = 与「未知错误」混为一谈,拿不到差异行也拿不到指引。"""
        self.assertEqual(classify_push_exception(ACK_ERROR), "duplicate_differs")

    def test_diff_comes_from_the_receipt_not_the_message(self):
        """差异取自回执的结构化 meta,不从那句中文里正则抠数字。"""
        fix = derive_duplicate_fix(ACK_ERROR, RESPONSE_BODY)
        self.assertEqual(fix["docnum"], DOCNUM)
        self.assertEqual(
            fix["fields"],
            [{"field": "base_amount", "in_erp": "1,070.00", "incoming": "2,140.00"}],
        )

    def test_chinese_label_from_the_writer_is_dropped(self):
        """小助手回执里的 label 是写死中文,透传上屏 = 泰国会计读一行看不懂的字。"""
        fix = derive_duplicate_fix(ACK_ERROR, RESPONSE_BODY)
        self.assertNotIn("label", fix["fields"][0])

    def test_confirm_param_is_not_relayed(self):
        """产品里没有「我知道,还是推」这个按钮。把参数名透传下去,下游迟早拼出一句
        会计照做不了的指令 —— 这正是本条接缝要挡掉的那句原话。"""
        fix = derive_duplicate_fix(ACK_ERROR, RESPONSE_BODY)
        self.assertNotIn("confirm_param", fix)
        self.assertNotIn("duplicate_confirmed", json.dumps(fix, ensure_ascii=False))

    def test_diff_survives_when_receipt_is_a_json_string(self):
        """response_body 落库是文本列,取回来是串 —— _coerce_body 该兜住。"""
        fix = derive_duplicate_fix(ACK_ERROR, json.dumps(RESPONSE_BODY, ensure_ascii=False))
        self.assertEqual(fix["fields"][0]["incoming"], "2,140.00")

    def test_missing_receipt_still_yields_the_docnum_shape(self):
        """老回执(没有 meta.duplicate)不该让整张卡崩成 None:字段空着,句子照说。"""
        fix = derive_duplicate_fix(ACK_ERROR, None)
        self.assertEqual(fix, {"docnum": "", "fields": []})

    def test_other_failures_get_no_duplicate_fix(self):
        """阴性对照:别的失败码不能凭空长出这块差异。"""
        self.assertIsNone(derive_duplicate_fix("[CDX_REINDEX_FAILED] x", RESPONSE_BODY))
        self.assertIsNone(derive_duplicate_fix("EXPRESS_MANUAL: no_ar_account", RESPONSE_BODY))
        self.assertIsNone(derive_duplicate_fix("[PRIOR_DOC_STILL_IN_ERP] y", RESPONSE_BODY))

    def test_frontend_reads_the_keys_we_produce(self):
        """卡片源码读的键名必须就是本模块产出的那个 —— 两头各测各的就是这一族病根。"""
        card = (PROJECT_ROOT / "src" / "home" / "erp-log-card.ts").read_text(encoding="utf-8")
        self.assertIn("DUPLICATE_CONTENT_DIFFERS: 'erp-reason-duplicate-differs'", card)
        self.assertIn("log.duplicate_fix && log.duplicate_fix.fields", card)
        self.assertIn("log.duplicate_fix && log.duplicate_fix.docnum", card)

    def test_every_diff_field_name_has_a_label_key(self):
        """桥端 HEAD_FIELDS 会比的四个字段,前端都得翻得出名字,否则上屏就是机器名。"""
        card = (PROJECT_ROOT / "src" / "home" / "erp-log-card.ts").read_text(encoding="utf-8")
        for name in ("base_amount", "vat_amount", "total_amount", "doc_date"):
            self.assertRegex(card, rf"{name}:\s*'erp-dup-field-")

    def test_all_four_languages_carry_both_placeholders(self):
        """四语齐全,每句都留 {doc} 与 {diff} —— 少一个就等于不告诉她差在哪 / 该动哪张。"""
        raw = (PROJECT_ROOT / "static" / "i18n-data.js").read_text(encoding="utf-8")
        hits = re.findall(r"'erp-reason-duplicate-differs':\s*'([^']+)'", raw)
        self.assertEqual(len(hits), 4, f"四语不齐:{hits}")
        for text in hits:
            self.assertIn("{doc}", text)
            self.assertIn("{diff}", text)
            self.assertIn("Express", text)

    def test_copy_never_tells_the_accountant_to_pass_a_parameter(self):
        """这一族文案的红线:界面上做不到的事一个字都不许说。小助手那句原话正是反例。"""
        raw = (PROJECT_ROOT / "static" / "i18n-data.js").read_text(encoding="utf-8")
        for text in re.findall(r"'erp-reason-duplicate-differs':\s*'([^']+)'", raw):
            self.assertNotIn("duplicate_confirmed", text)


if __name__ == "__main__":
    unittest.main()
