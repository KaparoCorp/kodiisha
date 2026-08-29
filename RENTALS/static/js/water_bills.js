document.addEventListener('DOMContentLoaded', function() {
    const selectAllWaterBillPayments = document.getElementById('selectAllWaterBillPayments');
    const deleteSelectedWaterBillPaymentsBtn = document.getElementById('deleteSelectedWaterBillPaymentsBtn');
    const uploadForm = document.getElementById('uploadWaterBillPaymentsForm');
    const uploadMessages = document.getElementById('uploadWaterBillPaymentsMessages');
    const waterBillPaymentsFile = document.getElementById('waterBillPaymentsFile');
    const validateWaterBillPaymentsBtn = document.getElementById('validateWaterBillPaymentsBtn');
    const uploadWaterBillPaymentsBtn = document.getElementById('uploadWaterBillPaymentsBtn');
    const cancelWaterBillPaymentsUploadBtn = document.getElementById('cancelWaterBillPaymentsUploadBtn');
    const bulkGenerateForm = document.getElementById('bulkGenerateWaterBillsForm');
    const bulkGenerateMessages = document.getElementById('bulkGenerateWaterBillsMessages');
    const bulkWaterBillsFile = document.getElementById('bulkWaterBillsFile');
    const validateBulkWaterBillsBtn = document.getElementById('validateBulkWaterBillsBtn');
    const uploadBulkWaterBillsBtn = document.getElementById('uploadBulkWaterBillsBtn');
    const cancelBulkWaterBillsUploadBtn = document.getElementById('cancelBulkWaterBillsUploadBtn');

    function escapeHtml(value) {
        const div = document.createElement('div');
        div.textContent = value;
        return div.innerHTML;
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

    function toggleWaterBillPaymentDeleteButton() {
        const count = document.querySelectorAll('.water-bill-payment-checkbox:checked').length;
        if (deleteSelectedWaterBillPaymentsBtn) {
            deleteSelectedWaterBillPaymentsBtn.style.display = count > 0 ? 'inline-block' : 'none';
        }
    }

    function initWaterBillPaymentDeleteButton() {
        toggleWaterBillPaymentDeleteButton();
    }

    if (selectAllWaterBillPayments) {
        selectAllWaterBillPayments.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.water-bill-payment-checkbox');
            checkboxes.forEach(checkbox => checkbox.checked = this.checked);
            toggleWaterBillPaymentDeleteButton();
        });
    }

    document.querySelectorAll('.water-bill-payment-checkbox').forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            toggleWaterBillPaymentDeleteButton();
        });
    });

    setTimeout(toggleWaterBillPaymentDeleteButton, 0);

    if (deleteSelectedWaterBillPaymentsBtn) {
        deleteSelectedWaterBillPaymentsBtn.addEventListener('click', function() {
            const selectedIds = Array.from(document.querySelectorAll('.water-bill-payment-checkbox:checked'))
                                     .map(checkbox => checkbox.value);

            if (!selectedIds.length) return;
            if (!confirm(`Delete ${selectedIds.length} water bill payment(s)?`)) return;
            if (!window.downloadSelectedRowsBeforeDelete('.water-bill-payment-checkbox:checked', 'water-bill-payments-before-delete')) return;

            const formData = new FormData();
            selectedIds.forEach(id => formData.append('payment_ids[]', id));

            fetch('/water_bills/payments/delete/', {
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
                    window.location.reload();
                } else {
                    alert(data.message || 'Failed to delete water bill payments');
                }
            })
            .catch(error => {
                alert('Error deleting water bill payments');
            });
        });
    }

    function showUploadMessage(type, title, messages = []) {
        if (!uploadMessages) return;

        const alertClass = type === 'success' ? 'alert-success' : type === 'info' ? 'alert-info' : 'alert-danger';
        const listHtml = messages.length
            ? `<ul class="mb-0 mt-2">${messages.map(message => `<li>${escapeHtml(message)}</li>`).join('')}</ul>`
            : '';

        uploadMessages.className = `alert ${alertClass}`;
        uploadMessages.innerHTML = `<div class="fw-semibold">${escapeHtml(title)}</div>${listHtml}`;
    }

    function showBulkGenerateMessage(type, title, messages = []) {
        if (!bulkGenerateMessages) return;

        const alertClass = type === 'success' ? 'alert-success' : type === 'info' ? 'alert-info' : 'alert-danger';
        const listHtml = messages.length
            ? `<ul class="mb-0 mt-2">${messages.map(message => `<li>${escapeHtml(message)}</li>`).join('')}</ul>`
            : '';

        bulkGenerateMessages.className = `alert ${alertClass}`;
        bulkGenerateMessages.innerHTML = `<div class="fw-semibold">${escapeHtml(title)}</div>${listHtml}`;
    }

    function resetUploadActions() {
        if (uploadWaterBillPaymentsBtn) {
            uploadWaterBillPaymentsBtn.style.display = 'none';
            uploadWaterBillPaymentsBtn.disabled = false;
            uploadWaterBillPaymentsBtn.textContent = 'Upload';
        }
        if (cancelWaterBillPaymentsUploadBtn) cancelWaterBillPaymentsUploadBtn.style.display = 'none';
        if (validateWaterBillPaymentsBtn) {
            validateWaterBillPaymentsBtn.style.display = 'inline-block';
            validateWaterBillPaymentsBtn.disabled = false;
            validateWaterBillPaymentsBtn.textContent = 'Validate';
        }
        if (uploadMessages) {
            uploadMessages.className = 'alert d-none';
            uploadMessages.innerHTML = '';
        }
    }

    function resetBulkGenerateActions() {
        if (uploadBulkWaterBillsBtn) {
            uploadBulkWaterBillsBtn.style.display = 'none';
            uploadBulkWaterBillsBtn.disabled = false;
            uploadBulkWaterBillsBtn.textContent = 'Upload';
        }
        if (cancelBulkWaterBillsUploadBtn) cancelBulkWaterBillsUploadBtn.style.display = 'none';
        if (validateBulkWaterBillsBtn) {
            validateBulkWaterBillsBtn.style.display = 'inline-block';
            validateBulkWaterBillsBtn.disabled = false;
            validateBulkWaterBillsBtn.textContent = 'Validate';
        }
        if (bulkGenerateMessages) {
            bulkGenerateMessages.className = 'alert d-none';
            bulkGenerateMessages.innerHTML = '';
        }
    }

    function getSelectedBulkWaterBillsFile() {
        const file = bulkWaterBillsFile && bulkWaterBillsFile.files ? bulkWaterBillsFile.files[0] : null;

        if (!file) {
            showBulkGenerateMessage('error', 'Please select a file');
            return null;
        }

        const validTypes = ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
        if (!validTypes.includes(file.type) && !file.name.endsWith('.csv') && !file.name.endsWith('.xlsx')) {
            showBulkGenerateMessage('error', 'Please upload a CSV or XLSX file');
            return null;
        }

        return file;
    }

    function postBulkWaterBillsUpload(validateOnly) {
        const file = getSelectedBulkWaterBillsFile();
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('csrfmiddlewaretoken', bulkGenerateForm.querySelector('[name=csrfmiddlewaretoken]').value);
        if (validateOnly) {
            formData.append('validate_only', '1');
        }

        if (validateOnly && validateBulkWaterBillsBtn) {
            validateBulkWaterBillsBtn.disabled = true;
            validateBulkWaterBillsBtn.textContent = 'Validating...';
        }
        if (!validateOnly && uploadBulkWaterBillsBtn) {
            uploadBulkWaterBillsBtn.disabled = true;
            uploadBulkWaterBillsBtn.textContent = 'Uploading...';
        }

        fetch('/water_bills/bulk-generate/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            const detailMessages = data.errors ? data.errors.slice(0, 10) : [];

            if (validateOnly) {
                if (data.success) {
                    showBulkGenerateMessage('success', data.message || `Validation complete: ${data.valid_rows || 0} valid, ${data.invalid_rows || 0} invalid.`, detailMessages);
                    if (uploadBulkWaterBillsBtn) {
                        uploadBulkWaterBillsBtn.style.display = 'inline-block';
                        uploadBulkWaterBillsBtn.disabled = false;
                        uploadBulkWaterBillsBtn.textContent = 'Upload';
                    }
                    if (cancelBulkWaterBillsUploadBtn) cancelBulkWaterBillsUploadBtn.style.display = 'inline-block';
                    if (validateBulkWaterBillsBtn) validateBulkWaterBillsBtn.style.display = 'none';
                } else {
                    showBulkGenerateMessage('error', data.message || 'Validation failed', detailMessages);
                    if (uploadBulkWaterBillsBtn) uploadBulkWaterBillsBtn.style.display = 'none';
                    if (cancelBulkWaterBillsUploadBtn) cancelBulkWaterBillsUploadBtn.style.display = 'inline-block';
                    if (validateBulkWaterBillsBtn) {
                        validateBulkWaterBillsBtn.disabled = false;
                        validateBulkWaterBillsBtn.textContent = 'Validate';
                    }
                }
                return;
            }

            if (data.success) {
                showBulkGenerateMessage('success', data.message || `Successfully generated ${data.count} water bill(s)`, detailMessages);
                window.location.reload();
            } else {
                showBulkGenerateMessage('error', data.message || 'Failed to generate water bills', detailMessages);
                if (uploadBulkWaterBillsBtn) {
                    uploadBulkWaterBillsBtn.disabled = false;
                    uploadBulkWaterBillsBtn.textContent = 'Upload';
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showBulkGenerateMessage('error', validateOnly ? 'An error occurred while validating water bills' : 'An error occurred while generating water bills');
            if (validateBulkWaterBillsBtn) {
                validateBulkWaterBillsBtn.disabled = false;
                validateBulkWaterBillsBtn.textContent = 'Validate';
            }
            if (uploadBulkWaterBillsBtn) {
                uploadBulkWaterBillsBtn.disabled = false;
                uploadBulkWaterBillsBtn.textContent = 'Upload';
            }
        });
    }

    function getSelectedWaterBillPaymentFile() {
        const file = waterBillPaymentsFile && waterBillPaymentsFile.files ? waterBillPaymentsFile.files[0] : null;

        if (!file) {
            showUploadMessage('error', 'Please select a file');
            return null;
        }

        const validTypes = ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
        if (!validTypes.includes(file.type) && !file.name.endsWith('.csv') && !file.name.endsWith('.xlsx')) {
            showUploadMessage('error', 'Please upload a CSV or XLSX file');
            return null;
        }

        return file;
    }

    function postWaterBillPaymentUpload(validateOnly) {
        const file = getSelectedWaterBillPaymentFile();
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('csrfmiddlewaretoken', uploadForm.querySelector('[name=csrfmiddlewaretoken]').value);
        if (validateOnly) {
            formData.append('validate_only', '1');
        }

        if (validateOnly && validateWaterBillPaymentsBtn) {
            validateWaterBillPaymentsBtn.disabled = true;
            validateWaterBillPaymentsBtn.textContent = 'Validating...';
        }
        if (!validateOnly && uploadWaterBillPaymentsBtn) {
            uploadWaterBillPaymentsBtn.disabled = true;
            uploadWaterBillPaymentsBtn.textContent = 'Uploading...';
        }

        fetch('/water_bills/upload/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            const detailMessages = data.errors ? data.errors.slice(0, 10) : [];

            if (validateOnly) {
                if (data.success) {
                    showUploadMessage('success', data.message || `Validation complete: ${data.valid_rows || 0} valid, ${data.invalid_rows || 0} invalid.`, detailMessages);
                    if (uploadWaterBillPaymentsBtn) {
                        uploadWaterBillPaymentsBtn.style.display = 'inline-block';
                        uploadWaterBillPaymentsBtn.disabled = false;
                        uploadWaterBillPaymentsBtn.textContent = 'Upload';
                    }
                    if (cancelWaterBillPaymentsUploadBtn) cancelWaterBillPaymentsUploadBtn.style.display = 'inline-block';
                    if (validateWaterBillPaymentsBtn) validateWaterBillPaymentsBtn.style.display = 'none';
                } else {
                    showUploadMessage('error', data.message || 'Validation failed', detailMessages);
                    if (uploadWaterBillPaymentsBtn) uploadWaterBillPaymentsBtn.style.display = 'none';
                    if (cancelWaterBillPaymentsUploadBtn) cancelWaterBillPaymentsUploadBtn.style.display = 'inline-block';
                    if (validateWaterBillPaymentsBtn) {
                        validateWaterBillPaymentsBtn.disabled = false;
                        validateWaterBillPaymentsBtn.textContent = 'Validate';
                    }
                }
                return;
            }

            if (data.success) {
                showUploadMessage('success', data.message || `Successfully uploaded ${data.count} water bill payments`, detailMessages);
                window.location.reload();
            } else {
                showUploadMessage('error', data.message || 'Failed to upload water bill payments', detailMessages);
                if (uploadWaterBillPaymentsBtn) {
                    uploadWaterBillPaymentsBtn.disabled = false;
                    uploadWaterBillPaymentsBtn.textContent = 'Upload';
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showUploadMessage('error', validateOnly ? 'An error occurred while validating water bill payments' : 'An error occurred while uploading water bill payments');
            if (validateWaterBillPaymentsBtn) {
                validateWaterBillPaymentsBtn.disabled = false;
                validateWaterBillPaymentsBtn.textContent = 'Validate';
            }
            if (uploadWaterBillPaymentsBtn) {
                uploadWaterBillPaymentsBtn.disabled = false;
                uploadWaterBillPaymentsBtn.textContent = 'Upload';
            }
        });
    }

    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            postWaterBillPaymentUpload(true);
        });

        if (uploadWaterBillPaymentsBtn) {
            uploadWaterBillPaymentsBtn.addEventListener('click', function() {
                postWaterBillPaymentUpload(false);
            });
        }

        if (waterBillPaymentsFile) {
            waterBillPaymentsFile.addEventListener('change', resetUploadActions);
        }

        const uploadModal = document.getElementById('uploadModal');
        if (uploadModal) {
            uploadModal.addEventListener('hidden.bs.modal', function() {
                uploadForm.reset();
                resetUploadActions();
            });
        }
    }

    if (bulkGenerateForm) {
        bulkGenerateForm.addEventListener('submit', function(e) {
            e.preventDefault();
            postBulkWaterBillsUpload(true);
        });

        if (uploadBulkWaterBillsBtn) {
            uploadBulkWaterBillsBtn.addEventListener('click', function() {
                postBulkWaterBillsUpload(false);
            });
        }

        if (bulkWaterBillsFile) {
            bulkWaterBillsFile.addEventListener('change', resetBulkGenerateActions);
        }

        const bulkGenerateModal = document.getElementById('bulkGenerateWaterBillModal');
        if (bulkGenerateModal) {
            bulkGenerateModal.addEventListener('hidden.bs.modal', function() {
                bulkGenerateForm.reset();
                resetBulkGenerateActions();
            });
        }
    }

    // Claim Payment Modal
    const claimPaymentModal = document.getElementById('claimPaymentModal');
    const claimPaymentSelect = document.getElementById('claimPaymentSelect');
    const claimPaymentDetails = document.getElementById('claimPaymentDetails');
    const claimAmountInput = document.getElementById('claimAmountInput');
    const confirmClaimPaymentBtn = document.getElementById('confirmClaimPaymentBtn');
    const claimPaymentMessages = document.getElementById('claimPaymentMessages');
    const claimWaterBillInfo = document.getElementById('claimWaterBillInfo');

    let currentClaimWaterBillId = null;
    let currentClaimTenantId = null;
    let currentClaimPaymentBalance = null;

    function showClaimPaymentMessage(type, title, messages = []) {
        if (!claimPaymentMessages) return;

        const alertClass = type === 'success' ? 'alert-success' : type === 'info' ? 'alert-info' : 'alert-danger';
        const listHtml = messages.length
            ? `<ul class="mb-0 mt-2">${messages.map(message => `<li>${escapeHtml(message)}</li>`).join('')}</ul>`
            : '';

        claimPaymentMessages.className = `alert ${alertClass}`;
        claimPaymentMessages.innerHTML = `<div class="fw-semibold">${escapeHtml(title)}</div>${listHtml}`;
    }

    function resetClaimPaymentForm() {
        if (claimPaymentSelect) {
            claimPaymentSelect.innerHTML = '<option value="">-- Select a payment --</option>';
        }
        if (claimPaymentDetails) claimPaymentDetails.classList.add('d-none');
        if (claimAmountInput) {
            claimAmountInput.value = '';
            claimAmountInput.removeAttribute('max');
        }
        if (claimPaymentMessages) {
            claimPaymentMessages.className = 'alert d-none';
            claimPaymentMessages.innerHTML = '';
        }
        if (claimWaterBillInfo) claimWaterBillInfo.textContent = 'Select a water bill to view details';
        currentClaimWaterBillId = null;
        currentClaimTenantId = null;
        currentClaimPaymentBalance = null;
    }

    document.addEventListener('click', function(e) {
        const btn = e.target.closest('.claim-payment-btn');
        if (!btn) return;

        currentClaimWaterBillId = btn.dataset.waterBillId;
        currentClaimTenantId = btn.dataset.tenantId;
        const unitId = btn.dataset.unitId;
        const propertyId = btn.dataset.propertyId;

        const billRow = btn.closest('tr');
        const unitName = billRow ? billRow.cells[1]?.textContent.trim() : '';
        const amount = billRow ? billRow.cells[7]?.textContent.trim() : '';
        const dueDate = billRow ? billRow.cells[8]?.textContent.trim() : '';
        const status = billRow ? billRow.cells[9]?.textContent.trim() : '';

        if (claimWaterBillInfo) {
            claimWaterBillInfo.innerHTML = `
                <strong>Unit:</strong> ${escapeHtml(unitName)}<br>
                <strong>Amount:</strong> KES ${escapeHtml(amount)}<br>
                <strong>Due Date:</strong> ${escapeHtml(dueDate)}<br>
                <strong>Status:</strong> ${escapeHtml(status)}
            `;
        }

        resetClaimPaymentForm();

        if (currentClaimTenantId) {
            fetch(`/water_bills/available-payments/?tenant_id=${currentClaimTenantId}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) return;
                if (claimPaymentSelect) {
                    claimPaymentSelect.innerHTML = '<option value="">-- Select a payment --</option>';
                    data.payments.forEach(payment => {
                        const option = document.createElement('option');
                        option.value = payment.id;
                        option.textContent = `Payment #${payment.id} - KES ${payment.balance} remaining (${payment.date})`;
                        option.dataset.balance = payment.balance;
                        option.dataset.amount = payment.amount;
                        option.dataset.date = payment.date;
                        option.dataset.code = payment.code || '';
                        option.dataset.description = payment.description || '';
                        option.dataset.attachments = JSON.stringify(payment.attachments || []);
                        claimPaymentSelect.appendChild(option);
                    });
                }
            })
            .catch(error => {
                console.error('Error fetching available payments:', error);
            });
        }
    });

    if (claimPaymentSelect) {
        claimPaymentSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            if (!selectedOption.value) {
                if (claimPaymentDetails) claimPaymentDetails.classList.add('d-none');
                if (claimAmountInput) {
                    claimAmountInput.value = '';
                    claimAmountInput.removeAttribute('max');
                }
                currentClaimPaymentBalance = null;
                return;
            }

            const balance = parseFloat(selectedOption.dataset.balance);
            currentClaimPaymentBalance = balance;

            if (claimPaymentDetails) claimPaymentDetails.classList.remove('d-none');
            const amountEl = document.getElementById('claimPaymentAmount');
            const dateEl = document.getElementById('claimPaymentDate');
            const codeEl = document.getElementById('claimPaymentCode');
            const balanceEl = document.getElementById('claimPaymentBalance');
            const descEl = document.getElementById('claimPaymentDescription');
            const attachmentsEl = document.getElementById('claimPaymentAttachments');

            if (amountEl) amountEl.textContent = `KES ${selectedOption.dataset.amount}`;
            if (dateEl) dateEl.textContent = selectedOption.dataset.date;
            if (codeEl) codeEl.textContent = selectedOption.dataset.code || '-';
            if (balanceEl) balanceEl.textContent = `KES ${selectedOption.dataset.balance}`;
            if (descEl) descEl.textContent = selectedOption.dataset.description || '-';

            const attachments = JSON.parse(selectedOption.dataset.attachments || '[]');
            if (attachmentsEl) {
                if (attachments.length === 0) {
                    attachmentsEl.textContent = 'None';
                } else {
                    attachmentsEl.innerHTML = attachments.map(a =>
                        `<div>Invoice ${escapeHtml(a.invoice_number || a.invoice_id)} - KES ${a.amount_applied}</div>`
                    ).join('');
                }
            }

            if (claimAmountInput) {
                claimAmountInput.max = selectedOption.dataset.balance;
                claimAmountInput.value = selectedOption.dataset.balance;
            }
        });
    }

    if (confirmClaimPaymentBtn) {
        confirmClaimPaymentBtn.addEventListener('click', function() {
            if (!currentClaimWaterBillId) {
                showClaimPaymentMessage('error', 'Error', ['No water bill selected']);
                return;
            }

            const selectedPaymentId = claimPaymentSelect ? claimPaymentSelect.value : '';
            if (!selectedPaymentId) {
                showClaimPaymentMessage('error', 'Error', ['Please select a payment']);
                return;
            }

            const amountToClaim = claimAmountInput ? claimAmountInput.value : '';
            if (!amountToClaim || parseFloat(amountToClaim) <= 0) {
                showClaimPaymentMessage('error', 'Error', ['Claim amount must be greater than 0']);
                return;
            }

            if (currentClaimPaymentBalance !== null && parseFloat(amountToClaim) > currentClaimPaymentBalance) {
                showClaimPaymentMessage('error', 'Error', ['Claim amount exceeds payment balance']);
                return;
            }

            confirmClaimPaymentBtn.disabled = true;
            confirmClaimPaymentBtn.textContent = 'Processing...';

            const formData = new FormData();
            formData.append('payment_id', selectedPaymentId);
            formData.append('amount_to_claim', amountToClaim);
            formData.append('water_bill_id', currentClaimWaterBillId);
            formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

            fetch('/water_bills/claim-payment/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showClaimPaymentMessage('success', 'Success', [data.message]);
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    showClaimPaymentMessage('error', 'Error', [data.message || 'Claim failed']);
                    confirmClaimPaymentBtn.disabled = false;
                    confirmClaimPaymentBtn.textContent = 'Confirm Claim';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showClaimPaymentMessage('error', 'Error', ['An error occurred while processing the claim']);
                confirmClaimPaymentBtn.disabled = false;
                confirmClaimPaymentBtn.textContent = 'Confirm Claim';
            });
        });
    }

    if (claimPaymentModal) {
        claimPaymentModal.addEventListener('hidden.bs.modal', function() {
            resetClaimPaymentForm();
        });
    }

    const generateForm = document.getElementById('generateWaterBillForm');
    const generateProperty = document.getElementById('generateProperty');
    const generateUnit = document.getElementById('generateUnit');
    const generateModal = document.getElementById('generateModal');

    function setGenerateUnitPlaceholder(message, disabled = true) {
        if (!generateUnit) return;
        generateUnit.innerHTML = '';
        const option = document.createElement('option');
        option.value = '';
        option.textContent = message;
        option.selected = true;
        generateUnit.appendChild(option);
        generateUnit.disabled = disabled;
    }

    function buildPropertyUnitsUrl(propertyId) {
        const template = generateForm ? generateForm.dataset.unitsUrlTemplate : '';
        return template ? template.replace('/0/', `/${propertyId}/`) : `/water_bills/property-units/${propertyId}/`;
    }

    function loadGenerateUnits(propertyId) {
        if (!propertyId || !generateUnit) {
            setGenerateUnitPlaceholder('Select Property First');
            return;
        }

        setGenerateUnitPlaceholder('Loading Units...');

        fetch(buildPropertyUnitsUrl(propertyId), {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            generateUnit.innerHTML = '';

            if (!data.units || !data.units.length) {
                setGenerateUnitPlaceholder('No Units Found');
                return;
            }

            const placeholder = document.createElement('option');
            placeholder.value = '';
            placeholder.textContent = 'Select Unit';
            placeholder.selected = true;
            placeholder.disabled = true;
            generateUnit.appendChild(placeholder);

            data.units.forEach(unit => {
                const option = document.createElement('option');
                option.value = unit.id;
                const tenantLabel = unit.tenant ? ` - ${unit.tenant}` : '';
                option.textContent = `${unit.name}${tenantLabel}`;
                generateUnit.appendChild(option);
            });

            generateUnit.disabled = false;
        })
        .catch(() => {
            setGenerateUnitPlaceholder('Unable To Load Units');
        });
    }

    if (generateProperty && generateUnit) {
        generateProperty.addEventListener('change', function() {
            loadGenerateUnits(this.value);
        });
    }

    if (generateModal) {
        generateModal.addEventListener('hidden.bs.modal', function() {
            if (generateForm) generateForm.reset();
            setGenerateUnitPlaceholder('Select Property First');
            document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
            document.body.classList.remove('modal-open');
        });
    }

    const editForm = document.getElementById('editWaterBillForm');
    const editProperty = document.getElementById('editProperty');
    const editUnit = document.getElementById('editUnit');
    const editModal = document.getElementById('editWaterBillModal');
    const editBillIdInput = document.getElementById('editBillId');

    function setEditUnitPlaceholder(message, disabled = true) {
        if (!editUnit) return;
        editUnit.innerHTML = '';
        const option = document.createElement('option');
        option.value = '';
        option.textContent = message;
        option.selected = true;
        editUnit.appendChild(option);
        editUnit.disabled = disabled;
    }

    function loadEditUnits(propertyId) {
        if (!propertyId || !editUnit) {
            setEditUnitPlaceholder('Select Property First');
            return;
        }

        setEditUnitPlaceholder('Loading Units...');

        fetch(buildPropertyUnitsUrl(propertyId), {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            editUnit.innerHTML = '';

            if (!data.units || !data.units.length) {
                setEditUnitPlaceholder('No Units Found');
                return;
            }

            const placeholder = document.createElement('option');
            placeholder.value = '';
            placeholder.textContent = 'Select Unit';
            placeholder.selected = true;
            placeholder.disabled = true;
            editUnit.appendChild(placeholder);

            data.units.forEach(unit => {
                const option = document.createElement('option');
                option.value = unit.id;
                const tenantLabel = unit.tenant ? ` - ${unit.tenant}` : '';
                option.textContent = `${unit.name}${tenantLabel}`;
                editUnit.appendChild(option);
            });

            editUnit.disabled = false;
        })
        .catch(() => {
            setEditUnitPlaceholder('Unable To Load Units');
        });
    }

    if (editProperty && editUnit) {
        editProperty.addEventListener('change', function() {
            loadEditUnits(this.value);
        });
    }

    document.querySelectorAll('.editWaterBillBtn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const billId = this.getAttribute('data-bill-id');
            editBillIdInput.value = billId;

            fetch(`/water_bills/edit/${billId}/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (editProperty) editProperty.value = data.property_id;
                    loadEditUnits(data.property_id);
                    if (editUnit) {
                        editUnit.value = data.unit_id;
                        editUnit.disabled = false;
                    }
                    if (document.getElementById('editPreviousReading')) document.getElementById('editPreviousReading').value = data.previous_reading;
                    if (document.getElementById('editCurrentReading')) document.getElementById('editCurrentReading').value = data.current_reading;
                    if (document.getElementById('editRate')) document.getElementById('editRate').value = data.rate;
                    if (document.getElementById('editDueDate')) document.getElementById('editDueDate').value = data.due_date;

                    const modalInstance = bootstrap.Modal.getOrCreateInstance(editModal);
                    if (modalInstance) {
                        modalInstance.show();
                    }
                } else {
                    alert(data.message || 'Failed to load water bill data');
                }
            })
            .catch(() => {
                alert('Error loading water bill data');
            });
        });
    });

    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const billId = editBillIdInput ? editBillIdInput.value : '';
            if (!billId) return;

            const formData = new FormData(editForm);
            formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

            fetch(`/water_bills/edit/${billId}/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const modalInstance = bootstrap.Modal.getInstance(editModal);
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                    document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
                    document.body.classList.remove('modal-open');
                    setTimeout(function() {
                        window.location.reload();
                    }, 300);
                } else {
                    const errorText = data.errors ? Object.values(data.errors).flat().join(', ') : (data.message || 'Failed to update water bill');
                    alert(errorText);
                }
            })
            .catch(() => {
                alert('Error updating water bill');
            });
        });
    }

    if (editModal) {
        editModal.addEventListener('hidden.bs.modal', function() {
            if (editForm) editForm.reset();
            setEditUnitPlaceholder('Select Property First');
            document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
            document.body.classList.remove('modal-open');
        });
    }

    initWaterBillPaymentDeleteButton();
});

// ======================
// DELETE WATER BILLS FUNCTIONALITY
// ======================

(function() {
    const waterBillsPage = document.getElementById('waterBillsPage');
    const deleteWaterBillsUrl = waterBillsPage ? waterBillsPage.dataset.deleteUrl : '/water_bills/delete/';
    const selectAllCheckbox = document.getElementById('selectAllWaterBills');
    const waterBillCheckboxes = document.querySelectorAll('.water-bill-checkbox');
    const deleteSelectedBtn = document.getElementById('deleteSelectedWaterBillsBtn');

    function updateDeleteButton() {
        const anySelected = Array.from(waterBillCheckboxes).some(cb => cb.checked);
        const allSelected = waterBillCheckboxes.length > 0 && Array.from(waterBillCheckboxes).every(cb => cb.checked);
        if (deleteSelectedBtn) {
            deleteSelectedBtn.style.display = anySelected ? 'inline-block' : 'none';
        }
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = allSelected;
            selectAllCheckbox.indeterminate = anySelected && !allSelected;
        }
    }

    if (selectAllCheckbox && waterBillCheckboxes.length) {
        selectAllCheckbox.addEventListener('change', function() {
            waterBillCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateDeleteButton();
        });

        waterBillCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', updateDeleteButton);
        });

        if (deleteSelectedBtn) {
            deleteSelectedBtn.addEventListener('click', function() {
                const selectedIds = Array.from(waterBillCheckboxes)
                    .filter(cb => cb.checked)
                    .map(cb => cb.value);

                if (selectedIds.length === 0) {
                    alert('Please select at least one water bill to delete');
                    return;
                }

                if (confirm(`Are you sure you want to delete ${selectedIds.length} water bill/s? This action cannot be undone.`)) {
                    if (!window.downloadSelectedRowsBeforeDelete('.water-bill-checkbox:checked', 'water-bills-before-delete')) return;

                    const formData = new FormData();
                    selectedIds.forEach(id => formData.append('bill_ids[]', id));

                    fetch(deleteWaterBillsUrl, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value || '',
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
                            alert(data.message || 'Failed to delete water bills');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('An error occurred while deleting water bills');
                    });
                }
            });
        }
    }
})();
