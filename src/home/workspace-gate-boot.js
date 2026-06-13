import { ONB_CSS } from './onboarding-flow-html.js';

(function () {
    'use strict';

    function injectBootStyle(id, css) {
        if (document.getElementById(id)) return;
        const st = document.createElement('style');
        st.id = id;
        st.textContent = css;
        document.head.appendChild(st);
    }

    function mountBootGate() {
        if (window.PEARNLY_ADMIN_LAYOUT || window.PEARNLY_ADMIN_MODE) return;
        if (document.getElementById('onboarding-flow-root')) return;

        window.__workspaceGateBootPending = true;
        document.body.classList.add('workspace-gate-preboot');
        injectBootStyle('onb-flow-css', ONB_CSS);
        if (!document.getElementById('wsg-static-css')) {
            injectBootStyle(
                'wsg-boot-css',
                '.wsg-boot-spin{width:28px;height:28px;border-radius:50%;border:3px solid var(--line);border-top-color:var(--ink);animation:wsgBootSpin .8s linear infinite}@keyframes wsgBootSpin{to{transform:rotate(360deg)}}'
            );
        }

        let el = document.getElementById('workspace-gate-root');
        if (!el) {
            el = document.createElement('div');
            el.id = 'workspace-gate-root';
            el.className = 'onb-root';
            el.dataset.wsgBoot = '1';
            el.style.cssText = 'display:grid;place-items:center;';
            el.innerHTML = '<div class="wsg-boot-spin" aria-hidden="true"></div>';
            document.body.appendChild(el);
        }
    }

    window.showWorkspaceGate = mountBootGate;
    window.enforceWorkspaceGate = mountBootGate;
})();
