/*
 * Pearnly AI · ai-intake-bank-sales.js · 银行流水倒推销项(SA-3b)网络编排
 *
 * 拆自 ai-intake.js(单文件<500 行铁律已在预算线上,同 ai-payroll-annual-render.js 拆分
 * 先例)——纯粹是体量拆分,不是独立视图:折叠/行级裁决/让 AI 预判/采用建议值 四个动作
 * 操作的仍是 ai-intake.js 的收料会话态(S.bankSalesUi/S.order/S.formOpen 等)。
 *
 * create(getS, render) 是工厂:ai-intake.js 在 mount() 时传入一个「取当前会话态」的 getter
 * (getS() 返回它模块内可重新赋值的 S)与它的 render()。本文件内部按 ai-intake.js 既有的
 * session 卫哨范式(捕获会话引用,回调落地时 getS() 若已指向别的会话就不认——换客户/换单
 * 时旧回调不能污染新会话)驱动网络调用与乐观 UI。
 *
 * 建议本体不在这里持有:行级裁决/预判落库成功后一律 refreshOrder() 重取 order_detail,
 * 让 bank_sales_suggestion 投影由服务端读侧重算,不在前端拼一份影子状态跟着分叉。
 */
(function () {
    'use strict';

    // decideRow/run 两处失败回调同款「映射 API 错误码 → 可译 key,查不到译名就兜底
    // err_generic」判据,抽出避免逐字重复。
    function errKey(err) {
        var key = AI.api.mapApiErrorKey(err && err.code);
        return key !== 'err_generic' && at(key) !== key ? key : 'err_generic';
    }

    function create(getS, render) {
        function refreshOrder(session) {
            return session.api.getOrder(session.orderId).then(function (detail) {
                if (getS() !== session) return;
                session.order = detail;
                session.needsSales = (detail.needs || []).indexOf('sales_summary') >= 0;
                render();
            });
        }

        function toggleFold(kind) {
            var S = getS();
            if (!S.bankSalesUi.open || !(kind in S.bankSalesUi.open)) return;
            S.bankSalesUi.open[kind] = !S.bankSalesUi.open[kind];
            render();
        }

        function decideRow(fingerprint, verdict) {
            var S = getS();
            if (!fingerprint || S.bankSalesUi.rowBusy[fingerprint]) return;
            var session = S;
            S.bankSalesUi.rowBusy[fingerprint] = true;
            S.bankSalesUi.rowErr[fingerprint] = null;
            render();
            S.api
                .decideBankSales(S.orderId, { fingerprint: fingerprint, verdict: verdict })
                .then(function () {
                    if (getS() !== session) return;
                    delete session.bankSalesUi.rowBusy[fingerprint];
                    return refreshOrder(session);
                })
                .catch(function (err) {
                    if (getS() !== session) return;
                    session.bankSalesUi.rowBusy[fingerprint] = false;
                    session.bankSalesUi.rowErr[fingerprint] = errKey(err);
                    render();
                });
        }

        function run() {
            var S = getS();
            if (S.bankSalesUi.runBusy) return;
            var session = S;
            S.bankSalesUi.runBusy = true;
            S.bankSalesUi.runErrKey = null;
            render();
            S.api
                .runBankSales(S.orderId)
                .then(function () {
                    if (getS() !== session) return;
                    session.bankSalesUi.runBusy = false;
                    return refreshOrder(session);
                })
                .catch(function (err) {
                    if (getS() !== session) return;
                    session.bankSalesUi.runBusy = false;
                    session.bankSalesUi.runErrKey = errKey(err);
                    render();
                });
        }

        // 「采用建议值」:只把 sales_amount/output_vat 预填进既有人工销项表单,不提交
        // (硬闸#2)——展开表单 + 存一次性预填值,ai-intake.js 的 render() 消费。canApply
        // 与卡上按钮 disabled 判据同一份纯函数,双保险(按钮该灰的时候点了也不动)。
        function apply() {
            var S = getS();
            var sug = S.order && S.order.bank_sales_suggestion;
            if (!AI.bankSalesRender.canApply(sug)) return;
            S.formOpen = true;
            S.formErr = false;
            S.bankSalesPrefill = { sales: sug.sales_amount, vat: sug.output_vat };
            render();
        }

        return { toggleFold: toggleFold, decideRow: decideRow, run: run, apply: apply };
    }

    window.AI = window.AI || {};
    window.AI.intakeBankSales = { create: create };
})();
