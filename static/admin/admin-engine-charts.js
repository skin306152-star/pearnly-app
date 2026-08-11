/*
 * Pearnly · admin-engine-charts.js · 超管「OCR 引擎」页的图表层
 *
 * ECharts 按需现拉(static/vendor/echarts · 664KB):超管后台七个页面里只有这一页画图,
 * 挂在 admin.html 上会让另外六页白背这份体积。拉取失败不静默 —— 调用方把 reject 画成
 * 错误态带重试,图表区不许出现"空着但看着像没数据"。
 *
 * 配色分工:柱图用状态色(超/未超定价,固定不随主题),环形图用分类色板(定序不轮回);
 * 文字/网格/表面取页面 CSS 令牌,主题真换了图跟着换。
 */
(function () {
    'use strict';

    const ECHARTS_SRC = '/static/vendor/echarts/echarts.common.min.js';

    // 颜色全部取自 admin-viz.css 的令牌(状态色 --viz-over/-under 是「超没超售价」的二值判断,
    // --viz-1..6 是分类色板定序)。第 7 个入口起并入「其他」,不现造新色。
    const SERIES_SLOTS = ['--viz-1', '--viz-2', '--viz-3', '--viz-4', '--viz-5', '--viz-6'];
    // 环形图只画到第 5 名(余下并成「其他」):副图只有主图三分之一宽,再多切片标签就叠成一团。
    const MAX_SLICES = 5;
    // 占比低于这条线的切片不外挂标签,靠图例 + 明细表认人 —— 细扇区的引线比数字还占地方。
    const LABEL_MIN_PCT = 6;
    // 拖动停手后才重排:合并连发的 resize,又短到松手时图已经跟上,人察觉不到延迟。
    const RESIZE_DEBOUNCE_MS = 150;

    let _loader = null;
    const _charts = [];

    function _ink(styles, name, fallback) {
        const v = styles ? styles.getPropertyValue(name).trim() : '';
        return v || fallback;
    }

    // 令牌读不到时回落到"能看见"的中性色:图宁可丑,不许因为一个变量没解析出来就画成隐形。
    // getComputedStyle 取一次复用:它每调一次都强制一次样式解析,一张图要读十来个令牌。
    function _theme() {
        let styles = null;
        try {
            styles = getComputedStyle(document.documentElement);
        } catch (_) {}
        return {
            ink: _ink(styles, '--ink', 'rgb(35,25,66)'),
            ink2: _ink(styles, '--ink2', 'rgb(91,88,117)'),
            ink3: _ink(styles, '--ink3', 'rgb(143,138,168)'),
            line: _ink(styles, '--line', 'rgb(236,232,246)'),
            card: _ink(styles, '--card', 'rgb(255,255,255)'),
            over: _ink(styles, '--viz-over', 'rgb(208,59,59)'),
            under: _ink(styles, '--viz-under', 'rgb(12,163,12)'),
            other: _ink(styles, '--viz-other', 'rgb(173,181,189)'),
            series: SERIES_SLOTS.map(function (slot) {
                return _ink(styles, slot, 'rgb(42,120,214)');
            }),
        };
    }

    function ensure() {
        if (window.echarts) return Promise.resolve(window.echarts);
        if (_loader) return _loader;
        _loader = new Promise(function (resolve, reject) {
            const s = document.createElement('script');
            s.src = ECHARTS_SRC;
            s.async = true;
            s.onload = function () {
                if (window.echarts) resolve(window.echarts);
                else reject(new Error('echarts loaded but missing'));
            };
            s.onerror = function () {
                _loader = null; // 允许重试按钮再拉一次
                reject(new Error('echarts load failed'));
            };
            document.head.appendChild(s);
        });
        return _loader;
    }

    function _mount(el, option) {
        const chart = window.echarts.init(el, null, { renderer: 'canvas' });
        chart.setOption(option);
        _charts.push(chart);
        return chart;
    }

    function disposeAll() {
        while (_charts.length) {
            const c = _charts.pop();
            try {
                c.dispose();
            } catch (_) {}
        }
    }

    function resizeAll() {
        _charts.forEach(function (c) {
            try {
                c.resize();
            } catch (_) {}
        });
    }

    /**
     * 每页成本柱图 · 横向参考线钉当前定价。
     * rows: [{label, tip, cost_per_page}] 已由调用方过滤掉无页数的行。
     */
    function renderBar(el, rows, price, text) {
        const t = _theme();
        const labels = rows.map(function (r) {
            return r.label;
        });
        const data = rows.map(function (r) {
            return {
                value: r.cost_per_page,
                itemStyle: {
                    color: r.cost_per_page > price ? t.over : t.under,
                    borderRadius: [4, 4, 0, 0],
                },
            };
        });
        return _mount(el, {
            animation: false,
            // 左侧留白不能给 0:横轴标签是斜的,最左那条会被绘图区边缘切掉半截。
            grid: { left: 24, right: 16, top: 34, bottom: 4, containLabel: true },
            tooltip: {
                trigger: 'item',
                backgroundColor: t.card,
                borderColor: t.line,
                textStyle: { color: t.ink, fontSize: 12 },
                formatter: function (p) {
                    return rows[p.dataIndex].tip;
                },
            },
            xAxis: {
                type: 'category',
                data: labels,
                axisLine: { lineStyle: { color: t.line } },
                axisTick: { show: false },
                axisLabel: {
                    color: t.ink2,
                    fontSize: 11,
                    lineHeight: 14,
                    // 一根柱子一个名字,不许跳着标(interval 0)。入口/单据分两行 + 按柱宽截断,
                    // 比斜排好读,也不会像斜排那样把最左那条顶出绘图区被切掉。完整名字在悬浮里。
                    interval: 0,
                    width: 64,
                    overflow: 'truncate',
                    hideOverlap: false,
                },
            },
            yAxis: {
                type: 'value',
                name: text.axisName,
                nameTextStyle: { color: t.ink3, fontSize: 11, align: 'left' },
                axisLabel: { color: t.ink3, fontSize: 11 },
                splitLine: { lineStyle: { color: t.line } },
            },
            series: [
                {
                    type: 'bar',
                    data: data,
                    barMaxWidth: 40,
                    label: {
                        show: true,
                        position: 'top',
                        color: t.ink2,
                        fontSize: 11,
                        formatter: function (p) {
                            return p.value.toFixed(2);
                        },
                    },
                    markLine: {
                        silent: true,
                        symbol: 'none',
                        lineStyle: { type: 'dashed', width: 2, color: t.ink2 },
                        label: {
                            position: 'insideEndTop',
                            color: t.ink2,
                            fontSize: 11,
                            formatter: text.priceLabel,
                        },
                        data: [{ yAxis: price }],
                    },
                },
            ],
        });
    }

    /** 入口成本占比环形图 · 超过 6 个入口并入「其他」,不新造颜色。 */
    function renderDonut(el, slices, text) {
        const t = _theme();
        // 「未归因」永远单独成片:它小就被折进「其他」的话,这块钱就又看不见了 —— 而它正是要看见的。
        const muted = slices.filter(function (s) {
            return s.muted;
        });
        const sorted = slices
            .filter(function (s) {
                return !s.muted;
            })
            .sort(function (a, b) {
                return b.value - a.value;
            });
        const head = sorted.slice(0, MAX_SLICES);
        const tail = sorted.slice(MAX_SLICES);
        const data = head.map(function (s, i) {
            return { name: s.name, value: s.value, itemStyle: { color: t.series[i] } };
        });
        if (tail.length) {
            data.push({
                name: text.other,
                value: tail.reduce(function (sum, s) {
                    return sum + s.value;
                }, 0),
                itemStyle: { color: t.other },
            });
        }
        muted.forEach(function (s) {
            data.push({ name: s.name, value: s.value, itemStyle: { color: t.other } });
        });
        const total = data.reduce(function (sum, d) {
            return sum + d.value;
        }, 0);
        data.forEach(function (d) {
            if (total && (d.value / total) * 100 < LABEL_MIN_PCT) d.label = { show: false };
        });
        return _mount(el, {
            animation: false,
            tooltip: {
                trigger: 'item',
                backgroundColor: t.card,
                borderColor: t.line,
                textStyle: { color: t.ink, fontSize: 12 },
                formatter: function (p) {
                    return p.name + '<br/>฿ ' + p.value.toFixed(2) + ' · ' + p.percent + '%';
                },
            },
            // 图例不分页:分页 = 有几个入口被藏在第二页,而这张图就是给人看「谁在花钱」的。
            legend: {
                bottom: 0,
                type: 'plain',
                itemWidth: 10,
                itemHeight: 10,
                itemGap: 10,
                textStyle: { color: t.ink2, fontSize: 11 },
            },
            series: [
                {
                    type: 'pie',
                    radius: ['46%', '66%'],
                    center: ['50%', '42%'],
                    avoidLabelOverlap: true,
                    itemStyle: { borderColor: t.card, borderWidth: 2 },
                    label: {
                        color: t.ink2,
                        fontSize: 11,
                        formatter: '{b} {d}%',
                    },
                    labelLine: { length: 8, length2: 8, lineStyle: { color: t.ink3 } },
                    data: data,
                },
            ],
        });
    }

    // 拖窗口一次能打出上百个 resize 事件,每个都让两张图重排一次 —— 停手后再重排一次就够。
    let _resizeTimer = null;
    window.addEventListener('resize', function () {
        clearTimeout(_resizeTimer);
        _resizeTimer = setTimeout(resizeAll, RESIZE_DEBOUNCE_MS);
    });

    window.AdminEngineCharts = {
        ensure: ensure,
        renderBar: renderBar,
        renderDonut: renderDonut,
        disposeAll: disposeAll,
        resizeAll: resizeAll,
    };
})();
