document.addEventListener('DOMContentLoaded', function() {
    const overdueElements = document.querySelectorAll('.badge-overdue');
    overdueElements.forEach(function(el) {
        const row = el.closest('tr');
        if (row) {
            row.style.backgroundColor = 'rgba(255, 107, 107, 0.1)';
        }
    });

    const tenantSelect = document.getElementById('tenantLedgerTenantSelect');
    if (tenantSelect) {
        tenantSelect.addEventListener('change', function() {
            if (this.value) {
                window.location.href = this.value;
            }
        });
    }

    const printButton = document.getElementById('printLedgerButton');
    if (printButton) {
        printButton.addEventListener('click', function() {
            document.body.classList.add('ledger-printing');
            window.print();
        });
    }

    window.addEventListener('afterprint', function() {
        document.body.classList.remove('ledger-printing');
    });
});
