document.addEventListener('DOMContentLoaded', function() {
    // ======================
    // ADD TENANT — UNIT DROPDOWN
    // ======================
    const addTenantProperty = document.getElementById('id_property');
    const addTenantUnit = document.getElementById('addTenantUnit');

    function loadUnitsForProperty(propertyId) {
        if (!addTenantUnit) return;
        addTenantUnit.innerHTML = '<option value="">No Unit</option>';
        if (!propertyId) return;

        addTenantUnit.disabled = true;
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'Loading units...';
        addTenantUnit.appendChild(option);

        fetch(`/tenants/available-units/${propertyId}/`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.json())
        .then(data => {
            addTenantUnit.innerHTML = '<option value="">No Unit</option>';
            if (data.units && data.units.length > 0) {
                data.units.forEach(unit => {
                    const opt = document.createElement('option');
                    opt.value = unit.id;
                    opt.textContent = `${unit.name} — $${unit.rent_amount}`;
                    addTenantUnit.appendChild(opt);
                });
            }
            addTenantUnit.disabled = false;
        })
        .catch(() => {
            addTenantUnit.innerHTML = '<option value="">No Unit</option>';
            addTenantUnit.disabled = false;
        });
    }

    if (addTenantProperty) {
        addTenantProperty.addEventListener('change', function() {
            loadUnitsForProperty(this.value);
        });
    }

    const addTenantModal = document.getElementById('addTenantModal');
    if (addTenantModal) {
        addTenantModal.addEventListener('hidden.bs.modal', function() {
            if (addTenantUnit) {
                addTenantUnit.innerHTML = '<option value="">No Unit</option>';
            }
        });
    }

    // ======================
    // TENANT UPLOAD LOGIC
    // ======================
    const uploadForm = document.getElementById('uploadTenantsForm');
    const validateBtn = document.getElementById('validateTenantsBtn');
    const uploadBtn = document.getElementById('uploadTenantsBtn');
    const validationDiv = document.getElementById('tenantUploadValidation');

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

    function showValidationMessage(type, title, messages = []) {
        if (!validationDiv) return;
        const alertClass = type === 'success' ? 'alert-success' : type === 'info' ? 'alert-info' : 'alert-danger';
        const listHtml = messages.length
            ? `<ul class="mb-0 mt-2">${messages.map(message => `<li>${message}</li>`).join('')}</ul>`
            : '';
        validationDiv.className = `alert ${alertClass}`;
        validationDiv.innerHTML = `<div class="fw-semibold">${title}</div>${listHtml}`;
        validationDiv.style.display = 'block';
    }

    function resetUploadActions() {
        if (uploadBtn) {
            uploadBtn.style.display = 'none';
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Upload';
        }
        if (validateBtn) {
            validateBtn.style.display = 'inline-block';
            validateBtn.disabled = false;
            validateBtn.textContent = 'Validate';
        }
        if (validationDiv) {
            validationDiv.className = 'alert d-none';
            validationDiv.innerHTML = '';
        }
    }

    function getSelectedTenantFile() {
        const fileInput = document.getElementById('tenantsFile');
        const file = fileInput && fileInput.files ? fileInput.files[0] : null;
        if (!file) {
            showValidationMessage('error', 'Please select a file');
            return null;
        }
        const validTypes = ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
        if (!validTypes.includes(file.type) && !file.name.endsWith('.csv') && !file.name.endsWith('.xlsx')) {
            showValidationMessage('error', 'Please upload a CSV or XLSX file');
            return null;
        }
        return file;
    }

    function postTenantUpload(validateOnly) {
        const file = getSelectedTenantFile();
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('csrfmiddlewaretoken', uploadForm.querySelector('[name=csrfmiddlewaretoken]').value);
        if (validateOnly) {
            formData.append('validate_only', '1');
        }

        if (validateOnly && validateBtn) {
            validateBtn.disabled = true;
            validateBtn.textContent = 'Validating...';
        }
        if (!validateOnly && uploadBtn) {
            uploadBtn.disabled = true;
            uploadBtn.textContent = 'Uploading...';
        }

        fetch('/tenants/upload/', {
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
                    showValidationMessage('success', data.message || `Validation complete: ${data.valid_rows || 0} valid, ${data.invalid_rows || 0} invalid.`, detailMessages);
                    if (uploadBtn) {
                        uploadBtn.style.display = 'inline-block';
                        uploadBtn.disabled = false;
                        uploadBtn.textContent = 'Upload';
                    }
                    if (validateBtn) validateBtn.style.display = 'none';
                } else {
                    showValidationMessage('error', data.message || 'Validation failed', detailMessages);
                    if (uploadBtn) uploadBtn.style.display = 'none';
                    if (validateBtn) {
                        validateBtn.disabled = false;
                        validateBtn.textContent = 'Validate';
                    }
                }
                return;
            }

            if (data.success) {
                showValidationMessage('success', data.message || `Successfully uploaded ${data.count} tenants`, detailMessages);
                setTimeout(function() {
                    window.location.reload();
                }, 1500);
            } else {
                showValidationMessage('error', data.message || 'Failed to upload tenants', detailMessages);
                if (uploadBtn) {
                    uploadBtn.disabled = false;
                    uploadBtn.textContent = 'Upload';
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showValidationMessage('error', validateOnly ? 'An error occurred while validating tenants' : 'An error occurred while uploading tenants');
            if (validateBtn) {
                validateBtn.disabled = false;
                validateBtn.textContent = 'Validate';
            }
            if (uploadBtn) {
                uploadBtn.disabled = false;
                uploadBtn.textContent = 'Upload';
            }
        });
    }

    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            postTenantUpload(true);
        });

        if (uploadBtn) {
            uploadBtn.addEventListener('click', function() {
                postTenantUpload(false);
            });
        }

        if (validateBtn) {
            validateBtn.addEventListener('click', function() {
                postTenantUpload(true);
            });
        }

        const uploadModal = document.getElementById('uploadTenantsModal');
        if (uploadModal) {
            uploadModal.addEventListener('hidden.bs.modal', function() {
                uploadForm.reset();
                resetUploadActions();
            });
        }
    }

    // ======================
    // MULTI-SELECT LOGIC
    // ======================
    const selectAllBtn = document.getElementById('selectAllTenants');
    const deleteBtn = document.getElementById('deleteSelectedTenantsBtn');

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
            const checkboxes = document.querySelectorAll('.tenant-checkbox');
            checkboxes.forEach(cb => cb.checked = this.checked);
            toggleDeleteButton();
        });
    }

    // 3. Individual checkbox logic (using delegation)
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('tenant-checkbox')) {
            const allCheckboxes = document.querySelectorAll('.tenant-checkbox');
            const checkedCheckboxes = document.querySelectorAll('.tenant-checkbox:checked');
            
            // Sync the "Select All" checkbox state
            if (selectAllBtn) {
                selectAllBtn.checked = allCheckboxes.length === checkedCheckboxes.length;
            }
            toggleDeleteButton();
        }
    });

    function toggleDeleteButton() {
        const count = document.querySelectorAll('.tenant-checkbox:checked').length;
        if (deleteBtn) {
            deleteBtn.style.display = count > 0 ? 'inline-block' : 'none';
        }
    }

    // 4. The Delete Fetch
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
            const selectedIds = Array.from(document.querySelectorAll('.tenant-checkbox:checked'))
                                     .map(cb => cb.value);

            if (!selectedIds.length) return;
            if (!confirm(`Delete ${selectedIds.length} tenants?`)) return;
            if (!window.downloadSelectedRowsBeforeDelete('.tenant-checkbox:checked', 'tenants-before-delete')) return;

            const formData = new FormData();
            selectedIds.forEach(id => formData.append('tenant_ids[]', id));

            // USE THE ABSOLUTE PATH matching your urls.py
            fetch('/tenants/delete/', {
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

    // 5. Attach Unit — event delegation for dynamically rendered buttons
    document.addEventListener('click', function(e) {
        const attachBtn = e.target.closest('.attach-btn');
        if (!attachBtn) return;

        const tenantId = attachBtn.dataset.tenantId;
        const tenantName = attachBtn.dataset.tenantName;

        document.getElementById('attachTenantId').value = tenantId;
        document.getElementById('attachTenantName').textContent = tenantName;
        document.getElementById('attachUnitInfo').className = 'alert alert-info d-none';
        document.getElementById('attachUnitInfo').textContent = '';
        document.getElementById('attachUnitSelect').innerHTML = '<option value="">-- Select a Unit --</option>';
        document.getElementById('attachUnitSelect').disabled = true;

        const modal = new bootstrap.Modal(document.getElementById('attachUnitModal'));
        modal.show();

        fetch('/tenants/attach-available-units/', {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('attachUnitSelect');
            const info = document.getElementById('attachUnitInfo');
            if (data.units && data.units.length > 0) {
                data.units.forEach(unit => {
                    const option = document.createElement('option');
                    option.value = unit.id;
                    option.textContent = `${unit.name} — ${unit.property__name} ($${unit.rent_amount})`;
                    select.appendChild(option);
                });
                info.textContent = `${data.units.length} vacant unit(s) available.`;
                info.className = 'alert alert-info';
                select.disabled = false;
            } else {
                info.textContent = 'No vacant units available in any accessible property.';
                info.className = 'alert alert-warning';
            }
        })
        .catch(error => {
            console.error('Error loading units:', error);
            document.getElementById('attachUnitInfo').textContent = 'Unable to load units right now.';
            document.getElementById('attachUnitInfo').className = 'alert alert-danger';
        });
    });

    // Attach unit form submission
    const attachUnitForm = document.getElementById('attachUnitForm');
    if (attachUnitForm) {
        attachUnitForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const tenantId = document.getElementById('attachTenantId').value;
            const unitId = document.getElementById('attachUnitSelect').value;
            if (!tenantId || !unitId) {
                alert('Please select a unit to attach.');
                return;
            }

            const formData = new FormData();
            formData.append('unit_id', unitId);
            formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

            fetch(`/tenants/attach/${tenantId}/`, {
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
                    alert(data.message || 'Failed to attach unit.');
                }
            })
            .catch(error => {
                console.error('Error attaching unit:', error);
                alert('An error occurred while attaching the unit.');
            });
        });
    }

    // 6. Detach — event delegation for dynamically rendered buttons
    document.addEventListener('click', function(e) {
        const detachBtn = e.target.closest('.detach-btn');
        if (!detachBtn) return;

        const tenantId = detachBtn.dataset.tenantId;
        const tenantName = detachBtn.dataset.tenantName;

        if (!confirm(`Detach ${tenantName} from their unit?`)) return;

        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

        fetch(`/tenants/detach/${tenantId}/`, {
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
                alert(data.message || 'Failed to detach tenant.');
            }
        })
        .catch(error => {
            console.error('Error detaching tenant:', error);
            alert('An error occurred while detaching the tenant.');
        });
    });

    // 7. Edit Tenant — event delegation for dynamically rendered buttons
    document.addEventListener('click', function(e) {
        const editBtn = e.target.closest('.editTenantBtn');
        if (!editBtn) return;

        const tenantId = editBtn.dataset.tenantId;
        document.getElementById('editTenantId').value = tenantId;

        fetch(`/tenants/edit/${tenantId}/`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('editTenantFirstName').value = data.first_name || '';
                document.getElementById('editTenantLastName').value = data.last_name || '';
                document.getElementById('editTenantPhone').value = data.phone_number || '';
                document.getElementById('editTenantKinName').value = data.next_of_kin_name || '';
                document.getElementById('editTenantKinPhone').value = data.next_of_kin_phone_number || '';
                document.getElementById('editTenantDescription').value = data.description || '';
                document.getElementById('editTenantDepositRequired').checked = data.deposit_required;
                document.getElementById('editTenantDepositAmount').value = data.deposit_amount || 0;
                document.getElementById('editTenantKraPin').value = data.kra_pin || '';
                const propertySelect = document.getElementById('editTenantProperty');
                if (propertySelect) {
                    propertySelect.value = data.property_id || '';
                }

                const frontPreview = document.getElementById('editTenantIdFrontPreview');
                const backPreview = document.getElementById('editTenantIdBackPreview');
                if (frontPreview) {
                    if (data.id_card_front_url) {
                        frontPreview.src = data.id_card_front_url;
                        frontPreview.style.display = 'block';
                    } else {
                        frontPreview.src = '#';
                        frontPreview.style.display = 'none';
                    }
                }
                if (backPreview) {
                    if (data.id_card_back_url) {
                        backPreview.src = data.id_card_back_url;
                        backPreview.style.display = 'block';
                    } else {
                        backPreview.src = '#';
                        backPreview.style.display = 'none';
                    }
                }

                const modal = new bootstrap.Modal(document.getElementById('editTenantModal'));
                modal.show();
            } else {
                alert(data.message || 'Failed to load tenant data');
            }
        })
        .catch(() => {
            alert('Error loading tenant data');
        });
    });

    const editTenantForm = document.getElementById('editTenantForm');
    if (editTenantForm) {
        editTenantForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const tenantId = document.getElementById('editTenantId').value;
            if (!tenantId) return;

            const formData = new FormData();
            formData.append('first_name', document.getElementById('editTenantFirstName').value);
            formData.append('last_name', document.getElementById('editTenantLastName').value);
            formData.append('phone_number', document.getElementById('editTenantPhone').value);
            formData.append('next_of_kin_name', document.getElementById('editTenantKinName').value);
            formData.append('next_of_kin_phone_number', document.getElementById('editTenantKinPhone').value);
            formData.append('description', document.getElementById('editTenantDescription').value);
            formData.append('deposit_required', document.getElementById('editTenantDepositRequired').checked ? 'true' : 'false');
            formData.append('deposit_amount', document.getElementById('editTenantDepositAmount').value);
            formData.append('kra_pin', document.getElementById('editTenantKraPin').value);
            const propertyVal = document.getElementById('editTenantProperty').value;
            if (propertyVal) {
                formData.append('property', propertyVal);
            }
            const idFrontFile = document.getElementById('editTenantIdFront').files[0];
            const idBackFile = document.getElementById('editTenantIdBack').files[0];
            if (idFrontFile) {
                formData.append('id_card_front', idFrontFile);
            }
            if (idBackFile) {
                formData.append('id_card_back', idBackFile);
            }
            formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

            fetch(`/tenants/edit/${tenantId}/`, {
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
                    const modalInstance = bootstrap.Modal.getInstance(document.getElementById('editTenantModal'));
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                    document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
                    document.body.classList.remove('modal-open');
                    setTimeout(function() {
                        window.location.reload();
                    }, 300);
                } else {
                    const errorText = data.errors ? Object.values(data.errors).flat().join(', ') : (data.message || 'Failed to update tenant');
                    alert(errorText);
                }
            })
            .catch(() => {
                alert('Error updating tenant');
            });
        });
    }

    const editTenantModal = document.getElementById('editTenantModal');
    if (editTenantModal) {
        editTenantModal.addEventListener('hidden.bs.modal', function() {
            if (editTenantForm) editTenantForm.reset();
            const frontPreview = document.getElementById('editTenantIdFrontPreview');
            const backPreview = document.getElementById('editTenantIdBackPreview');
            if (frontPreview) {
                frontPreview.src = '#';
                frontPreview.style.display = 'none';
            }
            if (backPreview) {
                backPreview.src = '#';
                backPreview.style.display = 'none';
            }
            document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
            document.body.classList.remove('modal-open');
        });
    }
});
