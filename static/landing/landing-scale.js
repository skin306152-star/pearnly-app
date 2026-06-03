(function () {
    const root = document.getElementById('pearnly-auth-root');
    const stage = () => document.querySelector('.auth-stage');
    const baseWidth = 1402;
    const baseHeight = 1122;
    const mobileWidth = 760;

    function applyStageScale() {
        const target = stage();
        if (!root || !target) return;
        if (window.innerWidth <= mobileWidth) {
            root.style.removeProperty('--stage-scale');
            root.style.removeProperty('height');
            root.classList.add('mobile-layout');
            return;
        }
        const scale =
            window.innerWidth >= baseWidth - 4
                ? 1
                : Math.min(1, Math.max(0.58, (window.innerWidth - 28) / baseWidth));
        root.classList.remove('mobile-layout');
        root.style.setProperty('--stage-scale', scale.toFixed(4));
        root.style.height = `${Math.ceil(baseHeight * scale) + 28}px`;
    }

    window.PearnlyApplyStageScale = applyStageScale;
    window.addEventListener('resize', applyStageScale);
    window.addEventListener('orientationchange', applyStageScale);
    window.requestAnimationFrame(applyStageScale);
})();
