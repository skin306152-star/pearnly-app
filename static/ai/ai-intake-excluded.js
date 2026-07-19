/* Pearnly AI · 排除件改判编排。 */
(function (root) {
    'use strict';

    function decisionPayload(itemId, kind) {
        if (!itemId || !kind) return null;
        return { item_id: itemId, decision: 'assign_kind', kind: kind };
    }

    var pure = { decisionPayload: decisionPayload };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;
    if (!root) return;

    function create(getState, render, refresh) {
        var busy = {};
        var errors = {};

        function context() {
            var state = getState();
            return {
                excluded: (state.order && state.order.excluded) || [],
                excludedBusy: busy,
                excludedErr: errors,
            };
        }

        function reassign(select) {
            var itemId = select.getAttribute('data-item-id');
            var payload = decisionPayload(itemId, select.value);
            if (!payload || busy[itemId]) return;
            busy[itemId] = true;
            delete errors[itemId];
            render();
            var state = getState();
            state.api
                .decide(state.orderId, payload)
                .then(refresh)
                .catch(function () {
                    delete busy[itemId];
                    errors[itemId] = true;
                    render();
                });
        }

        function onChange(event) {
            var target = event.target;
            var select = target.closest && target.closest('[data-action="ik-excluded-assign"]');
            if (select) reassign(select);
        }

        return { context: context, onChange: onChange };
    }

    root.AI = root.AI || {};
    root.AI.intakeExcluded = Object.assign({ create: create }, pure);
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
