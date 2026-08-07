/*
 * Pearnly AI · ai-steward-history-sync.js · 会话历史拉取(拆自 ai-steward.js · 单文件<500 铁律)
 *
 * 两条路都是"服务端消息流是权威的,补拉进本地 S":
 *   sync(opts)     回到本页 / 切会话 / 任务收尾时重建一次(afterSwitch 见下)
 *   loadEarlier()  手动往前翻一页,滚动位置钉在原地
 *
 * 工厂注入钩子,零模块级状态 —— 状态全落 ai-steward.js 的 S(单一事实源),本层
 * 只读写注入的那份(同 ai-steward-tasks.js/ai-steward-sessions.js 先例)。
 *
 * hooks 契约:
 *   state()            → S(读写 messages/hasMore/historyLoading/historyErr/
 *                        loadingEarlier/busy/sessionId/taskId)
 *   getEl(id)          → element|null(loadEarlier 读 stwFeedWrap 钉滚动位)
 *   renderFeed()       重画消息流
 *   renderTitle()      重画会话标题(sync 成功后标题可能随首句落定)
 *   backfill()         历史轮过程条按需补拉(ai-steward-tasks.js)
 *   loadTask(tid,opts) 拉单条任务投影(ai-steward-tasks.js)
 *   pending()          → 命令条/画像卡 CTA 带来、还没送出的第一句话(非空则 sync 整轮跳过)
 */
(function (root) {
    'use strict';

    function create(hooks) {
        function S() {
            return hooks.state();
        }

        // 服务端的消息流是权威的,回到本页或任务收尾时重建一次;本地只留还没落库的
        // (sending/failed)接在后面。送出在途时整轮跳过,避免与回包抢写。
        //
        // opts.afterSwitch = true:刚 resetTo() 切过来的这次拉取(见 ai-steward.js 的
        // switchSession/newSession)。这次必须让人看得见——resetTo() 已把 S.messages
        // 清空、画出「欢迎屏」空态,那一屏与「这个会话本来就没消息」长得一模一样;
        // 网络慢或这次请求真失败,用户看到的就是「点了历史记录,什么都没有」
        // (2026-08-07 真机复现:桩 2.5s 延迟/500 两种条件,空态原样卡住、catch 不留
        // 痕迹,详见对应 E2E spec)。因此这条路径要:立刻亮一个跟「空会话」区分得开
        // 的骨架屏,失败要落 S.historyErr 出错误态 + 重试(data-action=
        // "stw-history-retry"),不能悄悄吞。后台静默刷新(mount() 回访时那次,
        // afterSwitch 不传)维持老规矩不吵——那份数据早就在屏幕上,一次网络抖动
        // 不该把它换成错误态。
        function sync(opts) {
            var s = S();
            if (!s || !s.sessionId || s.busy || hooks.pending()) return;
            var afterSwitch = !!(opts && opts.afterSwitch);
            var session = s;
            var sid = s.sessionId;
            if (afterSwitch) {
                s.historyLoading = true;
                s.historyErr = false;
                hooks.renderFeed();
            }
            s.api
                .getStewardSession(sid)
                .then(function (resp) {
                    if (S() !== session || S().busy || S().sessionId !== sid) return;
                    S().historyLoading = false;
                    if (!resp || !Array.isArray(resp.messages)) {
                        // 200 但契约漂了:切会话场景不能装作"这个会话真的没消息"。
                        if (afterSwitch) S().historyErr = true;
                        hooks.renderFeed();
                        return;
                    }
                    S().messages = resp.messages.concat(
                        S().messages.filter(function (m) {
                            return m.state === 'sending' || m.state === 'failed';
                        })
                    );
                    S().hasMore = !!resp.has_more;
                    hooks.renderFeed();
                    hooks.renderTitle();
                    hooks.backfill();
                    if (resp.current_task_id && !S().taskId) {
                        hooks.loadTask(resp.current_task_id, { fromSync: true });
                    }
                })
                .catch(function () {
                    if (S() !== session || S().busy || S().sessionId !== sid) return;
                    S().historyLoading = false;
                    // 切会话触发的这次失败必须露脸(见上方函数注释);后台静默刷新
                    // 那份数据本来就在屏幕上,一次抖动不动它,老规矩不变。
                    if (afterSwitch) {
                        S().historyErr = true;
                        hooks.renderFeed();
                    }
                });
        }

        // 更早一页接在顶上,滚动位置钉在原地(不接住的话内容一插,读的那行就飞了)。
        function loadEarlier() {
            var s = S();
            var oldest = s.messages.filter(function (m) {
                return m.id;
            })[0];
            if (!s.sessionId || !oldest || s.loadingEarlier) return;
            s.loadingEarlier = true;
            hooks.renderFeed();
            var session = s;
            s.api
                .getStewardSession(s.sessionId, { before: oldest.id })
                .then(function (resp) {
                    if (S() !== session) return;
                    S().loadingEarlier = false;
                    if (!resp || !Array.isArray(resp.messages)) {
                        hooks.renderFeed();
                        return;
                    }
                    var wrap = hooks.getEl('stwFeedWrap');
                    var bottomGap = wrap ? wrap.scrollHeight - wrap.scrollTop : 0;
                    S().messages = resp.messages.concat(S().messages);
                    S().hasMore = !!resp.has_more;
                    hooks.renderFeed();
                    if (wrap) wrap.scrollTop = wrap.scrollHeight - bottomGap;
                    hooks.backfill();
                })
                .catch(function () {
                    if (S() !== session) return;
                    S().loadingEarlier = false;
                    hooks.renderFeed();
                });
        }

        return { sync: sync, loadEarlier: loadEarlier };
    }

    var api = { create: create };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.stewardHistorySync = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
