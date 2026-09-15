/* Authenticate the native Meteor connection using its gateway-bound identity. */
/* global window, document, setTimeout, MutationObserver */
(() => {
    const PRODUCT_NAME = 'Pearnly';
    // The stock name, in the two spellings the native layout and title use.
    const STOCK_NAMES = ['WeKan', 'Wekan'];

    // Until this runs, branding.css keeps the native UI invisible behind the
    // Pearnly boot cover. Revealing is therefore the LAST step of a successful
    // entry, and also the first step of every failure - a cover that never
    // lifted would be worse than the flash it removes.
    function reveal() {
        document.documentElement.classList.add('pearnly-ready');
    }

    // The tab title and the two "app name" metas are hardcoded in the native
    // layout, so the native `productName` setting cannot reach them. Rewrite
    // them rather than leaving the upstream name in the tab or on a phone's
    // home screen.
    function renameTitle() {
        const title = document.querySelector('head > title');
        if (!title) return;
        const next = title.textContent
            .split(' - ')
            .map((part) => (STOCK_NAMES.includes(part.trim()) ? PRODUCT_NAME : part))
            .join(' - ');
        if (next !== title.textContent) title.textContent = next;
    }

    function renameMetaTags() {
        for (const name of ['application-name', 'apple-mobile-web-app-title']) {
            const meta = document.querySelector(`meta[name="${name}"]`);
            if (meta && STOCK_NAMES.includes(meta.getAttribute('content'))) {
                meta.setAttribute('content', PRODUCT_NAME);
            }
        }
    }

    function applyBranding() {
        renameTitle();
        renameMetaTags();
    }

    function watchBranding() {
        applyBranding();
        // Blaze re-renders the title on every navigation, and the layout can
        // arrive after this script, so follow the head instead of assuming
        // either order.
        const observer = new MutationObserver(applyBranding);
        observer.observe(document.head, { childList: true, subtree: true, characterData: true });
        for (const name of ['application-name', 'apple-mobile-web-app-title']) {
            const meta = document.querySelector(`meta[name="${name}"]`);
            if (meta) observer.observe(meta, { attributes: true, attributeFilter: ['content'] });
        }
    }

    // Native AccountsTemplates redirects immediately after logout. Own this
    // button's navigation so the gateway session is revoked before leaving.
    document.addEventListener(
        'click',
        (event) => {
            if (!event.target.closest?.('a.js-logout')) return;
            event.preventDefault();
            event.stopImmediatePropagation();
            async function finish() {
                try {
                    const response = await window.fetch('/_pearnly/logout', {
                        method: 'POST',
                        headers: { Accept: 'application/json' },
                    });
                    if (!response.ok) throw new Error('logout unavailable');
                    window.location.assign((await response.json()).url);
                } catch {
                    const message = document.createElement('p');
                    message.setAttribute('role', 'alert');
                    message.textContent = 'ออกจากระบบไม่สำเร็จ กรุณาลองอีกครั้ง';
                    document.body.prepend(message);
                }
            }
            // Meteor.logout invalidates its HTTP token before native reactive
            // navigation finishes. Revoke the gateway session instead: this
            // closes DDP and expires both gateway and native HTTP cookies.
            // A native token alone cannot pass the gateway identity checks.
            finish();
        },
        true
    );

    watchBranding();

    const deadline = Date.now() + 30000;
    function start() {
        const Accounts = window.Package?.['accounts-base']?.Accounts;
        if (!Accounts || !window.Meteor) {
            if (Date.now() < deadline) return setTimeout(start, 50);
            reveal();
            return;
        }
        window.Meteor.startup(() => {
            Accounts.callLoginMethod({
                methodArguments: [{ pearnly: true }],
                userCallback(error) {
                    if (!error) {
                        applyBranding();
                        reveal();
                        return;
                    }
                    const message = document.createElement('p');
                    message.setAttribute('role', 'alert');
                    message.textContent = 'กรุณากลับไปที่ COWORK แล้วเปิดการทำงานร่วมกันอีกครั้ง';
                    document.body.prepend(message);
                    reveal();
                },
            });
        });
    }
    start();
})();
