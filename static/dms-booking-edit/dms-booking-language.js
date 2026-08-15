(function () {
    'use strict';

    function mergeRef(previous, id) {
        return Object.assign({}, previous, { id: id });
    }

    function snapshot(form, current) {
        var previous = form.answers || {};
        return Object.assign({}, form, {
            customer: current.customer,
            payments: current.payments,
            files: {
                id_card: current.keep_files.id_card,
                slip: current.keep_files.slip,
            },
            answers: {
                place: mergeRef(previous.place, current.answers.place_id),
                car: mergeRef(previous.car, current.answers.car_id),
                paint: mergeRef(previous.paint, current.answers.paint_id),
                delivery_date_be: current.answers.delivery_date_be,
                term: mergeRef(previous.term, current.answers.term_id),
                regis: mergeRef(previous.regis, current.answers.regis_id),
                regis_name: current.answers.regis_name,
            },
        });
    }

    window.DmsBookingLanguage = { snapshot: snapshot };
})();
