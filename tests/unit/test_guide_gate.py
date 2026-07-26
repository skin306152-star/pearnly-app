# -*- coding: utf-8 -*-
"""使用教程内容闸的覆盖率测试(scripts/check_guide.py)。

这个仓库栽过「闸报绿其实闸没看」的跟头(清单式闸只数了数量、没真读内容,照样全绿)。
所以每道闸都得有反证:临时目录造出对应的坏数据,断言闸真的报红、且报的是那一条。
干净基线同时兜住另一头 —— 闸不许把好数据也判红,否则「红」失去信息量。
"""

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "check_guide",
    Path(__file__).resolve().parent.parent.parent / "scripts" / "check_guide.py",
)
guide = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(guide)


def _bi(zh, th):
    return {"zh": zh, "th": th}


def _index():
    return {
        "book": _bi("Express 推送手册", "คู่มือส่งข้อมูลเข้า Express"),
        "sections": [{"id": "daily", "title": _bi("日常推送", "งานประจำวัน"), "planned": 3}],
    }


def _links_ts(mapping, sec="daily", extra=""):
    """伪造一份 guide-links.ts —— 闸靠正则读它,所以喂给闸的必须是真 TS 文本而不是 dict。"""
    body = "".join(f"    {code}: '{ch}',\n" for code, ch in mapping.items())
    return (
        "import { esc, T } from './guide-content.js';\n"
        f"const REASON_CHAPTER: Record<string, ChapterRef> = inSection('{sec}', {{\n"
        f"{extra}{body}}});\n"
    )


def _section():
    return {
        "id": "daily",
        "chapters": [
            {
                "id": "push-upload-batch",
                "title": _bi("上传本批票据", "อัปโหลดเอกสารชุดนี้"),
                "intro": _bi("收到一批票据后在本页一次性上传。", "อัปโหลดเอกสารทั้งชุดจากหน้านี้"),
                "steps": [
                    {
                        "text": _bi("点击「录入工作台」。", "คลิก「บันทึกเอกสาร」"),
                        "shot": "upload-01-nav",
                        "caption": _bi("左侧导航", "เมนูด้านซ้าย"),
                    },
                    {"text": _bi("点击「开始」。", "คลิก「เริ่ม」")},
                ],
                "notes": [{"kind": "warn", "text": _bi("识别按张计费。", "คิดค่าบริการเป็นรายใบ")}],
            }
        ],
    }


class GuideGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="guide-gate-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.content = self.tmp / "content"
        self.shots = self.tmp / "shots"
        self.content.mkdir()
        self.shots.mkdir()
        self.index = _index()
        self.section = _section()
        self.links = self.tmp / "guide-links.ts"
        self.link_map = {"no_ar_account": "push-upload-batch"}
        self.link_sec = "daily"
        self.link_extra = ""
        self.link_src = None  # 非 None 时按原样写,用来喂「写法变了」这类坏形状
        self._write_links()

    def _write_links(self):
        src = self.link_src
        if src is None:
            src = _links_ts(self.link_map, self.link_sec, self.link_extra)
        self.links.write_text(src, encoding="utf-8")

    def _write(self):
        (self.content / "index.json").write_text(
            json.dumps(self.index, ensure_ascii=False), encoding="utf-8"
        )
        (self.content / "daily.json").write_text(
            json.dumps(self.section, ensure_ascii=False), encoding="utf-8"
        )
        self._write_links()

    def _shot(self, name, langs=("zh", "th")):
        for lg in langs:
            (self.shots / f"{name}.{lg}.png").write_bytes(b"\x89PNG")

    def _run(self):
        self._write()
        return guide.collect_failures(self.content, self.shots, self.links)

    def _chapter(self):
        return self.section["chapters"][0]

    # -- 控制组:好数据必须全绿,否则下面每条「红」都无从归因 ------------------

    def test_clean_fixture_passes(self):
        self._shot("upload-01-nav")
        self.assertEqual(self._run(), [])

    # -- 闸① 配图存在 --------------------------------------------------------

    def test_missing_thai_shot_fails(self):
        self._shot("upload-01-nav", langs=("zh",))
        fails = self._run()
        self.assertTrue(any(f.startswith("[配图]") and "upload-01-nav.th.png" in f for f in fails))
        self.assertFalse(any("upload-01-nav.zh.png" in f for f in fails))

    def test_missing_both_shots_fails_twice(self):
        fails = [f for f in self._run() if f.startswith("[配图]")]
        self.assertEqual(len(fails), 2)
        self.assertIn("push-upload-batch 第1步", fails[0])

    def test_step_without_shot_is_not_flagged(self):
        # 第 2 步没有 shot 字段 —— 不该被当成「缺图」。
        self._shot("upload-01-nav")
        self.assertEqual([f for f in self._run() if f.startswith("[配图]")], [])

    # -- 闸② 双语齐全 --------------------------------------------------------

    def test_missing_thai_step_text_fails(self):
        self._shot("upload-01-nav")
        self._chapter()["steps"][1]["text"]["th"] = ""
        fails = self._run()
        self.assertTrue(
            any(f.startswith("[双语]") and "第2步.text" in f and "th" in f for f in fails)
        )

    def test_blank_thai_is_treated_as_empty(self):
        # 只有空白字符 = 没翻译 · 别让「  」蒙混过关。
        self._shot("upload-01-nav")
        self._chapter()["intro"]["th"] = "   "
        self.assertTrue(any("intro" in f and f.startswith("[双语]") for f in self._run()))

    def test_missing_thai_title_and_caption_and_note_all_fail(self):
        self._shot("upload-01-nav")
        self._chapter()["title"]["th"] = ""
        self._chapter()["steps"][0]["caption"]["th"] = ""
        self._chapter()["notes"][0]["text"]["th"] = ""
        fails = [f for f in self._run() if f.startswith("[双语]")]
        self.assertEqual(len(fails), 3, fails)
        self.assertTrue(any(".title" in f for f in fails))
        self.assertTrue(any(".caption" in f for f in fails))
        self.assertTrue(any("提示1.text" in f for f in fails))

    def test_missing_chinese_also_fails(self):
        self._shot("upload-01-nav")
        del self._chapter()["intro"]["zh"]
        self.assertTrue(any("intro" in f and "zh" in f for f in self._run()))

    # -- 闸③ 一屏 ------------------------------------------------------------

    def test_over_word_budget_fails(self):
        self._shot("upload-01-nav")
        self._chapter()["steps"][1]["text"]["zh"] = "字" * (guide.MAX_ZH_CHARS + 1)
        fails = [f for f in self._run() if f.startswith("[一屏]")]
        self.assertEqual(len(fails), 1, fails)
        self.assertIn("push-upload-batch", fails[0])

    def test_word_budget_counts_intro_steps_and_notes_together(self):
        # 单条都不超,合起来超 —— 一屏闸算的是整章,不是单段。
        self._shot("upload-01-nav")
        chunk = "字" * (guide.MAX_ZH_CHARS // 2)
        self._chapter()["intro"]["zh"] = chunk
        self._chapter()["steps"][1]["text"]["zh"] = chunk
        self._chapter()["notes"][0]["text"]["zh"] = chunk
        self.assertTrue(any(f.startswith("[一屏]") for f in self._run()))

    def test_at_word_budget_passes(self):
        self._shot("upload-01-nav")
        ch = self._chapter()
        used = sum(
            len(t.replace(" ", ""))
            for t in (
                ch["intro"]["zh"],
                ch["steps"][0]["text"]["zh"],
                ch["notes"][0]["text"]["zh"],
            )
        )
        ch["steps"][1]["text"]["zh"] = "字" * (guide.MAX_ZH_CHARS - used)
        self.assertEqual(self._run(), [])

    def test_too_many_steps_fails(self):
        self._shot("upload-01-nav")
        extra = {"text": _bi("再点一下。", "คลิกอีกครั้ง")}
        self._chapter()["steps"] += [dict(extra) for _ in range(guide.MAX_STEPS)]
        fails = [f for f in self._run() if f.startswith("[一屏]")]
        self.assertTrue(any("步 >" in f for f in fails), fails)

    # -- 闸⑤ 内部话 ----------------------------------------------------------

    def _insider(self):
        return [f for f in self._run() if f.startswith("[内部话]")]

    def test_self_reference_talk_fails(self):
        # 2026-07-25 真机验收的原句:读者没见过旧文档,这句话让他去核对不存在的东西。
        self._shot("upload-01-nav")
        self._chapter()["intro"]["zh"] = "旧文档中「每天必须执行 PACK」的说法已不存在。"
        fails = self._insider()
        self.assertEqual(len(fails), 1, fails)
        self.assertIn("旧文档", fails[0])
        self.assertIn("文档自指", fails[0])
        self.assertIn("push-upload-batch", fails[0])

    def test_speech_directive_talk_fails(self):
        # 教程是操作手册不是话术稿 —— 一句里两个词就报两条,别只报第一个。
        self._shot("upload-01-nav")
        self._chapter()["steps"][1]["text"]["zh"] = "继续这样说明会引起客户追问。"
        fails = self._insider()
        self.assertEqual(len(fails), 2, fails)
        self.assertTrue(all("第2步.text" in f and "指挥对外言行" in f for f in fails), fails)
        self.assertTrue(any("会引起客户追问" in f for f in fails), fails)
        self.assertTrue(any("继续这样说明" in f for f in fails), fails)

    def test_code_jargon_fails(self):
        self._shot("upload-01-nav")
        self._chapter()["notes"][0]["text"]["zh"] = "这一步会重建 manifest。"
        fails = self._insider()
        self.assertEqual(len(fails), 1, fails)
        self.assertIn("manifest", fails[0])
        self.assertIn("代码内部词", fails[0])
        self.assertIn("提示1.text", fails[0])

    def test_code_jargon_in_thai_side_fails(self):
        # 组三跨语种都查:泰文侧甩个 adapter,泰籍会计一样看不懂。
        self._shot("upload-01-nav")
        self._chapter()["steps"][0]["text"]["th"] = "ระบบจะเรียก adapter ตัวใหม่"
        fails = self._insider()
        self.assertEqual(len(fails), 1, fails)
        self.assertIn("(th)", fails[0])
        self.assertIn("adapter", fails[0])

    def test_thai_self_reference_is_a_known_gap(self):
        # 组一/组二只查中文侧:泰文没有「旧文档」这种定型说法,硬列词表要么漏要么误伤。
        # 钉住这个缺口 —— 哪天补上了泰文词表,这条会红,提醒改测试而不是悄悄漂移。
        self._shot("upload-01-nav")
        self._chapter()["intro"]["th"] = "ตามเอกสารเก่า ต้องกด PACK ทุกวัน"
        self.assertEqual(self._insider(), [])

    def test_batch_word_is_not_insider_talk(self):
        # 防误伤:「进项 / 销项 · 本批」是界面上真有的字样,收进禁词表会误判 31 处正文。
        self._shot("upload-01-nav")
        self._chapter()["intro"][
            "zh"
        ] = "上传前在侧栏勾选「进项 / 销项 · 本批」与「过账去向 · 本批」。"
        self._chapter()["notes"][0]["text"]["zh"] = "本批票据的字段在核对屏左侧。"
        self.assertEqual(self._run(), [])

    def test_onscreen_key_literal_is_not_insider_talk(self):
        # 防误伤:界面原样印着这串英文键名,教程必须教会计认它。整词匹配放行键名里的
        # preflight / payload,只逮裸着写的那种。
        self._shot("upload-01-nav")
        self._chapter()["steps"][1]["text"][
            "zh"
        ] = "界面会印出英文键名 erp-preflight-key-payload_version,按上下两行判断即可。"
        self.assertEqual(self._run(), [])

    def test_bare_jargon_still_fails_next_to_key_literal(self):
        # 上一条放行的是键名,不是这个词本身 —— 裸着写照样红,否则整词规则等于放弃组三。
        self._shot("upload-01-nav")
        self._chapter()["steps"][1]["text"]["zh"] = "payload 的格式由云端决定。"
        self.assertTrue(any("payload" in f for f in self._insider()), self._insider())

    # -- 清单:planned 倒挂 / id 重复 ----------------------------------------

    def test_chapters_exceeding_planned_fails(self):
        self._shot("upload-01-nav")
        self.index["sections"][0]["planned"] = 0
        fails = [f for f in self._run() if "planned" in f]
        self.assertEqual(len(fails), 1, fails)
        self.assertIn("实际 1 章", fails[0])

    def test_planned_equal_to_chapter_count_passes(self):
        self._shot("upload-01-nav")
        self.index["sections"][0]["planned"] = 1
        self.assertEqual(self._run(), [])

    def test_duplicate_chapter_id_fails(self):
        self._shot("upload-01-nav")
        dup = json.loads(json.dumps(self._chapter()))
        self.section["chapters"].append(dup)
        self.index["sections"][0]["planned"] = 5
        fails = [f for f in self._run() if "重复" in f]
        self.assertEqual(len(fails), 1, fails)
        self.assertIn("push-upload-batch", fails[0])

    def test_duplicate_chapter_id_across_sections_fails(self):
        self._shot("upload-01-nav")
        self.index["sections"].append(
            {"id": "setup", "title": _bi("接入", "การเชื่อมต่อ"), "planned": 2}
        )
        other = json.loads(json.dumps(self.section))
        other["id"] = "setup"
        self._write()
        (self.content / "setup.json").write_text(
            json.dumps(other, ensure_ascii=False), encoding="utf-8"
        )
        fails = guide.collect_failures(self.content, self.shots, self.links)
        self.assertTrue(any("重复" in f and "daily" in f and "setup" in f for f in fails), fails)

    # -- 闸④ 深链落到真章 ----------------------------------------------------

    def test_deeplink_to_missing_chapter_fails(self):
        self._shot("upload-01-nav")
        self.link_map = {"no_ar_account": "push-not-written-yet"}
        fails = [f for f in self._run() if f.startswith("[深链]")]
        self.assertEqual(len(fails), 1, fails)
        self.assertIn("no_ar_account", fails[0])
        self.assertIn("daily/push-not-written-yet", fails[0])

    def test_deeplink_to_unwritten_section_fails(self):
        # 篇在 index 里登记了但正文还没开工 —— 章照样不存在,深链照样落空。
        self.index["sections"].append(
            {"id": "stuck", "title": _bi("推不进去怎么办", "เมื่อส่งไม่สำเร็จ"), "planned": 40}
        )
        self.link_sec = "stuck"
        self._shot("upload-01-nav")
        fails = [f for f in self._run() if f.startswith("[深链]")]
        self.assertEqual(len(fails), 1, fails)
        self.assertIn("stuck/push-upload-batch", fails[0])

    def test_whole_table_of_placeholder_ids_fails(self):
        # 2026-07-25 的真事:整表 35 条写的是占位 id,正文里全是另一套前缀,一条都没命中,
        # 而页面只是安静地退回手册首页。闸必须逐条报,别只报第一条。
        self._shot("upload-01-nav")
        self.link_map = {
            c: f"stuck-{c}" for c in ("no_ar_account", "credit_note", "low_confidence")
        }
        fails = [f for f in self._run() if f.startswith("[深链]")]
        self.assertEqual(len(fails), 3, fails)

    def test_commented_out_mapping_is_ignored(self):
        # 注释里的示例码不是真映射:报它就是假红,也说明闸在裸 grep 整个文件而不是读表。
        self._shot("upload-01-nav")
        self.link_extra = "    // retired_code: 'gone-chapter',\n"
        self.assertEqual([f for f in self._run() if f.startswith("[深链]")], [])

    def test_unreadable_table_shape_fails(self):
        # 表被清空、或 inSection(...) 换了写法 —— 闸一条都抠不出来时会「全绿」,
        # 而全绿正是它该报红的时候(本仓库栽过「闸报绿其实闸没看」)。
        self._shot("upload-01-nav")
        self.link_src = "export const REASON_CHAPTER = {};\n"
        fails = [f for f in self._run() if f.startswith("[深链]")]
        self.assertEqual(len(fails), 1, fails)
        self.assertIn("闸失效", fails[0])

    def test_missing_links_file_fails(self):
        self._shot("upload-01-nav")
        self._write()
        fails = guide.collect_failures(self.content, self.shots, self.tmp / "gone.ts")
        self.assertTrue(any(f.startswith("[深链]") and "文件不存在" in f for f in fails), fails)

    # -- 结构性坏数据不许把闸打崩(崩了退出码也非零,但报不出人话) ----------

    def test_unstarted_section_is_not_a_failure(self):
        # 七篇里六篇还没开工:文件不存在 = 空篇,前端也按「编写中」渲染,不该报红。
        self._shot("upload-01-nav")
        self.index["sections"].append(
            {"id": "stuck", "title": _bi("推不进去怎么办", "เมื่อส่งไม่สำเร็จ"), "planned": 40}
        )
        self.assertEqual(self._run(), [])

    def test_orphan_section_file_fails(self):
        self._shot("upload-01-nav")
        self._write()
        (self.content / "concept.json").write_text('{"id":"concept","chapters":[]}', "utf-8")
        fails = guide.collect_failures(self.content, self.shots, self.links)
        self.assertTrue(any("未登记" in f for f in fails), fails)

    def test_broken_json_reports_instead_of_raising(self):
        self._write()
        (self.content / "daily.json").write_text("{ 坏掉的 json", encoding="utf-8")
        fails = guide.collect_failures(self.content, self.shots, self.links)
        self.assertTrue(any("JSON 解析失败" in f for f in fails), fails)

    def test_missing_index_reports_instead_of_raising(self):
        fails = guide.collect_failures(self.content, self.shots, self.links)
        self.assertTrue(any("index.json" in f for f in fails), fails)


class GuideGateExitCodeTests(unittest.TestCase):
    """CLI 接线:闸报红必须落到退出码上,否则 CI 里等于没挂。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="guide-gate-cli-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "content").mkdir()
        (self.tmp / "shots").mkdir()
        self.links = self.tmp / "guide-links.ts"
        self.links.write_text(_links_ts({"no_ar_account": "push-upload-batch"}), encoding="utf-8")
        self.argv = [
            "--content",
            str(self.tmp / "content"),
            "--shots",
            str(self.tmp / "shots"),
            "--links",
            str(self.links),
        ]

    def _write(self, index, section, shots=()):
        (self.tmp / "content" / "index.json").write_text(
            json.dumps(index, ensure_ascii=False), encoding="utf-8"
        )
        (self.tmp / "content" / "daily.json").write_text(
            json.dumps(section, ensure_ascii=False), encoding="utf-8"
        )
        for name in shots:
            for lg in ("zh", "th"):
                (self.tmp / "shots" / f"{name}.{lg}.png").write_bytes(b"\x89PNG")

    def test_exit_zero_on_clean_data(self):
        self._write(_index(), _section(), shots=("upload-01-nav",))
        self.assertEqual(guide.main(self.argv), 0)

    def test_exit_one_on_missing_shot(self):
        self._write(_index(), _section())
        self.assertEqual(guide.main(self.argv), 1)

    def test_exit_one_on_dead_deeplink(self):
        self._write(_index(), _section(), shots=("upload-01-nav",))
        self.links.write_text(_links_ts({"no_ar_account": "nope"}), encoding="utf-8")
        self.assertEqual(guide.main(self.argv), 1)


class RepoDataTests(unittest.TestCase):
    """仓库现有教程数据必须过闸(闸挂 CI 前先证明它对真数据是绿的)。"""

    def test_shipped_guide_content_passes(self):
        self.assertEqual(guide.collect_failures(), [])

    def test_shipped_reason_chapters_resolve_to_real_chapters(self):
        """独立于闸再验一遍真表:35 条深链条条落在 stuck 篇真章上。

        只断言 collect_failures() 为空是不够的 —— 正则若一条都没读到,闸同样是绿的。
        故这里额外钉住条数与所属篇,自己读 JSON 对照,不复用闸的判断。
        """
        links = guide.parse_reason_chapters()
        self.assertIsNotNone(links, "guide-links.ts 没找到")
        self.assertGreaterEqual(len(links), 30, "整张表没读全 — 正则漏读时闸会安静地全绿")
        self.assertEqual({sec for _, sec, _ in links}, {"stuck"})
        stuck = json.loads((guide.CONTENT_DIR / "stuck.json").read_text(encoding="utf-8"))
        ids = {c["id"] for c in stuck["chapters"]}
        self.assertEqual(sorted({ch for _, _, ch in links if ch not in ids}), [])


if __name__ == "__main__":
    unittest.main()
