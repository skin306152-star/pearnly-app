/* Pearnly scanner success visual: fire-and-forget product feedback shared by all scan flows. */
(function (root) {
    'use strict';

    var doc = root && root.document;
    var serial = 0;
    var MOTION_KEY = 'pearnly_scan_motion';
    var BOX_ICON =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M21 8 12 3 3 8l9 5 9-5"/><path d="M3 8v8l9 5 9-5V8M12 13v8"/></svg>';
    var CHECK_ICON =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="m6 12 4 4 8-9"/></svg>';
    var TORCH_ICON =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="m9 2 6 0 1 5-8 0 1-5Z"/><path d="m8 7 2 4v10h4V11l2-4"/><path d="M10 15h4"/></svg>';

    function motionEnabled() {
        try {
            return root.localStorage.getItem(MOTION_KEY) !== '0';
        } catch {
            return true;
        }
    }

    function setMotionEnabled(enabled) {
        try {
            root.localStorage.setItem(MOTION_KEY, enabled ? '1' : '0');
        } catch {}
    }

    function translated(t, key, fallback) {
        if (typeof t !== 'function') return fallback;
        try {
            var value = t(key);
            return value && value !== key ? value : fallback;
        } catch {
            return fallback;
        }
    }

    function usableRect(el) {
        if (!el || typeof el.getBoundingClientRect !== 'function') return null;
        var rect = el.getBoundingClientRect();
        return rect && rect.width > 0 && rect.height > 0 ? rect : null;
    }

    function targetRect(target) {
        var choices = Array.isArray(target) ? target : [target];
        for (var i = 0; i < choices.length; i++) {
            var candidate = choices[i];
            if (typeof candidate === 'string' && doc) candidate = doc.querySelector(candidate);
            var rect = usableRect(candidate);
            if (rect) return rect;
        }
        return null;
    }

    function remove(el) {
        if (el && el.parentNode) el.parentNode.removeChild(el);
    }

    function setImage(card, img, imageUrl, loadImage) {
        if (!imageUrl) return;
        img.addEventListener(
            'load',
            function () {
                card.classList.add('has-image');
            },
            { once: true }
        );
        img.addEventListener(
            'error',
            function () {
                card.classList.remove('has-image');
            },
            { once: true }
        );
        try {
            var loading =
                typeof loadImage === 'function'
                    ? loadImage(img, imageUrl)
                    : ((img.src = imageUrl), null);
            if (loading && typeof loading.catch === 'function') loading.catch(function () {});
        } catch {
            card.classList.remove('has-image');
        }
    }

    function show(opts) {
        if (!doc || !doc.body || !opts || !motionEnabled()) return false;
        var width = Math.max(1, root.innerWidth || doc.documentElement.clientWidth || 1);
        var height = Math.max(1, root.innerHeight || doc.documentElement.clientHeight || 1);
        var target = targetRect(opts.target);
        var startX = width / 2 + ((serial++ % 3) - 1) * 18;
        var startY = Math.max(110, height * 0.46);
        var endX = target ? target.left + target.width / 2 : width / 2;
        var endY = target ? target.top + target.height / 2 : height - 72;

        var card = doc.createElement('div');
        card.className = 'scan-success-fly';
        card.setAttribute('aria-hidden', 'true');
        card.setAttribute('data-scan-success-fly', '');
        card.style.left = startX + 'px';
        card.style.top = startY + 'px';
        card.style.setProperty('--scan-fly-x', endX - startX + 'px');
        card.style.setProperty('--scan-fly-y', endY - startY + 'px');

        var thumb = doc.createElement('span');
        thumb.className = 'scan-success-thumb';
        var fallback = doc.createElement('span');
        fallback.className = 'scan-success-placeholder';
        fallback.innerHTML = BOX_ICON;
        var img = doc.createElement('img');
        img.alt = '';
        thumb.appendChild(fallback);
        thumb.appendChild(img);
        var check = doc.createElement('span');
        check.className = 'scan-success-check';
        check.innerHTML = CHECK_ICON;
        thumb.appendChild(check);
        card.appendChild(thumb);

        var caption = doc.createElement('span');
        caption.className = 'scan-success-caption';
        var name = doc.createElement('span');
        name.className = 'scan-success-name';
        name.textContent = String(opts.label || '');
        caption.appendChild(name);
        if (opts.increment !== false) {
            var amount = doc.createElement('span');
            amount.className = 'scan-success-amount';
            amount.textContent = '+1';
            caption.appendChild(amount);
        }
        card.appendChild(caption);

        var ring = doc.createElement('span');
        ring.className = 'scan-success-ring';
        ring.setAttribute('aria-hidden', 'true');
        ring.setAttribute('data-scan-success-ring', '');
        ring.style.left = endX + 'px';
        ring.style.top = endY + 'px';

        doc.body.appendChild(card);
        doc.body.appendChild(ring);
        setImage(card, img, opts.imageUrl, opts.loadImage);

        card.addEventListener(
            'animationend',
            function () {
                remove(card);
            },
            { once: true }
        );
        ring.addEventListener(
            'animationend',
            function () {
                remove(ring);
            },
            { once: true }
        );
        root.setTimeout(function () {
            remove(card);
            remove(ring);
        }, 1100);
        return true;
    }

    function mountControls(opts) {
        if (!doc || !opts || !opts.container || !opts.camera) return null;
        var container = opts.container;
        var camera = opts.camera;
        var t = opts.t;
        var controls = doc.createElement('div');
        controls.className = 'scan-view-controls';
        controls.setAttribute('data-scan-view-controls', '');

        var torch = doc.createElement('button');
        torch.type = 'button';
        torch.className = 'scan-view-torch';
        torch.innerHTML = TORCH_ICON;
        torch.hidden = true;
        torch.setAttribute('aria-pressed', 'false');
        controls.appendChild(torch);

        var motion = doc.createElement('label');
        motion.className = 'scan-view-motion';
        var checkbox = doc.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = motionEnabled();
        checkbox.setAttribute('data-scan-motion-toggle', '');
        checkbox.addEventListener('change', function () {
            setMotionEnabled(checkbox.checked);
        });
        var motionText = doc.createElement('span');
        motionText.textContent = translated(t, 'scan-controls.animation', 'Scan animation');
        motion.appendChild(checkbox);
        motion.appendChild(motionText);
        controls.appendChild(motion);
        container.appendChild(controls);

        function cameraControl(name, value) {
            if (typeof camera.cameraControl !== 'function') return false;
            return camera.cameraControl(name, value);
        }

        function paintTorch() {
            var available = cameraControl('torchAvailable');
            torch.hidden = !available;
            if (!available) return false;
            var on = cameraControl('torchEnabled');
            var label = translated(
                t,
                on ? 'scan-controls.torch-off' : 'scan-controls.torch-on',
                on ? 'Turn flashlight off' : 'Turn flashlight on'
            );
            torch.setAttribute('aria-pressed', on ? 'true' : 'false');
            torch.setAttribute('aria-label', label);
            torch.title = label;
            return true;
        }

        torch.addEventListener('click', function () {
            if (torch.disabled) return;
            var next = !cameraControl('torchEnabled');
            torch.disabled = true;
            Promise.resolve(cameraControl('setTorch', next)).then(
                function (ok) {
                    torch.disabled = false;
                    if (ok === false && !cameraControl('torchAvailable')) torch.hidden = true;
                    else paintTorch();
                },
                function () {
                    torch.disabled = false;
                    paintTorch();
                }
            );
        });
        paintTorch();

        return {
            refreshTorch: paintTorch,
            destroy: function () {
                remove(controls);
            },
        };
    }

    var api = {
        show: show,
        motionEnabled: motionEnabled,
        setMotionEnabled: setMotionEnabled,
        mountControls: mountControls,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) root.PearnlyScanSuccessVisual = api;
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
