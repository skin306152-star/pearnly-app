/* Customer address options follow explicit parent selections; never pick the first row. */
(function (root) {
    'use strict';
    var C = root.DXST,
        S = C.S;
    var fields = ['province_id', 'district_id', 'subdistrict_id', 'zipcode_id'];
    var levels = ['provinces', 'districts', 'subdistricts', 'zipcodes'];
    var requests = {};
    var blank = '<option value="">—</option>';

    function clearAfter(index, suffix) {
        fields.slice(index + 1).forEach(function (field) {
            var key = field + suffix;
            S.form[key] = '';
            S.form[field.replace('_id', '_name') + suffix] = '';
            S.geoOptions[key] = [];
            requests[key] = (requests[key] || 0) + 1;
            var el = C.$('dx-f-' + key);
            if (el) {
                el.innerHTML = blank;
                el.value = '';
                el.disabled = false;
            }
        });
        C.syncMirror();
    }

    function onChange(el) {
        var key = el.dataset.fk,
            value = el.value;
        var base = key.replace(/_ct$|_sd$/, ''),
            suffix = key.slice(base.length);
        var index = fields.indexOf(base);
        S.form[key] = value;
        if (index < 0) return C.syncMirror();
        S.form[base.replace('_id', '_name') + suffix] =
            value && el.selectedOptions.length ? el.selectedOptions[0].textContent : '';
        clearAfter(index, suffix);
        if (index === fields.length - 1 || !value) return;
        var targetKey = fields[index + 1] + suffix;
        var token = requests[targetKey];
        var epoch = S.geoEpoch;
        var target = C.$('dx-f-' + targetKey);
        if (target) target.disabled = true;
        var current = function () {
            return S.geoEpoch === epoch && requests[targetKey] === token && S.form[key] === value;
        };
        return fetch(
            '/api/dms/geo?level=' + levels[index + 1] + '&parent_id=' + encodeURIComponent(value),
            { headers: C.authHeaders(), cache: 'no-store' }
        )
            .then(function (r) {
                if (!r.ok) throw new Error('geo unavailable');
                return r.json();
            })
            .then(function (data) {
                if (!current()) return;
                if (!Array.isArray(data.options)) throw new Error('geo unavailable');
                var options = data.options.filter(function (row) {
                    return Array.isArray(row) && row.length > 1 && row[0] != null && String(row[0]);
                });
                S.geoOptions[targetKey] = options;
                target = C.$('dx-f-' + targetKey);
                if (target) {
                    target.innerHTML =
                        blank +
                        options
                            .map(function (row) {
                                return (
                                    '<option value="' +
                                    C.esc(row[0]) +
                                    '">' +
                                    C.esc(row[1]) +
                                    '</option>'
                                );
                            })
                            .join('');
                    target.value = '';
                }
            })
            .catch(function () {
                if (current()) root.showToast(root.t('dx-geo-load-fail'), 'error');
            })
            .then(function () {
                if (current()) {
                    target = C.$('dx-f-' + targetKey);
                    if (target) target.disabled = false;
                    C.syncMirror();
                }
            });
    }

    function missingSelection() {
        if (!S.form.prefix_id) return true;
        return ['', '_ct', '_sd'].some(function (suffix) {
            var values = fields.map(function (field) {
                return S.form[field + suffix];
            });
            return (
                (!suffix || values.some(Boolean)) &&
                values.some(function (value) {
                    return !value;
                })
            );
        });
    }

    root.DXGEO = { onChange: onChange, missingSelection: missingSelection };
})(typeof self !== 'undefined' ? self : this);
