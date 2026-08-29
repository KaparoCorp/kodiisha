document.addEventListener('DOMContentLoaded', function() {
    // ======================
    // UNIT UPLOAD LOGIC
    // ======================
    const uploadForm = document.getElementById('uploadUnitsForm');
    const validateBtn = document.getElementById('validateUnitsBtn');
    const uploadBtn = document.getElementById('uploadUnitsBtn');
    const validationDiv = document.getElementById('unitUploadValidation');

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

    function getSelectedUnitFile() {
        const fileInput = document.getElementById('unitsFile');
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

    function postUnitUpload(validateOnly) {
        const file = getSelectedUnitFile();
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

        fetch('/units/upload/', {
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
                showValidationMessage('success', data.message || `Successfully uploaded ${data.count} units`, detailMessages);
                setTimeout(function() {
                    window.location.reload();
                }, 1500);
            } else {
                showValidationMessage('error', data.message || 'Failed to upload units', detailMessages);
                if (uploadBtn) {
                    uploadBtn.disabled = false;
                    uploadBtn.textContent = 'Upload';
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showValidationMessage('error', validateOnly ? 'An error occurred while validating units' : 'An error occurred while uploading units');
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
            postUnitUpload(true);
        });

        if (uploadBtn) {
            uploadBtn.addEventListener('click', function() {
                postUnitUpload(false);
            });
        }

        if (validateBtn) {
            validateBtn.addEventListener('click', function() {
                postUnitUpload(true);
            });
        }

        const uploadModal = document.getElementById('uploadUnitsModal');
        if (uploadModal) {
            uploadModal.addEventListener('hidden.bs.modal', function() {
                uploadForm.reset();
                resetUploadActions();
            });
        }
    }

    const unitsPage = document.getElementById('unitsPage');
    const deleteUnitsUrl = unitsPage ? unitsPage.dataset.deleteUrl : '/units/delete/';
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const unitCheckboxes = document.querySelectorAll('.unit-checkbox');
    const deleteSelectedBtn = document.getElementById('deleteSelectedBtn');
    const assignButtons = document.querySelectorAll('.assignTenantBtn');
    const detachButtons = document.querySelectorAll('.detachTenantBtn');
    const assignTenantForm = document.getElementById('assignTenantForm');
    
    // ======================
    // ASSIGN TENANT FUNCTIONALITY
    // ======================
    assignButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const unitId = this.getAttribute('data-unit-id');
            const unitName = this.getAttribute('data-unit-name');
            
            // Set unit info in modal
            document.getElementById('assignUnitId').value = unitId;
            document.getElementById('assignUnitName').textContent = unitName;
            
            // Fetch available tenants
            fetch(`/units/assign/${unitId}/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                const tenantSelect = document.getElementById('assignTenantSelect');
                tenantSelect.innerHTML = '<option value="">-- Select a Tenant --</option>';
                
                if (data.tenants && data.tenants.length > 0) {
                    data.tenants.forEach(tenant => {
                        const option = document.createElement('option');
                        option.value = tenant.id;
                        option.textContent = `${tenant.first_name} ${tenant.last_name}`;
                        tenantSelect.appendChild(option);
                    });
                } else {
                    const option = document.createElement('option');
                    option.textContent = 'No available tenants';
                    option.disabled = true;
                    tenantSelect.appendChild(option);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to load tenants');
            });
        });
    });
    
    // Handle assign form submission
    if (assignTenantForm) {
        assignTenantForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const unitId = document.getElementById('assignUnitId').value;
            const tenantId = document.getElementById('assignTenantSelect').value;
            
            if (!tenantId) {
                alert('Please select a tenant');
                return;
            }
            
            const formData = new FormData();
            formData.append('tenant_id', tenantId);
            formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
            
            fetch(`/units/assign/${unitId}/`, {
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
                    alert(data.message || 'Failed to assign tenant');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while assigning the tenant');
            });
        });
    }
    
    // ======================
    // DETACH TENANT FUNCTIONALITY
    // ======================
    detachButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const unitId = this.getAttribute('data-unit-id');
            const unitName = this.getAttribute('data-unit-name');
            
            if (confirm(`Are you sure you want to detach the tenant from ${unitName}?`)) {
                const formData = new FormData();
                formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
                
                fetch(`/units/detach/${unitId}/`, {
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
                        alert(data.message || 'Failed to detach tenant');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while detaching the tenant');
                });
            }
        });
    });

    // ======================
    // EDIT UNIT FUNCTIONALITY
    // ======================
    const editUnitButtons = document.querySelectorAll('.editUnitBtn');
    const editUnitModal = document.getElementById('editUnitModal');
    const editUnitForm = document.getElementById('editUnitForm');
    const editUnitIdInput = document.getElementById('editUnitId');
    const editUnitProperty = document.getElementById('editUnitProperty');
    const editUnitName = document.getElementById('editUnitName');
    const editUnitRent = document.getElementById('editUnitRent');
    const editUnitDesc = document.getElementById('editUnitDesc');

    editUnitButtons.forEach(button => {
        button.addEventListener('click', function() {
            const unitId = this.getAttribute('data-unit-id');
            editUnitIdInput.value = unitId;

            fetch(`/units/edit/${unitId}/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (editUnitProperty) editUnitProperty.value = data.property_id;
                    if (editUnitName) editUnitName.value = data.name;
                    if (editUnitRent) editUnitRent.value = data.rent_amount;
                    if (editUnitDesc) editUnitDesc.value = data.description;

                    const modalInstance = bootstrap.Modal.getOrCreateInstance(editUnitModal);
                    if (modalInstance) {
                        modalInstance.show();
                    }
                } else {
                    alert(data.message || 'Failed to load unit data');
                }
            })
            .catch(() => {
                alert('Error loading unit data');
            });
        });
    });

    if (editUnitForm) {
        editUnitForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const unitId = editUnitIdInput ? editUnitIdInput.value : '';
            if (!unitId) return;

            const formData = new FormData();
            formData.append('property', editUnitProperty ? editUnitProperty.value : '');
            formData.append('name', editUnitName ? editUnitName.value : '');
            formData.append('rent_amount', editUnitRent ? editUnitRent.value : '');
            formData.append('description', editUnitDesc ? editUnitDesc.value : '');
            formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

            fetch(`/units/edit/${unitId}/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const modalInstance = bootstrap.Modal.getInstance(editUnitModal);
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                    document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
                    document.body.classList.remove('modal-open');
                    setTimeout(function() {
                        window.location.reload();
                    }, 300);
                } else {
                    const errorText = data.errors ? Object.values(data.errors).flat().join(', ') : (data.message || 'Failed to update unit');
                    alert(errorText);
                }
            })
            .catch(() => {
                alert('Error updating unit');
            });
        });
    }

    if (editUnitModal) {
        editUnitModal.addEventListener('hidden.bs.modal', function() {
            if (editUnitForm) editUnitForm.reset();
            document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
            document.body.classList.remove('modal-open');
        });
    }

    const addUnitModal = document.getElementById('addUnitModal');
    const addUnitForm = addUnitModal ? addUnitModal.querySelector('form') : null;
    const statusSelect = document.getElementById('id_status');
    const propertySelect = document.getElementById('id_property');
    const tenantSelect = document.getElementById('unitTenantSelect');
    const tenantSelectContainer = document.getElementById('tenantSelectContainer');

    function updateTenantDropdown() {
        if (!statusSelect || !propertySelect || !tenantSelect || !tenantSelectContainer) return;

        const propertyId = propertySelect.value;
        if (statusSelect.value === 'occupied' && propertyId) {
            tenantSelectContainer.style.display = 'block';
            fetch(`/units/available-tenants/${propertyId}/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                tenantSelect.innerHTML = '<option value="">-- Select Tenant --</option>';
                if (data.tenants && data.tenants.length > 0) {
                    data.tenants.forEach(tenant => {
                        const option = document.createElement('option');
                        option.value = tenant.id;
                        option.textContent = `${tenant.first_name} ${tenant.last_name}`;
                        tenantSelect.appendChild(option);
                    });
                } else {
                    const option = document.createElement('option');
                    option.value = '';
                    option.textContent = 'No available tenants';
                    option.disabled = true;
                    tenantSelect.appendChild(option);
                }
            })
            .catch(() => {
                tenantSelect.innerHTML = '<option value="">-- Select Tenant --</option>';
            });
        } else {
            tenantSelectContainer.style.display = 'none';
            tenantSelect.innerHTML = '<option value="">-- Select Tenant --</option>';
        }
    }

    if (statusSelect) {
        statusSelect.addEventListener('change', updateTenantDropdown);
    }
    if (propertySelect) {
        propertySelect.addEventListener('change', updateTenantDropdown);
    }
    if (addUnitModal) {
        addUnitModal.addEventListener('hidden.bs.modal', function() {
            if (statusSelect) statusSelect.value = '';
            if (tenantSelect) tenantSelect.innerHTML = '<option value="">-- Select Tenant --</option>';
            if (tenantSelectContainer) tenantSelectContainer.style.display = 'none';
            if (addUnitForm) addUnitForm.reset();
        });
    }
    
// ======================
// DELETE UNITS FUNCTIONALITY
// ======================

function csvEscape(value) {
    const text = String(value == null ? '' : value);
    if (/[",\n]/.test(text)) {
        return `"${text.replace(/"/g, '""')}"`;
    }
    return text;
}

function downloadRelatedDataCSV(blockName, records, timestampStr) {
    if (!records || records.length === 0) return;
    const keys = Object.keys(records[0]);
    const headers = keys.map(k => csvEscape(k)).join(',');
    const rows = records.map(record =>
        keys.map(k => csvEscape(record[k])).join(',')
    );
    const csv = [headers, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${blockName}-${timestampStr}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
}

function formatBlockName(name) {
    return name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

selectAllCheckbox.addEventListener('change', function() {
    unitCheckboxes.forEach(checkbox => {
        checkbox.checked = this.checked;
    });
    updateDeleteButton();
});

unitCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', updateDeleteButton);
});

function updateDeleteButton() {
    const anySelected = Array.from(unitCheckboxes).some(cb => cb.checked);
    deleteSelectedBtn.style.display = anySelected ? 'inline-block' : 'none';
}

deleteSelectedBtn.addEventListener('click', function() {
    const selectedIds = Array.from(unitCheckboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.value);

    if (selectedIds.length === 0) {
        alert('Please select at least one unit to delete');
        return;
    }

    const relatedDataModal = document.getElementById('deleteUnitModal');
    const modalBody = document.getElementById('deleteUnitModalBody');
    const confirmBtn = document.getElementById('confirmDeleteUnitBtn');

    modalBody.innerHTML = '<div class="text-center py-3"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';

    const relatedDataModalInstance = new bootstrap.Modal(relatedDataModal);
    relatedDataModalInstance.show();

    const formData = new FormData();
    selectedIds.forEach(id => formData.append('unit_ids[]', id));

    fetch('/units/related-data/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value || '',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            alert(data.message || 'Failed to load related data');
            relatedDataModalInstance.hide();
            return;
        }

        const relatedData = data.related_data;
        const blockNames = Object.keys(relatedData);
        const hasData = blockNames.some(name => relatedData[name].count > 0);

        if (!hasData) {
            modalBody.innerHTML = '<p class="text-center mb-0">No related data found. The unit(s) will be deleted directly.</p>';
        } else {
            let html = '<div class="list-group list-group-flush">';
            blockNames.forEach(name => {
                const info = relatedData[name];
                const count = info.count;
                const label = formatBlockName(name);
                html += `
                    <div class="list-group-item d-flex align-items-center justify-content-between py-2">
                        <div>
                            <strong>${label}</strong>
                            ${count > 0 ? `<span class="badge bg-secondary ms-2">${count}</span>` : ''}
                            ${info.note ? `<small class="text-muted d-block">${info.note}</small>` : ''}
                        </div>
                        ${count > 0 ? `<input type="checkbox" class="form-check-input download-block-check" value="${name}" checked>` : ''}
                    </div>`;
            });
            html += '</div>';
            modalBody.innerHTML = html;
        }

        confirmBtn.onclick = function() {
            const downloadBlocks = [];
            modalBody.querySelectorAll('.download-block-check:checked').forEach(cb => {
                downloadBlocks.push(cb.value);
            });

            relatedDataModalInstance.hide();

            if (downloadBlocks.length > 0) {
                const timestampStr = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
                downloadBlocks.forEach(blockName => {
                    const records = relatedData[blockName].sample || [];
                    if (records.length > 0) {
                        downloadRelatedDataCSV(blockName, records, timestampStr);
                    }
                });
            }

            const deleteFormData = new FormData();
            selectedIds.forEach(id => deleteFormData.append('unit_ids[]', id));
            deleteFormData.append('download_blocks', JSON.stringify(downloadBlocks));

            fetch(deleteUnitsUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value || '',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: deleteFormData
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    alert(result.message);
                    location.reload();
                } else {
                    alert(result.message || 'Failed to delete units');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while deleting units');
            });
        };
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while loading related data');
        relatedDataModalInstance.hide();
    });
});
});
