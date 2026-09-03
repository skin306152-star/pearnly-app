/* Product names are master data and stay unchanged when the POS interface language changes. */
(function () {
    const POS = window.POS;

    POS.pnm = function (value) {
        if (!value || typeof value === 'string') return value || '';
        if (value.display) return value.display;
        const names = [value.th, value.en, value.zh, value.ja].map((name) =>
            String(name || '').trim()
        );
        const firstIndex = (name) =>
            names.findIndex(
                (candidate) => candidate.toLocaleLowerCase() === name.toLocaleLowerCase()
            );
        return names.filter((name, index) => name && firstIndex(name) === index).join(' / ');
    };
})();
