(function () {
    'use strict';

    var TEXT = window.DMS_CREDENTIALS_TEXT;
    var gateway;
    var locale = 'th';
    var closePage;
    var form = document.getElementById('editor');
    var result = document.getElementById('result');

    function t(key) {
        return (TEXT[locale] && TEXT[locale][key]) || TEXT.en[key] || key;
    }

    function esc(value) {
        var node = document.createElement('div');
        node.textContent = value == null ? '' : String(value);
        return node.innerHTML;
    }

    function translate() {
        document.documentElement.lang = locale;
        document.querySelectorAll('[data-credentials-text]').forEach(function (node) {
            node.textContent = t(node.dataset.credentialsText);
        });
        document.querySelectorAll('[data-credentials-placeholder]').forEach(function (node) {
            node.placeholder = t(node.dataset.credentialsPlaceholder);
        });
    }

    function errorKey(error) {
        var code = error && error.code;
        if (code === 'dms_booking.not_bound') return 'bindingChanged';
        if (code === 'dms_credentials.operator_inactive' || code === 'auth.account_disabled')
            return 'operatorInactive';
        if (code === 'dms_booking.line_auth_required' || (error && error.status === 401))
            return 'lineAuthRequired';
        if (code === 'dms_credentials.endpoint_missing') return 'endpointMissing';
        if (code === 'dms_credentials.unavailable') return 'unavailable';
        return 'failed';
    }

    async function request(path, options) {
        // Never switch identity and replay a form submitted by the old identity.
        return gateway.api(path, options);
    }

    function render(username) {
        document.getElementById('loading').hidden = true;
        result.hidden = true;
        result.innerHTML = '';
        form.hidden = false;
        form.className = 'editor credentials-editor';
        form.innerHTML =
            '<div class="intro"><h1 data-credentials-text="title"></h1>' +
            '<p data-credentials-text="subtitle"></p></div>' +
            '<section class="section credentials-card"><div class="credentials-grid">' +
            '<div class="field"><label for="credentials-username" data-credentials-text="username"></label>' +
            '<input id="credentials-username" name="username" autocomplete="username" maxlength="120" value="' +
            esc(username) +
            '" data-credentials-placeholder="usernamePlaceholder"></div>' +
            '<div class="field"><label for="credentials-password" data-credentials-text="password"></label>' +
            '<input id="credentials-password" name="password" type="password" autocomplete="new-password" maxlength="256" data-credentials-placeholder="passwordPlaceholder"></div>' +
            '<div class="field"><label for="credentials-confirm" data-credentials-text="confirm"></label>' +
            '<input id="credentials-confirm" name="confirm" type="password" autocomplete="new-password" maxlength="256" data-credentials-placeholder="confirmPlaceholder"></div>' +
            '</div><p class="credentials-note" data-credentials-text="note"></p>' +
            '<p id="credentials-error" class="error" role="alert" aria-live="assertive"></p></section>' +
            '<div class="sticky-actions"><button class="pu-btn secondary" id="credentials-cancel" type="button" data-credentials-text="cancel"></button>' +
            '<button class="pu-btn primary" id="credentials-save" type="submit" data-credentials-text="save"></button></div>';
        form.onsubmit = save;
        document.getElementById('credentials-cancel').onclick = closePage;
        ['credentials-username', 'credentials-password', 'credentials-confirm'].forEach(
            function (id) {
                document.getElementById(id).addEventListener('input', function () {
                    document.getElementById('credentials-error').textContent = '';
                });
            }
        );
        translate();
        document.getElementById('credentials-username').focus();
    }

    function retryButton(key) {
        var button = document.createElement('button');
        button.id = 'credentials-retry';
        button.type = 'button';
        button.className = 'pu-btn primary credentials-done';
        button.dataset.credentialsText =
            key === 'lineAuthRequired' || key === 'bindingChanged' ? 'reconnect' : 'retry';
        button.onclick = function () {
            form.reset();
            form.innerHTML = '';
            mount(
                { gateway: gateway, locale: locale, close: closePage },
                key === 'lineAuthRequired' || key === 'bindingChanged'
            );
        };
        return button;
    }

    function showLoadError(key) {
        document.getElementById('loading').hidden = true;
        form.hidden = true;
        result.hidden = false;
        result.innerHTML =
            '<h1 data-credentials-text="' + (key === 'failed' ? 'loadFailed' : key) + '"></h1>';
        result.appendChild(retryButton(key));
        translate();
    }

    async function save(event) {
        event.preventDefault();
        var username = document.getElementById('credentials-username').value.trim();
        var password = document.getElementById('credentials-password').value;
        var confirm = document.getElementById('credentials-confirm').value;
        var errorNode = document.getElementById('credentials-error');
        if (!username || !password) {
            errorNode.textContent = t('required');
            return;
        }
        if (password !== confirm) {
            errorNode.textContent = t('mismatch');
            document.getElementById('credentials-confirm').focus();
            return;
        }
        errorNode.textContent = '';
        var button = document.getElementById('credentials-save');
        button.disabled = true;
        try {
            await request('/api/line/dms-credentials', {
                method: 'PUT',
                body: JSON.stringify({ username: username, password: password }),
            });
            form.reset();
            form.hidden = true;
            result.hidden = false;
            result.innerHTML =
                '<h1 data-credentials-text="saved"></h1><p data-credentials-text="savedDetail"></p>' +
                '<button class="pu-btn primary credentials-done" id="credentials-done" type="button" data-credentials-text="done"></button>';
            document.getElementById('credentials-done').onclick = closePage;
            translate();
        } catch (error) {
            button.disabled = false;
            var key = errorKey(error);
            errorNode.textContent = t(key);
            if (key === 'bindingChanged' || key === 'lineAuthRequired') {
                button.disabled = true;
                var retry = document.getElementById('credentials-retry');
                if (!retry) errorNode.parentNode.appendChild(retryButton(key));
                translate();
            }
        }
    }

    async function mount(options, forceLogin) {
        gateway = options.gateway;
        locale = options.locale || 'th';
        closePage = options.close;
        form.hidden = true;
        result.hidden = true;
        document.getElementById('loading').hidden = false;
        document.getElementById('loading').querySelector('p').textContent = t('loading');
        try {
            await gateway.authenticate(forceLogin);
            var data = await request('/api/line/dms-credentials');
            render(data.username || '');
        } catch (error) {
            showLoadError(errorKey(error));
        }
    }

    window.DmsCredentials = {
        mount: mount,
        setLocale: function (nextLocale) {
            locale = nextLocale;
            translate();
        },
    };
})();
