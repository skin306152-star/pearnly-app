# -*- coding: utf-8 -*-
"""管线异常分诊(recognize/core.classify_pipeline_error)· 入口怪文件实弹 2026-07-06。

fake_ext2.jpg(PDF 字节配 .jpg 扩展名)→ Vision code 3 直通 500 吓用户;用户文件
问题必须 400 + 人话码(err.ocr.unreadable_file 四语已配),引擎故障才 500。

分诊按异常类型判(Layer1InvalidImageError · 见 services/ocr/layer1_base.py),
不靠字符串匹配 Vision 报文措辞(那是 Google 侧文本,可能改写)。
"""

import unittest

from services.ocr.layer1_base import Layer1InvalidImageError, Layer1PDFError
from services.ocr.recognize.core import classify_pipeline_error


class ClassifyPipelineErrorTests(unittest.TestCase):
    def test_invalid_image_is_user_fault(self):
        exc = Layer1InvalidImageError("layer1: page 1: API error code 3: Bad image data.")
        self.assertEqual(classify_pipeline_error(exc), "ocr.unreadable_file")

    def test_pdf_error_and_valueerror_keep_existing_mapping(self):
        self.assertTrue(
            str(classify_pipeline_error(Layer1PDFError("x"))).startswith("ocr.invalid_file")
        )
        self.assertTrue(
            str(classify_pipeline_error(ValueError("bad"))).startswith("ocr.invalid_file")
        )

    def test_engine_faults_stay_500(self):
        for exc in (RuntimeError("quota exceeded"), TimeoutError("deadline"), KeyError("x")):
            self.assertIsNone(classify_pipeline_error(exc))


if __name__ == "__main__":
    unittest.main(verbosity=2)
