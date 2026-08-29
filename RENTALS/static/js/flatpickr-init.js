// Flatpickr initialization for all date inputs with modern UI
// Requires flatpickr to be loaded globally

document.addEventListener('DOMContentLoaded', function() {
    if (window.flatpickr) {
        const initialized = new Set();

        // Detect and initialize paired date ranges (start_date / end_date)
        // regardless of class or type attribute
        document.querySelectorAll('input[name="start_date"], input[name="startDate"]').forEach(function(input) {
            if (initialized.has(input)) return;
            const form = input.closest('form');
            if (!form) return;
            const pair = form.querySelector('input[name="end_date"], input[name="endDate"]');
            if (pair && !initialized.has(pair)) {
                flatpickr(input, {
                    dateFormat: 'Y-m-d',
                    allowInput: true,
                    altInput: true,
                    altFormat: 'M j, Y',
                    appendTo: document.body,
                    disableMobile: true,
                    animate: true,
                    monthSelectorType: 'dropdown',
                    static: true,
                    onChange: function(selectedDates) {
                        if (selectedDates.length > 0) {
                            pair._flatpickr.set('minDate', selectedDates[0]);
                        }
                    },
                });
                flatpickr(pair, {
                    dateFormat: 'Y-m-d',
                    allowInput: true,
                    altInput: true,
                    altFormat: 'M j, Y',
                    appendTo: document.body,
                    disableMobile: true,
                    animate: true,
                    monthSelectorType: 'dropdown',
                    static: true,
                    onChange: function(selectedDates) {
                        if (selectedDates.length > 0) {
                            input._flatpickr.set('maxDate', selectedDates[0]);
                        }
                    },
                });
                initialized.add(input);
                initialized.add(pair);
            }
        });

        // Initialize standalone datepicker inputs (.datepicker class, not part of a range)
        document.querySelectorAll('input.datepicker').forEach(function(input) {
            if (initialized.has(input)) return;
            const name = input.getAttribute('name');
            if (name !== 'start_date' && name !== 'startDate' && name !== 'end_date' && name !== 'endDate') {
                flatpickr(input, {
                    dateFormat: 'Y-m-d',
                    allowInput: true,
                    altInput: true,
                    altFormat: 'M j, Y',
                    appendTo: document.body,
                    disableMobile: true,
                    animate: true,
                    monthSelectorType: 'dropdown',
                    static: true,
                });
                initialized.add(input);
            }
        });

        // Initialize native date inputs that haven't been initialized yet
        document.querySelectorAll('input[type="date"]:not(.flatpickr-input)').forEach(function(input) {
            if (initialized.has(input)) return;
            flatpickr(input, {
                dateFormat: 'Y-m-d',
                allowInput: true,
                altInput: true,
                altFormat: 'M j, Y',
                appendTo: document.body,
                disableMobile: true,
                animate: true,
                monthSelectorType: 'dropdown',
                static: true,
            });
            initialized.add(input);
        });
    }
});
