// 泰铢金额的排版口径 · /home SPA 单出口
//
// ฿ 的墨迹比它的字宽宽半像素,紧跟数字会糊成一个看不出是什么的字(实测详见
// static/ai/ai-format.js —— /ai SPA 早就是这个口径,这里不另起第二套)。垫一个窄空格
// U+2009 分开,任何字体/字号/字重下都不再粘连,又比普通空格窄得多、不像两个词。
//
// 此前 28 个文件各自手写这个符号,首页同一屏上能并存三种写法(有普通空格 / 没空格 /
// 数字在前符号在后)——2026-07-30 四语双端走查实测。焊死在这里,别处一律借;
// 守门在 tests/unit/test_home_money_single_exit.py。

export const BAHT = '฿\u2009'; // ฿ + 窄空格 U+2009

// 整数泰铢排版(四舍五入 + 千分位):报表/榜单用。此前 pos-sales-log / pos-audit /
// 销售仪表盘三处逐字各写一份,口径(舍入规则 · locale)漂了没人拦 —— 收进单出口。
export function bahtInt(v: string | number): string {
    return Math.round(Number(v) || 0).toLocaleString('en-US');
}
