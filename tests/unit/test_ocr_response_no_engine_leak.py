"""防回潮:/api/ocr/recognize 出口净化器不得泄漏内部实现标识。

竞品在 F12 看响应——引擎名(Gemini/Vision/Typhoon)、流水线层名、置信度门控、
触发原因一律不出网。本测试锁死 strip_internal_fields(主 + 缓存两条出口都过它):
递归后响应里不含引擎/品牌/层 key,也不含任何 _ 前缀 debug key。
"""

import unittest

from services.ocr.recognize.sanitize import strip_internal_fields

# 内部标识子串黑名单(出现在 key 名里即视为泄漏)。
_LEAK_SUBSTRINGS = ("engine", "typhoon", "layer", "gemini", "vision", "flash", "token")


def _iter_keys(obj):
    """递归吐出所有 dict key(查 pages/invoices 嵌套结构)。"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _iter_keys(v)
    elif isinstance(obj, list):
        for x in obj:
            yield from _iter_keys(x)


# 主出口 + 缓存出口的代表性响应(含所有曾泄漏的字段)。
def _sample_main_response():
    return {
        "filename": "bill.jpg",
        "confidence": 0.9,
        "engine": "gemini",
        "engine_chain": ["pipeline_v1"],
        "fallback_used": False,
        "typhoon_enhanced": False,
        "typhoon_pages": [],
        "pages": [
            {
                "page_number": 1,
                "fields": {"total": "100"},
                "input_tokens": 1234,
                "output_tokens": 567,
                "_layer_chain": ["text", "vision", "flash"],
                "_trigger_reasons": ["low_conf"],
                "_confidence_band": "mid",
                "_final_confidence": 0.8,
                "_document_type": "receipt",
                "_validation_warnings": [],
            }
        ],
        "invoices": [{"fields": {"total": "100"}, "_layer_chain": ["x"]}],
    }


def _sample_cache_response():
    return {
        "filename": "bill.jpg",
        "engine": "cache",
        "from_cache": True,
        "pages": [{"page_number": 1, "_layer_chain": ["text"], "_confidence_band": "hi"}],
    }


class OcrResponseNoEngineLeakTests(unittest.TestCase):
    def _assert_clean(self, raw):
        keys = list(_iter_keys(strip_internal_fields(raw)))
        leaked_internal = [k for k in keys if isinstance(k, str) and k.startswith("_")]
        self.assertEqual(leaked_internal, [], f"_ 前缀 debug key 泄漏: {leaked_internal}")
        leaked_engine = [
            k for k in keys if isinstance(k, str) and any(s in k.lower() for s in _LEAK_SUBSTRINGS)
        ]
        self.assertEqual(leaked_engine, [], f"引擎/品牌/层 key 泄漏: {leaked_engine}")

    def test_main_response_no_leak(self):
        self._assert_clean(_sample_main_response())

    def test_cache_response_no_leak(self):
        self._assert_clean(_sample_cache_response())

    def test_business_fields_preserved(self):
        # 净化不得误伤中性业务字段。
        out = strip_internal_fields(_sample_main_response())
        self.assertEqual(out["filename"], "bill.jpg")
        self.assertEqual(out["confidence"], 0.9)
        self.assertEqual(out["pages"][0]["fields"]["total"], "100")
        self.assertEqual(out["invoices"][0]["fields"]["total"], "100")

    def test_from_cache_flag_preserved(self):
        out = strip_internal_fields(_sample_cache_response())
        self.assertTrue(out["from_cache"])


if __name__ == "__main__":
    unittest.main()
