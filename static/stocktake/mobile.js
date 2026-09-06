(function () {
    'use strict';
    const host = document.getElementById('stocktake-mobile');
    const languages = document.getElementById('st-lang');
    const workspaces = document.getElementById('st-workspace');
    let lang = localStorage.getItem('pearnly_lang') || 'th';
    if (!window.I18N[lang]) lang = 'th';
    let token = '',
        workspace = '',
        view;
    const t = (key) => window.I18N[lang][key] || key;
    languages.value = lang;
    languages.onchange = () => {
        lang = languages.value;
        localStorage.setItem('pearnly_lang', lang);
        document.documentElement.lang = lang;
        view?.refreshLanguage();
    };
    async function api(path, init = {}) {
        const res = await fetch('/api/cowork/stocktakes' + path, {
            ...init,
            headers: {
                Authorization: 'Bearer ' + token,
                'X-Stocktake-Line': '1',
                'X-Workspace-Client-Id': workspace,
                'Content-Type': 'application/json',
            },
        });
        const data = await res.json();
        if (!res.ok) throw { code: data.detail, status: res.status };
        return data;
    }
    function start() {
        view?.destroy();
        workspace = workspaces.value;
        if (!workspace) {
            host.textContent = t('st-company');
            return;
        }
        view = window.PearnlyStocktake(host, { mobile: true, t, api });
        void view.load();
    }
    workspaces.onchange = start;
    host.textContent = t('st-loading');
    window.lineIntakeLiff
        .boot({
            flow: 'cowork-stocktake',
            configUrl: '/api/cowork-line/intake/liff/config',
            authUrl: '/api/cowork/stocktakes/line/auth',
            tokenKey: 'cowork_stocktake_token',
        })
        .then(async (auth) => {
            token = auth.token;
            const data = await api('/workspaces');
            workspaces.replaceChildren(new Option(t('st-company'), ''));
            for (const row of data.clients) workspaces.add(new Option(row.name, String(row.id)));
            workspaces.hidden = false;
            if (data.clients.length === 1) workspaces.value = String(data.clients[0].id);
            start();
        })
        .catch((err) => {
            host.textContent = t(err.status === 403 ? 'st-error-not_bound' : 'st-failed');
        });
    window.addEventListener('pagehide', () => view?.destroy());
})();
