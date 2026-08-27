(function () {
    'use strict';
    var root = document.getElementById('discard-dialog');
    var title = root.querySelector('#discard-dialog-title');
    var cancelButtons = root.querySelectorAll('[data-dialog-cancel]');
    var confirmButton = root.querySelector('[data-dialog-confirm]');
    var previousFocus;
    var onConfirm;
    var confirmEvent;
    var confirmTarget;
    function close() {
        root.hidden = true;
        root.setAttribute('aria-hidden', 'true');
        document.removeEventListener('keydown', onKeydown);
        if (previousFocus) previousFocus.focus();
    }
    function onKeydown(event) {
        if (event.key === 'Escape') close();
    }
    cancelButtons.forEach(function (button) {
        button.addEventListener('click', close);
    });
    confirmButton.addEventListener('click', function () {
        var callback = onConfirm;
        var event = confirmEvent;
        close();
        if (callback) callback({ currentTarget: confirmTarget || event, confirmed: true });
    });
    window.erpDiscardDialog = {
        open: function (message, cancelLabel, confirmLabel, event, callback) {
            previousFocus = document.activeElement;
            onConfirm = callback;
            confirmEvent = event;
            confirmTarget = event && event.currentTarget;
            title.textContent = message;
            cancelButtons[1].textContent = cancelLabel;
            confirmButton.textContent = confirmLabel;
            root.hidden = false;
            root.setAttribute('aria-hidden', 'false');
            confirmButton.focus();
            document.addEventListener('keydown', onKeydown);
        },
    };
})();
