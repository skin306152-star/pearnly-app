(function () {
    'use strict';

    function esc(value) {
        var node = document.createElement('div');
        node.textContent = value == null ? '' : String(value);
        return node.innerHTML;
    }

    function hydrate(form, previewLabel, failedLabel) {
        form.querySelectorAll('[data-preview]').forEach(function (element) {
            var token = sessionStorage.getItem('erp_line_token');
            fetch(element.dataset.preview, {
                headers: token ? { Authorization: 'Bearer ' + token } : {},
            })
                .then(function (response) {
                    if (!response.ok) throw Error('preview');
                    return response.blob();
                })
                .then(function (blob) {
                    var url = URL.createObjectURL(blob);
                    element.innerHTML =
                        '<a href="' +
                        url +
                        '" target="_blank" rel="noopener"><img class="preview" src="' +
                        url +
                        '" alt="' +
                        esc(previewLabel) +
                        '"></a>';
                })
                .catch(function () {
                    element.textContent = failedLabel;
                });
        });
    }

    window.erpLinePreviews = { hydrate: hydrate };
})();
