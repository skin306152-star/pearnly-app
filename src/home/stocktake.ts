import '../../static/stocktake/ui.js';
import '../../static/stocktake/stocktake.css';

const w = window as any;
const host = document.getElementById('page-stocktake')!;
let view: any;
const base = '/api/cowork/stocktakes';
function headers() {
    return { Authorization: 'Bearer ' + w.session.getToken(), ...w._wsHeader() };
}
async function request(path: string, init: RequestInit = {}) {
    const res = await fetch(base + path, {
        ...init,
        headers: {
            ...headers(),
            ...(init.body && !(init.body instanceof FormData)
                ? { 'Content-Type': 'application/json' }
                : {}),
        },
    });
    if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw { code: data.detail, status: res.status };
    }
    return res;
}
w.loadStocktake = function () {
    view?.destroy();
    if (!w.getActiveWorkspaceClientId()) {
        host.innerHTML = w.wsEmptyHtml('st-choose-ws');
        host.querySelector('button')!.onclick = () => w.openWorkspaceChooser();
        return;
    }
    view = w.PearnlyStocktake(host, {
        t: (key: string) => w.t(key),
        api: async (path: string, init?: RequestInit) => (await request(path, init)).json(),
        download: async (path: string, name: string) => {
            const lang = w._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
            const blob = await (await request(path + '?lang=' + encodeURIComponent(lang))).blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = name;
            a.click();
            setTimeout(() => URL.revokeObjectURL(url), 1000);
        },
    });
    void view.load();
};
window.addEventListener('hashchange', () => {
    if (location.hash !== '#/stocktake') view?.destroy();
});
window.addEventListener('pagehide', () => view?.destroy());
w.subscribeI18n?.('stocktake', () => {
    if (location.hash === '#/stocktake') view?.refreshLanguage();
});
