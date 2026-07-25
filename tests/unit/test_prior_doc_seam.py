# -*- coding: utf-8 -*-
"""防重单闸的跨仓库接缝:小助手拒了之后,会计得看懂并知道要去删哪一号。

这条闸唯一的存在理由是「会计改了票号回导重推」—— 号一改,小助手既有的
YOUREF+客户码 幂等就认不出,旧单还躺在 Express 里,新单再建一张 = 同一笔记两遍账。

而 2026-07-25 查下来,拒绝之后的路是断的:
  · 云端分类器不认这个码 → 掉进 other,没有 chip、没有专属指引
  · 前端 _AGENT_REASON_I18N 没这个码 → 翻译返空 → 原样显示小助手那句**写死中文**
    (泰国会计看不懂),还带着方括号里的英文码
  · 要删哪一号只在那句中文里,没有结构化字段可取

故这里从「小助手 ack 上来的真实 error_msg 形状」出发,一路压到前端要读的键。
形状变了(小助手改码 / ack 前缀格式变 / 载荷键改名)这里立刻红。
"""

import unittest

from services.erp.push_exception_classify import (
    PRIOR_DOC_CODE,
    classify_push_exception,
    derive_prior_doc_fix,
)

PRIOR = "IV69/00473"
# 小助手 queue_client.ack_failure 的真实格式:f"[{error_code}] {error}"。
# 那句中文原样抄自 companion dbf_sales —— 正因为它是写死中文,云端不能拿它当数据来源。
ACK_ERROR = f"[{PRIOR_DOC_CODE}] ERP 里上一版单据 {PRIOR} 还在 · 请先在 Express 删除它再重新导入"
REQUEST_BODY = {
    "adapter": "express",
    "payload": {
        "direction": "sales",
        "ref_no": "IV69/00474",
        "prior_docnum": PRIOR,
    },
}


class PriorDocSeam(unittest.TestCase):
    def test_code_matches_the_companion_constant(self):
        """两仓库共用这一个串。小助手改了名而这里没跟,闸就静默失效。"""
        self.assertEqual(PRIOR_DOC_CODE, "PRIOR_DOC_STILL_IN_ERP")

    def test_classified_into_its_own_bucket_not_other(self):
        """掉进 other = 没有 chip、没有专属指引,与「未知错误」混为一谈。"""
        self.assertEqual(classify_push_exception(ACK_ERROR), "prior_doc_exists")

    def test_docnum_comes_from_the_payload_not_the_message(self):
        """要删哪一号取自我们自己发下去的 prior_docnum(权威),不从中文串里正则抠。"""
        fix = derive_prior_doc_fix(ACK_ERROR, REQUEST_BODY)
        self.assertEqual(fix, {"docnum": PRIOR})

    def test_docnum_survives_when_payload_is_a_json_string(self):
        """request_body 落库是 jsonb,取回来有时是串 —— _coerce_body 该兜住。"""
        import json

        fix = derive_prior_doc_fix(ACK_ERROR, json.dumps(REQUEST_BODY))
        self.assertEqual(fix, {"docnum": PRIOR})

    def test_other_failures_get_no_prior_doc_fix(self):
        """阴性对照:别的失败码不能凭空长出这张卡。"""
        self.assertIsNone(derive_prior_doc_fix("[CDX_REINDEX_FAILED] x", REQUEST_BODY))
        self.assertIsNone(derive_prior_doc_fix("EXPRESS_MANUAL: no_ar_account", REQUEST_BODY))

    def test_frontend_reads_the_key_we_produce(self):
        """卡片源码里读的键名,必须就是本模块产出的那个 —— 两头各测各的就是今天这批病根。"""
        from pathlib import Path

        card = Path("src/home/erp-log-card.ts").read_text(encoding="utf-8")
        self.assertIn("PRIOR_DOC_STILL_IN_ERP: 'erp-reason-prior-doc'", card)
        self.assertIn("log.prior_doc_fix && log.prior_doc_fix.docnum", card)

    def test_all_four_languages_carry_the_docnum_placeholder(self):
        """四语齐全,且每一句都留了 {doc} —— 少了占位符就等于不告诉会计删哪张。"""
        import re
        from pathlib import Path

        raw = Path("static/i18n-data.js").read_text(encoding="utf-8")
        hits = re.findall(r"'erp-reason-prior-doc':\s*'([^']+)'", raw)
        self.assertEqual(len(hits), 4, f"四语不齐:{hits}")
        for text in hits:
            self.assertIn("{doc}", text)
            self.assertIn("Express", text)


if __name__ == "__main__":
    unittest.main()
