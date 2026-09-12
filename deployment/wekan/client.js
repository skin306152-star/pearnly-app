/* Authenticate the native Meteor connection using its gateway-bound identity. */
/* global window, document, setTimeout */
(() => {
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
    const deadline = Date.now() + 30000;
    function start() {
        const Accounts = window.Package?.['accounts-base']?.Accounts;
        if (!Accounts || !window.Meteor) {
            if (Date.now() < deadline) return setTimeout(start, 50);
            return;
        }
        window.Meteor.startup(() => {
            Accounts.callLoginMethod({
                methodArguments: [{ pearnly: true }],
                userCallback(error) {
                    if (!error) return;
                    const message = document.createElement('p');
                    message.setAttribute('role', 'alert');
                    message.textContent = 'กรุณากลับไปที่ COWORK แล้วเปิดการทำงานร่วมกันอีกครั้ง';
                    document.body.prepend(message);
                },
            });
        });
    }
    start();
})();
