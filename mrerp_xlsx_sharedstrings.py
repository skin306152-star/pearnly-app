# -*- coding: utf-8 -*-
"""MR.ERP xlsx · openpyxl 输出转 PhpSpreadsheet 兼容格式(inlineStr→sharedStrings 等).

mrerp_xlsx_generator 拆分 leaf。纯字节级 xlsx 后处理,0 逻辑改。仅 sales_credit 以外
sheet_kind 走此路径(sales_credit 走 korn-clone)。
"""

import io


def _convert_inline_to_shared_strings(xlsx_bytes: bytes, sheet_col_map=None) -> bytes:
    """v27.8.1.9 + v27.8.1.11 · 把 openpyxl 输出转成 MR.ERP / PhpSpreadsheet 兼容格式

    1. inlineStr → sharedStrings(PhpSpreadsheet 不识别 inline)
    2. 缺失的 cell 补「完全空 cell <c r='X#'/>」(跟 Korn 真样本风格一致)
    3. row 加 spans="1:N" 属性(让 PhpSpreadsheet 正确数列)
    4. sheet1 在 row 1/2 加 col 19 完全空 cell(让 dim=A1:S2 跟 Korn 一致)
    5. 去掉 t="n" 属性(Korn 真样本数值 cell 不带 t · default 就是 numeric)

    sheet_col_map: {'sheet1': 18, 'sheet2': 8, 'sheet3': 3} · 各 sheet schema 列数
    """
    import zipfile
    import re as _re
    from collections import OrderedDict

    src_buf = io.BytesIO(xlsx_bytes)
    files = {}
    with zipfile.ZipFile(src_buf, "r") as src_zip:
        for name in src_zip.namelist():
            files[name] = src_zip.read(name)

    shared = OrderedDict()

    def _get_idx(text):
        if text not in shared:
            shared[text] = len(shared)
        return shared[text]

    def _decode_xml_entities(s):
        s = (
            s.replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
            .replace("&apos;", "'")
        )
        s = _re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), s)
        s = _re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), s)
        return s

    inline_full_re = _re.compile(
        r'<c([^>]*?)\st="inlineStr"([^>]*?)>\s*<is>\s*<t(?:\s[^>]*)?>([^<]*)</t>\s*</is>\s*</c>',
        _re.DOTALL,
    )

    def _replace_full(m):
        pre, post, text = m.group(1), m.group(2), m.group(3)
        text = _decode_xml_entities(text)
        idx = _get_idx(text)
        return f'<c{pre} t="s"{post}><v>{idx}</v></c>'

    inline_empty_re = _re.compile(
        r'<c([^>]*?)\st="inlineStr"([^>]*?)\s*(?:/>|>\s*</c>|>\s*<is\s*/>\s*</c>|>\s*<is>\s*</is>\s*</c>)',
        _re.DOTALL,
    )

    def _replace_empty(m):
        pre, post = m.group(1), m.group(2)
        # v27.8.1.11 · 直接输出完全空 cell(无 t 无 v · 跟 Korn 风格一致)
        return f"<c{pre}{post}/>"

    # 去掉数值 cell 的 t="n" 属性(Korn 不带 t)
    numeric_t_re = _re.compile(r'<c([^>]*?)\st="n"([^>]*?)>(<v>[^<]*</v>)</c>')

    def _strip_numeric_t(m):
        pre, post, vtag = m.group(1), m.group(2), m.group(3)
        return f"<c{pre}{post}>{vtag}</c>"

    def _col_letter(n):
        s = ""
        while n > 0:
            n, r = divmod(n - 1, 26)
            s = chr(65 + r) + s
        return s

    def _process_sheet_xml(xml, sheet_name):
        # 阶段 1:cell 类型转换
        xml = inline_full_re.sub(_replace_full, xml)
        xml = inline_empty_re.sub(_replace_empty, xml)
        xml = numeric_t_re.sub(_strip_numeric_t, xml)

        col_target = (sheet_col_map or {}).get(sheet_name)
        if not col_target:
            return xml

        # sheet1 末尾 +1 占位 cell(对齐 Korn dim=A1:S2)
        if sheet_name == "sheet1":
            col_target_total = col_target + 1
        else:
            col_target_total = col_target

        # 阶段 2:每个 row 补缺失 cell + 加 spans
        def _process_row(rm):
            row_attr = rm.group(1)
            row_inner = rm.group(2)
            rn_match = _re.search(r'r="(\d+)"', row_attr)
            if not rn_match:
                return rm.group(0)
            row_num = int(rn_match.group(1))
            existing_cols = set()
            for cm in _re.finditer(r'<c\s+r="([A-Z]+)' + str(row_num) + r'"', row_inner):
                existing_cols.add(cm.group(1))
            missing = []
            for c in range(1, col_target_total + 1):
                letter = _col_letter(c)
                if letter not in existing_cols:
                    missing.append(f'<c r="{letter}{row_num}"/>')
            if missing:
                row_inner = row_inner + "".join(missing)
            if "spans=" not in row_attr:
                row_attr = row_attr + f' spans="1:{col_target_total}"'
            return f"<row{row_attr}>{row_inner}</row>"

        xml = _re.sub(r"<row([^>]*)>(.*?)</row>", _process_row, xml, flags=_re.DOTALL)

        # 阶段 3:重算 dimension
        new_dim_letter = _col_letter(col_target_total)
        max_row = 1
        for rm in _re.finditer(r'<row r="(\d+)"', xml):
            rn = int(rm.group(1))
            if rn > max_row:
                max_row = rn
        new_dim = f"A1:{new_dim_letter}{max_row}"
        xml = _re.sub(r'<dimension ref="[^"]+"', f'<dimension ref="{new_dim}"', xml)
        return xml

    for name in list(files.keys()):
        if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
            xml = files[name].decode("utf-8")
            sheet_name = name.split("/")[-1].replace(".xml", "")
            xml = _process_sheet_xml(xml, sheet_name)
            files[name] = xml.encode("utf-8")

    if shared:

        def _xml_escape(s):
            return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        parts = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            f'count="{len(shared)}" uniqueCount="{len(shared)}">',
        ]
        for text in shared:
            parts.append(f'<si><t xml:space="preserve">{_xml_escape(text)}</t></si>')
        parts.append("</sst>")
        files["xl/sharedStrings.xml"] = "".join(parts).encode("utf-8")

        ct = files["[Content_Types].xml"].decode("utf-8")
        if "sharedStrings.xml" not in ct:
            ct = ct.replace(
                "</Types>",
                '<Override PartName="/xl/sharedStrings.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
                "</Types>",
            )
            files["[Content_Types].xml"] = ct.encode("utf-8")

        rels_path = "xl/_rels/workbook.xml.rels"
        if rels_path in files:
            rels = files[rels_path].decode("utf-8")
            if "sharedStrings.xml" not in rels:
                rid_nums = [int(m.group(1)) for m in _re.finditer(r'Id="rId(\d+)"', rels)]
                new_rid = (max(rid_nums) if rid_nums else 0) + 1
                rels = rels.replace(
                    "</Relationships>",
                    f'<Relationship Id="rId{new_rid}" '
                    f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" '
                    f'Target="sharedStrings.xml"/></Relationships>',
                )
                files[rels_path] = rels.encode("utf-8")

    out_buf = io.BytesIO()
    with zipfile.ZipFile(out_buf, "w", zipfile.ZIP_DEFLATED) as out_zip:
        for name, data in files.items():
            out_zip.writestr(name, data)
    return out_buf.getvalue()
