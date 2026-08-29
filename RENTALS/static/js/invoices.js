document.addEventListener('DOMContentLoaded', function() {
    const selectAllInvoices = document.getElementById('selectAllInvoices');
    const deleteSelectedInvoicesBtn = document.getElementById('deleteSelectedInvoicesBtn');
    const attachButtons = document.querySelectorAll('.attachPaymentBtn');
    const paymentSelect = document.getElementById('paymentSelect');
    const attachPaymentBtn = document.getElementById('attachPaymentBtn');
    const attachError = document.getElementById('attachError');
    const amountToApplyInput = document.getElementById('amountToApplyInput');
    const editPaymentsError = document.getElementById('editPaymentsError');
    const editPaymentsSuccess = document.getElementById('editPaymentsSuccess');
    const singleInvoiceForm = document.getElementById('singleInvoiceForm');
    const singleInvoiceProperty = document.getElementById('singleInvoiceProperty');
    const singleInvoiceUnit = document.getElementById('singleInvoiceUnit');
    let currentInvoiceId = null;

    function showElement(element) {
        if (element) {
            element.classList.remove('invoice-hidden');
        }
    }

    function hideElement(element) {
        if (element) {
            element.classList.add('invoice-hidden');
        }
    }

    function setMessage(element, message, visible) {
        if (!element) return;
        element.textContent = message;
        if (visible) {
            showElement(element);
        } else {
            hideElement(element);
        }
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function getCsrfToken() {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfInput ? csrfInput.value : getCookie('csrftoken');
    }

    function setSingleInvoiceUnitPlaceholder(message, disabled = true) {
        if (!singleInvoiceUnit) return;
        singleInvoiceUnit.innerHTML = '';
        const option = document.createElement('option');
        option.value = '';
        option.textContent = message;
        option.selected = true;
        singleInvoiceUnit.appendChild(option);
        singleInvoiceUnit.disabled = disabled;
    }

    function buildPropertyUnitsUrl(propertyId) {
        const template = singleInvoiceForm ? singleInvoiceForm.dataset.unitsUrlTemplate : '';
        return template ? template.replace('/0/', `/${propertyId}/`) : `/invoices/property-units/${propertyId}/`;
    }

    function loadSingleInvoiceUnits(propertyId) {
        if (!propertyId || !singleInvoiceUnit) {
            setSingleInvoiceUnitPlaceholder('Select Property First');
            return;
        }

        setSingleInvoiceUnitPlaceholder('Loading Units...');

        fetch(buildPropertyUnitsUrl(propertyId), {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => response.json())
            .then(data => {
                singleInvoiceUnit.innerHTML = '';

                if (!data.units || !data.units.length) {
                    setSingleInvoiceUnitPlaceholder('No Units Found');
                    return;
                }

                const placeholder = document.createElement('option');
                placeholder.value = '';
                placeholder.textContent = 'Select Unit';
                placeholder.selected = true;
                placeholder.disabled = true;
                singleInvoiceUnit.appendChild(placeholder);

                data.units.forEach(unit => {
                    const option = document.createElement('option');
                    option.value = unit.id;
                    const tenantLabel = unit.tenant ? ` - ${unit.tenant}` : '';
                    option.textContent = `${unit.name}${tenantLabel}`;
                    option.dataset.rentAmount = unit.rent_amount;
                    singleInvoiceUnit.appendChild(option);
                });

                singleInvoiceUnit.disabled = false;
            })
            .catch(() => {
                setSingleInvoiceUnitPlaceholder('Unable To Load Units');
            });
    }

    if (singleInvoiceProperty && singleInvoiceUnit) {
        singleInvoiceProperty.addEventListener('change', function() {
            loadSingleInvoiceUnits(this.value);
        });
    }

    function toggleDeleteInvoicesButton() {
        if (!deleteSelectedInvoicesBtn) return;
        const hasCheckedInvoices = document.querySelectorAll('.invoice-checkbox:checked').length > 0;
        if (hasCheckedInvoices) {
            showElement(deleteSelectedInvoicesBtn);
        } else {
            hideElement(deleteSelectedInvoicesBtn);
        }
    }

    if (selectAllInvoices) {
        selectAllInvoices.addEventListener('change', function() {
            document.querySelectorAll('.invoice-checkbox').forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            toggleDeleteInvoicesButton();
        });
    }

    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('invoice-checkbox')) {
            const invoiceCheckboxes = document.querySelectorAll('.invoice-checkbox');
            const checkedInvoiceCheckboxes = document.querySelectorAll('.invoice-checkbox:checked');
            if (selectAllInvoices) {
                selectAllInvoices.checked = invoiceCheckboxes.length > 0 && invoiceCheckboxes.length === checkedInvoiceCheckboxes.length;
            }
            toggleDeleteInvoicesButton();
        }
    });

    if (deleteSelectedInvoicesBtn) {
        deleteSelectedInvoicesBtn.addEventListener('click', function() {
            const selectedIds = Array.from(document.querySelectorAll('.invoice-checkbox:checked')).map(checkbox => checkbox.value);
            if (!selectedIds.length) return;
            if (!confirm(`Delete ${selectedIds.length} invoice(s)?`)) return;
            if (!window.downloadSelectedRowsBeforeDelete('.invoice-checkbox:checked', 'invoices-before-delete')) return;

            const formData = new FormData();
            selectedIds.forEach(id => formData.append('invoice_ids[]', id));

            fetch('/invoices/delete/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert(data.message || 'Failed to delete invoices');
                    }
                })
                .catch(() => {
                    alert('Error deleting invoices');
                });
        });
    }

    attachButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            currentInvoiceId = this.getAttribute('data-invoice-id');
            loadInvoicePayments(currentInvoiceId);
        });
    });

    function loadInvoicePayments(invoiceId) {
        fetch(`/invoices/get-payments/?invoice_id=${invoiceId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('invoiceNumber').textContent = data.invoice_number;
                    document.getElementById('invoiceAmount').textContent = `KES ${data.invoice_amount}`;
                    document.getElementById('amountPaid').textContent = `KES ${data.amount_paid}`;
                    document.getElementById('amountDue').textContent = `KES ${data.remaining_balance}`;

                    document.getElementById('amountRemainingDisplay').textContent = data.remaining_balance.toFixed(2);
                    document.getElementById('amountRemainingHint').textContent = `Total: KES ${data.invoice_amount.toFixed(2)} - Paid: KES ${data.amount_paid.toFixed(2)} = Remaining: KES ${data.remaining_balance.toFixed(2)}`;

                    paymentSelect.innerHTML = '<option value="">-- Select a payment --</option>';
                    data.payments.forEach(payment => {
                        const option = document.createElement('option');
                        option.value = payment.id;
                        const codePrefix = payment.code ? `${payment.code} - ` : '';
                        option.textContent = `${codePrefix}KES ${payment.amount} (credit KES ${payment.balance}) - ${payment.date}${payment.description ? ' (' + payment.description + ')' : ''}`;
                        option.dataset.balance = payment.balance;
                        option.dataset.amount = payment.amount;
                        paymentSelect.appendChild(option);
                    });

                    paymentSelect.value = '';
                    amountToApplyInput.value = '';
                    amountToApplyInput.removeAttribute('max');
                    hideElement(attachError);
                } else {
                    setMessage(attachError, data.message, true);
                }
            })
            .catch(() => {
                setMessage(attachError, 'Error loading payments', true);
            });
    }

    if (paymentSelect) {
        paymentSelect.addEventListener('change', function() {
            if (this.value) {
                const selectedOption = this.options[this.selectedIndex];
                const paymentBalance = parseFloat(selectedOption.dataset.balance);
                const paymentAmount = parseFloat(selectedOption.dataset.amount);
                const invoiceDue = parseFloat(document.getElementById('amountDue').textContent.replace('KES ', ''));
                const defaultAmount = Math.min(paymentBalance, invoiceDue);

                document.getElementById('paymentRemaining').innerHTML = `<strong>Remaining on this payment: KES ${paymentBalance.toFixed(2)}</strong><br><small>Total payment: KES ${paymentAmount.toFixed(2)}</small>`;
                amountToApplyInput.value = defaultAmount.toFixed(2);
                amountToApplyInput.max = defaultAmount.toFixed(2);
            } else {
                document.getElementById('paymentRemaining').innerHTML = 'Select a payment to see available balance';
                amountToApplyInput.value = '';
                amountToApplyInput.removeAttribute('max');
            }
        });
    }

    if (attachPaymentBtn) {
        attachPaymentBtn.addEventListener('click', function() {
            if (!currentInvoiceId || !paymentSelect.value) {
                setMessage(attachError, 'Please select a payment', true);
                return;
            }

            const selectedOption = paymentSelect.options[paymentSelect.selectedIndex];
            const paymentBalance = parseFloat(selectedOption.dataset.balance);
            const invoiceDue = parseFloat(document.getElementById('amountDue').textContent.replace('KES ', ''));
            const amountToApply = parseFloat(amountToApplyInput.value);

            if (isNaN(amountToApply) || amountToApply <= 0 || amountToApply > paymentBalance || amountToApply > invoiceDue) {
                setMessage(attachError, `Amount must be greater than 0 and no more than KES ${Math.min(paymentBalance, invoiceDue).toFixed(2)}`, true);
                return;
            }

            const formData = new FormData();
            formData.append('invoice_id', currentInvoiceId);
            formData.append('payment_id', paymentSelect.value);
            formData.append('amount_applied', amountToApply);
            formData.append('csrfmiddlewaretoken', getCsrfToken());

            fetch('/invoices/attach-payment/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(data.message);
                        location.reload();
                    } else {
                        setMessage(attachError, data.message, true);
                    }
                })
                .catch(() => {
                    setMessage(attachError, 'Error attaching payment', true);
                });
        });
    }

    const editButtons = document.querySelectorAll('.editPaymentsBtn');
    let currentEditInvoiceId = null;

    editButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            currentEditInvoiceId = this.getAttribute('data-invoice-id');
            loadEditPayments(currentEditInvoiceId);
        });
    });

    function loadEditPayments(invoiceId) {
        fetch(`/invoices/get-payments/?invoice_id=${invoiceId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('editInvoiceNumber').textContent = data.invoice_number;
                    document.getElementById('editInvoiceAmount').textContent = `KES ${data.invoice_amount}`;
                    document.getElementById('editAmountPaid').textContent = `KES ${data.amount_paid}`;
                    document.getElementById('editAmountDue').textContent = `KES ${data.remaining_balance}`;

                    loadAttachedPayments(invoiceId);
                } else {
                    setMessage(editPaymentsError, data.message, true);
                }
            })
            .catch(() => {
                setMessage(editPaymentsError, 'Error loading invoice details', true);
            });
    }

    function loadAttachedPayments(invoiceId) {
        fetch(`/invoices/get-attached-payments/?invoice_id=${invoiceId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const tbody = document.getElementById('attachedPaymentsList');
                    tbody.innerHTML = '';

                    if (data.attached_payments.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No payments attached to this invoice</td></tr>';
                    } else {
                        data.attached_payments.forEach(payment => {
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td class="fw-bold">KES ${payment.amount}</td>
                                <td>KES ${payment.amount_applied}</td>
                                <td>${payment.date}</td>
                                <td>
                                    <button class="btn btn-sm btn-warning editAmountBtn" data-invoice-payment-id="${payment.invoice_payment_id}" data-amount-applied="${payment.amount_applied}" data-max-amount="${payment.amount}">Edit</button>
                                    <button class="btn btn-sm btn-danger removePaymentBtn" data-invoice-payment-id="${payment.invoice_payment_id}" data-amount-applied="${payment.amount_applied}">Remove</button>
                                </td>
                            `;
                            tbody.appendChild(row);
                        });

                        document.querySelectorAll('.editAmountBtn').forEach(btn => {
                            btn.addEventListener('click', editPaymentAmount);
                        });

                        document.querySelectorAll('.removePaymentBtn').forEach(btn => {
                            btn.addEventListener('click', removePayment);
                        });
                    }

                    hideElement(editPaymentsError);
                } else {
                    setMessage(editPaymentsError, data.message, true);
                }
            })
            .catch(() => {
                setMessage(editPaymentsError, 'Error loading attached payments', true);
            });
    }

    function editPaymentAmount(e) {
        const btn = e.target.closest('.editAmountBtn');
        const invoicePaymentId = btn.getAttribute('data-invoice-payment-id');
        const currentAmount = parseFloat(btn.getAttribute('data-amount-applied'));
        const maxAmount = parseFloat(btn.getAttribute('data-max-amount'));

        const newAmount = prompt(`Enter new amount (max KES ${maxAmount.toFixed(2)}):`, currentAmount.toFixed(2));

        if (newAmount === null) return;

        const amount = parseFloat(newAmount);
        if (isNaN(amount) || amount < 0 || amount > maxAmount) {
            alert(`Amount must be between 0 and ${maxAmount.toFixed(2)}`);
            return;
        }

        updatePaymentAmount(invoicePaymentId, amount, currentEditInvoiceId);
    }

    function removePayment(e) {
        if (!confirm('Are you sure you want to remove this payment?')) return;

        const btn = e.target.closest('.removePaymentBtn');
        const invoicePaymentId = btn.getAttribute('data-invoice-payment-id');

        removePaymentAttachment(invoicePaymentId, currentEditInvoiceId);
    }

    function updatePaymentAmount(invoicePaymentId, newAmount, invoiceId) {
        const formData = new FormData();
        formData.append('invoice_payment_id', invoicePaymentId);
        formData.append('amount_applied', newAmount);
        formData.append('csrfmiddlewaretoken', getCsrfToken());

        fetch('/invoices/update-invoice-payment/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    setMessage(editPaymentsSuccess, data.message, true);
                    loadEditPayments(invoiceId);
                } else {
                    setMessage(editPaymentsError, data.message, true);
                }
            })
            .catch(() => {
                setMessage(editPaymentsError, 'Error updating payment', true);
            });
    }

    function removePaymentAttachment(invoicePaymentId, invoiceId) {
        const formData = new FormData();
        formData.append('invoice_payment_id', invoicePaymentId);
        formData.append('csrfmiddlewaretoken', getCsrfToken());

        fetch('/invoices/remove-invoice-payment/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    setMessage(editPaymentsSuccess, data.message, true);
                    loadEditPayments(invoiceId);
                } else {
                    setMessage(editPaymentsError, data.message, true);
                }
            })
            .catch(() => {
                setMessage(editPaymentsError, 'Error removing payment', true);
            });
    }
});
