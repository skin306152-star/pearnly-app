/* 看板工具条(筛选 / 批量开单 / 本期缺单条)词条 · 四份词典已由前置分片初始化(同
 * ai-i18n-fail.js 先例)。/ai 是事务所内部工作台,按 adm-* 超管键先例只写 zh + th;
 * en/ja 由 at() 回落 zh,对外开放再补两语。守门测试 tests/unit/test_ai_board_tools_render.py
 * 锁 zh/th key 集合一致 + 每个 kb_ 词条都真被引用(防死词条)。
 *
 * 文案口径:缺单条要答得出「这家本月还差哪几张单」,批量按钮要写明开的是哪一期——
 * 「批量开单」四个字不说账期,点下去开出哪个月全靠猜。 */
Object.assign(window.__AI_I18N_ZH__, {
    kb_missing_list: '{p} 还缺 {n} 张单：{list}',
    kb_missing_unknown: '{p} 还没开单',
    kb_check_aria: '选中 {name}，一起开单',
    kb_bulk_selected: '已选 {n} 家',
    kb_bulk_clear: '取消选择',
    kb_bulk_open: '开 {p} 的单',
    kb_bulk_open_busy: '开单中…',
    kb_bulk_result_ok: '已开出 {n} 张单',
    kb_bulk_result_fail: '{n} 家没开成 · 重新勾选再试一次，不会重复开单',
    kb_col_empty_filtered: '这一列没有符合筛选的客户',
});

Object.assign(window.__AI_I18N_TH__, {
    kb_missing_list: '{p} ยังขาด {n} ใบงาน: {list}',
    kb_missing_unknown: '{p} ยังไม่ได้เปิดใบงาน',
    kb_check_aria: 'เลือก {name} เพื่อเปิดใบงานพร้อมกัน',
    kb_bulk_selected: 'เลือกแล้ว {n} ราย',
    kb_bulk_clear: 'ยกเลิกการเลือก',
    kb_bulk_open: 'เปิดใบงานงวด {p}',
    kb_bulk_open_busy: 'กำลังเปิดใบงาน…',
    kb_bulk_result_ok: 'เปิดใบงานแล้ว {n} ใบ',
    kb_bulk_result_fail: '{n} รายเปิดไม่สำเร็จ · เลือกใหม่แล้วลองอีกครั้ง จะไม่เกิดใบงานซ้ำ',
    kb_col_empty_filtered: 'ไม่มีลูกค้าที่ตรงกับตัวกรองในคอลัมน์นี้',
});
