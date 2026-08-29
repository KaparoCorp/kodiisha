document.addEventListener('DOMContentLoaded', function() {
    const selectAllBtn = document.getElementById('selectAllPayments');
    const deleteBtn = document.getElementById('deleteSelectedPaymentsBtn');

    // 1. Correct way to get CSRF token in Django
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

    // 2. Multi-select logic
    if (selectAllBtn) {
        selectAllBtn.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.payment-checkbox');
            checkboxes.forEach(cb => cb.checked = this.checked);
            toggleDeleteButton();
        });
    }

    // 3. Individual checkbox logic (using delegation)
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('payment-checkbox')) {
            const allCheckboxes = document.querySelectorAll('.payment-checkbox');
            const checkedCheckboxes = document.querySelectorAll('.payment-checkbox:checked');
            
            // Sync the "Select All" checkbox state
            if (selectAllBtn) {
                selectAllBtn.checked = allCheckboxes.length === checkedCheckboxes.length;
            }
            toggleDeleteButton();
        }
    });

    function toggleDeleteButton() {
        const count = document.querySelectorAll('.payment-checkbox:checked').length;
        if (deleteBtn) {
            deleteBtn.style.display = count > 0 ? 'inline-block' : 'none';
        }
    }

    // 4. The Delete Fetch
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
            const selectedIds = Array.from(document.querySelectorAll('.payment-checkbox:checked'))
                                     .map(cb => cb.value);

            if (!selectedIds.length) return;
            if (!confirm(`Delete ${selectedIds.length} payment(s)?`)) return;
            if (!window.downloadSelectedRowsBeforeDelete('.payment-checkbox:checked', 'payments-before-delete')) return;

            const formData = new FormData();
            selectedIds.forEach(id => formData.append('payment_ids[]', id));

            // USE THE ABSOLUTE PATH matching your urls.py
            fetch('/payments/delete/', { 
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    alert(data.message);
                }
            })
            .catch(err => alert("Communication error with server. Check URL configuration."));
        });
    }

    // 5. Handle Add Payment Form
    const addPaymentForm = document.getElementById('addPaymentForm');
    
    if (addPaymentForm) {
        addPaymentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            fetch('', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => response.text())
            .then(html => {
                // Check if response contains form errors
                if (html.includes('errorlist') || html.includes('This field is required')) {
                    // Display errors in modal
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const errorElements = doc.querySelectorAll('ul.errorlist');
                    
                    let errorHtml = '<ul>';
                    errorElements.forEach(el => {
                        const items = el.querySelectorAll('li');
                        items.forEach(item => {
                            errorHtml += '<li>' + item.textContent + '</li>';
                        });
                    });
                    errorHtml += '</ul>';
                    
                    if (errorElements.length > 0) {
                        document.getElementById('paymentErrors').innerHTML = errorHtml;
                        document.getElementById('paymentErrors').style.display = 'block';
                    } else {
                        location.reload();
                    }
                } else {
                    // Success - reload page
                    location.reload();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred');
            });
        });
    }
    
    // 6. Handle Upload Payments Form
    const uploadForm = document.getElementById('uploadPaymentsForm');
    const uploadMessages = document.getElementById('uploadPaymentsMessages');
    const paymentsFile = document.getElementById('paymentsFile');
    const validatePaymentsBtn = document.getElementById('validatePaymentsBtn');
    const uploadPaymentsBtn = document.getElementById('uploadPaymentsBtn');
    const cancelPaymentsUploadBtn = document.getElementById('cancelPaymentsUploadBtn');

    function escapeHtml(value) {
        const div = document.createElement('div');
        div.textContent = value;
        return div.innerHTML;
    }

    function showUploadMessage(type, title, messages = []) {
        if (!uploadMessages) return;

        const alertClass = type === 'success' ? 'alert-success' : type === 'info' ? 'alert-info' : type === 'warning' ? 'alert-warning' : 'alert-danger';
        const listHtml = messages.length
            ? `<ul class="mb-0 mt-2">${messages.map(message => `<li>${escapeHtml(message)}</li>`).join('')}</ul>`
            : '';

        uploadMessages.className = `alert ${alertClass}`;
        uploadMessages.innerHTML = `<div class="fw-semibold">${escapeHtml(title)}</div>${listHtml}`;
    }

    function resetUploadActions() {
        if (uploadPaymentsBtn) {
            uploadPaymentsBtn.style.display = 'none';
            uploadPaymentsBtn.disabled = false;
            uploadPaymentsBtn.textContent = 'Upload';
        }
        if (cancelPaymentsUploadBtn) cancelPaymentsUploadBtn.style.display = 'none';
        if (validatePaymentsBtn) {
            validatePaymentsBtn.style.display = 'inline-block';
            validatePaymentsBtn.disabled = false;
            validatePaymentsBtn.textContent = 'Validate';
        }
        if (uploadMessages) {
            uploadMessages.className = 'alert d-none';
            uploadMessages.innerHTML = '';
        }
    }

    function getSelectedPaymentFile() {
        const file = paymentsFile && paymentsFile.files ? paymentsFile.files[0] : null;

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

    function postPaymentUpload(validateOnly) {
        const file = getSelectedPaymentFile();
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('csrfmiddlewaretoken', uploadForm.querySelector('[name=csrfmiddlewaretoken]').value);
        if (validateOnly) {
            formData.append('validate_only', '1');
        }

        if (validateOnly && validatePaymentsBtn) {
            validatePaymentsBtn.disabled = true;
            validatePaymentsBtn.textContent = 'Validating...';
        }
        if (!validateOnly && uploadPaymentsBtn) {
            uploadPaymentsBtn.disabled = true;
            uploadPaymentsBtn.textContent = 'Uploading...';
        }

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 300000);

        fetch('/payments/upload/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData,
            signal: controller.signal
        })
        .then(response => {
            clearTimeout(timeoutId);
            return response.json();
        })
        .then(data => {
            const detailMessages = [
                ...(data.errors || []),
                ...(data.duplicates || []),
            ].slice(0, 10);

            if (validateOnly) {
                if (data.success) {
                    const hasWarnings = data.duplicates && data.duplicates.length > 0;
                    showUploadMessage(
                        hasWarnings ? 'warning' : 'success',
                        data.message || `Validation complete: ${data.valid_rows || 0} valid, ${data.invalid_rows || 0} invalid.`,
                        detailMessages
                    );
                    if (uploadPaymentsBtn) {
                        uploadPaymentsBtn.style.display = 'inline-block';
                        uploadPaymentsBtn.disabled = false;
                        uploadPaymentsBtn.textContent = 'Upload';
                    }
                    if (cancelPaymentsUploadBtn) cancelPaymentsUploadBtn.style.display = 'inline-block';
                    if (validatePaymentsBtn) validatePaymentsBtn.style.display = 'none';
                } else {
                    showUploadMessage('error', data.message || 'Validation failed', detailMessages);
                    if (uploadPaymentsBtn) uploadPaymentsBtn.style.display = 'none';
                    if (cancelPaymentsUploadBtn) cancelPaymentsUploadBtn.style.display = 'inline-block';
                    if (validatePaymentsBtn) {
                        validatePaymentsBtn.disabled = false;
                        validatePaymentsBtn.textContent = 'Validate';
                    }
                }
                return;
            }

            if (data.success) {
                const hasWarnings = data.duplicates && data.duplicates.length > 0;
                showUploadMessage(
                    hasWarnings ? 'warning' : 'success',
                    data.message || `Successfully uploaded ${data.count} payments`,
                    detailMessages
                );
                window.location.reload();
            } else {
                showUploadMessage('error', data.message || 'Failed to upload payments', detailMessages);
                if (uploadPaymentsBtn) {
                    uploadPaymentsBtn.disabled = false;
                    uploadPaymentsBtn.textContent = 'Upload';
                }
            }
        })
        .catch(error => {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                showUploadMessage('error', validateOnly ? 'Validation timed out' : 'Upload timed out');
                if (validatePaymentsBtn) {
                    validatePaymentsBtn.disabled = false;
                    validatePaymentsBtn.textContent = 'Validate';
                }
                if (uploadPaymentsBtn) {
                    uploadPaymentsBtn.disabled = false;
                    uploadPaymentsBtn.textContent = 'Upload';
                }
            } else {
                console.error('Error:', error);
                showUploadMessage('error', validateOnly ? 'An error occurred while validating payments' : 'An error occurred while uploading payments');
                if (validatePaymentsBtn) {
                    validatePaymentsBtn.disabled = false;
                    validatePaymentsBtn.textContent = 'Validate';
                }
                if (uploadPaymentsBtn) {
                    uploadPaymentsBtn.disabled = false;
                    uploadPaymentsBtn.textContent = 'Upload';
                }
            }
        });
    }
    
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            postPaymentUpload(true);
        });

        if (uploadPaymentsBtn) {
            uploadPaymentsBtn.addEventListener('click', function() {
                postPaymentUpload(false);
            });
        }

        if (paymentsFile) {
            paymentsFile.addEventListener('change', resetUploadActions);
        }

        const uploadModal = document.getElementById('uploadModal');
        if (uploadModal) {
            uploadModal.addEventListener('hidden.bs.modal', function() {
                uploadForm.reset();
                resetUploadActions();
            });
        }
    }
});
