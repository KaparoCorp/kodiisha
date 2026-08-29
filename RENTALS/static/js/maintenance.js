document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('addMaintenanceForm');
    const modal = document.getElementById('addMaintenanceModal');
    const messageDiv = document.getElementById('maintenanceMessage');
    const maintenanceProperty = document.getElementById('maintenanceProperty');
    const maintenanceUnit = document.getElementById('maintenanceUnit');

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

    function setMaintenanceUnitPlaceholder(message, disabled = true) {
        if (!maintenanceUnit) return;
        maintenanceUnit.innerHTML = '';
        const option = document.createElement('option');
        option.value = '';
        option.textContent = message;
        option.selected = true;
        maintenanceUnit.appendChild(option);
        maintenanceUnit.disabled = disabled;
    }

    function buildPropertyUnitsUrl(propertyId) {
        const template = form ? form.dataset.unitsUrlTemplate : '';
        return template ? template.replace('/0/', `/${propertyId}/`) : `/maintenance/property-units/${propertyId}/`;
    }

    function loadMaintenanceUnits(propertyId) {
        if (!propertyId || !maintenanceUnit) {
            setMaintenanceUnitPlaceholder('Select Property First');
            return;
        }

        setMaintenanceUnitPlaceholder('Loading Units...');

        fetch(buildPropertyUnitsUrl(propertyId), {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => response.json())
            .then(data => {
                maintenanceUnit.innerHTML = '';

                if (!data.units || !data.units.length) {
                    setMaintenanceUnitPlaceholder('No Units Found');
                    return;
                }

                const placeholder = document.createElement('option');
                placeholder.value = '';
                placeholder.textContent = 'Select Unit';
                placeholder.selected = true;
                placeholder.disabled = true;
                maintenanceUnit.appendChild(placeholder);

                data.units.forEach(unit => {
                    const option = document.createElement('option');
                    option.value = unit.id;
                    const tenantLabel = unit.tenant ? ` - ${unit.tenant}` : '';
                    option.textContent = `${unit.name}${tenantLabel}`;
                    maintenanceUnit.appendChild(option);
                });

                maintenanceUnit.disabled = false;
            })
            .catch(() => {
                setMaintenanceUnitPlaceholder('Unable To Load Units');
            });
    }

    if (maintenanceProperty && maintenanceUnit) {
        maintenanceProperty.addEventListener('change', function() {
            loadMaintenanceUnits(this.value);
        });
    }

    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(form);
            formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

            fetch("/maintenance/create/", {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(async response => {
                const contentType = response.headers.get('content-type') || '';
                const isJson = contentType.includes('application/json');
                let data = null;
                if (isJson) {
                    data = await response.json();
                } else {
                    data = { success: false, message: `Server error: ${response.status} ${response.statusText}` };
                }

                if (data.success) {
                    messageDiv.className = 'alert alert-success';
                    messageDiv.textContent = data.message;
                    messageDiv.style.display = 'block';
                    form.reset();
                    setTimeout(function() {
                        // `modal` is the raw <div> element, not a Bootstrap Modal
                        // instance. Calling .hide() on it throws a TypeError,
                        // aborting this callback before location.reload() runs
                        // and leaving Bootstrap's .modal-backdrop.fade.show overlay
                        // stuck in front of the page. Resolve the real instance
                        // (created by the data-bs-toggle trigger) instead.
                        const modalInstance = bootstrap.Modal.getInstance(modal);
                        if (modalInstance) {
                            modalInstance.hide();
                        }
                        document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
                        document.body.classList.remove('modal-open');
                        messageDiv.style.display = 'none';
                        window.location.reload();
                    }, 1000);
                } else {
                    messageDiv.className = 'alert alert-danger';
                    if (data.errors && Object.keys(data.errors).length) {
                        const fieldErrors = Object.entries(data.errors)
                            .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
                            .join('\n');
                        messageDiv.textContent = (data.message || 'Please fix the errors below') + '\n' + fieldErrors;
                    } else {
                        messageDiv.textContent = data.message || 'Failed to add maintenance';
                    }
                    messageDiv.style.display = 'block';
                }
            })
            .catch(error => {
                messageDiv.className = 'alert alert-danger';
                messageDiv.textContent = 'An error occurred: ' + (error.message || error);
                messageDiv.style.display = 'block';
            });
        });
    }

    if (modal) {
        modal.addEventListener('hidden.bs.modal', function() {
            form.reset();
            setMaintenanceUnitPlaceholder('Select Property First');
            messageDiv.style.display = 'none';
        });
    }

    const editForm = document.getElementById('editMaintenanceForm');
    const editProperty = document.getElementById('editMaintenanceProperty');
    const editUnit = document.getElementById('editMaintenanceUnit');
    const editModal = document.getElementById('editMaintenanceModal');
    const editMaintenanceIdInput = document.getElementById('editMaintenanceId');
    const editMessageDiv = document.getElementById('editMaintenanceMessage');

    function setEditMaintenanceUnitPlaceholder(message, disabled = true) {
        if (!editUnit) return;
        editUnit.innerHTML = '';
        const option = document.createElement('option');
        option.value = '';
        option.textContent = message;
        option.selected = true;
        editUnit.appendChild(option);
        editUnit.disabled = disabled;
    }

    function loadEditMaintenanceUnits(propertyId) {
        if (!propertyId || !editUnit) {
            setEditMaintenanceUnitPlaceholder('Select Property First');
            return;
        }

        setEditMaintenanceUnitPlaceholder('Loading Units...');

        const template = editForm ? editForm.dataset.unitsUrlTemplate : '';
        const url = template ? template.replace('/0/', `/${propertyId}/`) : `/maintenance/property-units/${propertyId}/`;

        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            editUnit.innerHTML = '';

            if (!data.units || !data.units.length) {
                setEditMaintenanceUnitPlaceholder('No Units Found');
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
            setEditMaintenanceUnitPlaceholder('Unable To Load Units');
        });
    }

    if (editProperty && editUnit) {
        editProperty.addEventListener('change', function() {
            loadEditMaintenanceUnits(this.value);
        });
    }

    document.querySelectorAll('.editMaintenanceBtn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const maintenanceId = this.getAttribute('data-maintenance-id');
            editMaintenanceIdInput.value = maintenanceId;

            fetch(`/maintenance/edit/${maintenanceId}/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (editProperty) editProperty.value = data.property_id;
                    loadEditMaintenanceUnits(data.property_id);
                    if (editUnit) {
                        editUnit.value = data.unit_id;
                        editUnit.disabled = false;
                    }
                    if (document.getElementById('editMaintenanceDate')) document.getElementById('editMaintenanceDate').value = data.date;
                    if (document.getElementById('editMaintenanceDescription')) document.getElementById('editMaintenanceDescription').value = data.description;
                    if (document.getElementById('editMaintenanceAmount')) document.getElementById('editMaintenanceAmount').value = data.amount;
                    if (document.getElementById('editMaintenanceStatus')) document.getElementById('editMaintenanceStatus').value = data.status;

                    const modalInstance = bootstrap.Modal.getOrCreateInstance(editModal);
                    if (modalInstance) {
                        modalInstance.show();
                    }
                } else {
                    alert(data.message || 'Failed to load maintenance data');
                }
            })
            .catch(() => {
                alert('Error loading maintenance data');
            });
        });
    });

    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const maintenanceId = editMaintenanceIdInput ? editMaintenanceIdInput.value : '';
            if (!maintenanceId) return;

            const formData = new FormData(editForm);
            formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

            fetch(`/maintenance/edit/${maintenanceId}/`, {
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
                    const errorText = data.errors ? Object.values(data.errors).flat().join(', ') : (data.message || 'Failed to update maintenance');
                    alert(errorText);
                }
            })
            .catch(() => {
                alert('Error updating maintenance');
            });
        });
    }

    if (editModal) {
        editModal.addEventListener('hidden.bs.modal', function() {
            if (editForm) editForm.reset();
            setEditMaintenanceUnitPlaceholder('Select Property First');
            document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
            document.body.classList.remove('modal-open');
        });
    }

    function isCompletedPage() {
        return window.location.pathname.includes('/maintenance/completed');
    }

    document.querySelectorAll('.status-select').forEach(function(select) {
        select.addEventListener('change', function() {
            const id = this.getAttribute('data-id');
            const newStatus = this.value;
            const row = this.closest('tr');

            fetch(`/maintenance/toggle-status/${id}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(async response => {
                const data = await response.json();
                if (data.success) {
                    this.setAttribute('data-status', data.status);
                    this.value = data.status;
                    if ((isCompletedPage() && data.status === 'pending') || (!isCompletedPage() && data.status === 'completed')) {
                        row.style.transition = 'opacity 0.4s';
                        row.style.opacity = '0';
                        setTimeout(function() {
                            row.remove();
                        }, 400);
                    }
                } else {
                    this.value = this.getAttribute('data-status');
                    alert(data.message || 'Failed to update status');
                }
            })
            .catch(error => {
                this.value = this.getAttribute('data-status');
                alert('An error occurred: ' + (error.message || error));
            });
        });
    });

    document.querySelectorAll('.receipt-form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const id = this.getAttribute('data-id');
            const formData = new FormData(this);
            formData.append('csrfmiddlewaretoken', getCookie('csrftoken'));

            fetch(`/maintenance/attach-receipt/${id}/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(async response => {
                const data = await response.json();
                const messageDiv = document.getElementById(`receiptMessage${id}`);
                if (data.success) {
                    messageDiv.className = 'alert alert-success';
                    messageDiv.textContent = data.message;
                    messageDiv.style.display = 'block';
                    setTimeout(function() {
                        const modalEl = document.getElementById(`receiptModal${id}`);
                        const modalInstance = bootstrap.Modal.getInstance(modalEl);
                        if (modalInstance) {
                            modalInstance.hide();
                        }
                        document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
                        document.body.classList.remove('modal-open');
                        messageDiv.style.display = 'none';
                        window.location.reload();
                    }, 1000);
                } else {
                    messageDiv.className = 'alert alert-danger';
                    messageDiv.textContent = data.message || 'Failed to attach receipt';
                    messageDiv.style.display = 'block';
                }
            })
            .catch(error => {
                const messageDiv = document.getElementById(`receiptMessage${id}`);
                messageDiv.className = 'alert alert-danger';
                messageDiv.textContent = 'An error occurred: ' + (error.message || error);
                messageDiv.style.display = 'block';
            });
        });
    });
});

// ======================
// DELETE MAINTENANCE FUNCTIONALITY
// ======================

(function() {
    const maintenancePage = document.getElementById('maintenancePage');
    const deleteMaintenanceUrl = maintenancePage ? maintenancePage.dataset.deleteUrl : '/maintenance/delete/';
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const maintenanceCheckboxes = document.querySelectorAll('.maintenance-checkbox');
    const deleteSelectedBtn = document.getElementById('deleteSelectedBtn');

    if (selectAllCheckbox && maintenanceCheckboxes.length) {
        selectAllCheckbox.addEventListener('change', function() {
            maintenanceCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateDeleteButton();
        });

        maintenanceCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', updateDeleteButton);
        });

        function updateDeleteButton() {
            const anySelected = Array.from(maintenanceCheckboxes).some(cb => cb.checked);
            deleteSelectedBtn.style.display = anySelected ? 'inline-block' : 'none';
        }

        deleteSelectedBtn.addEventListener('click', function() {
            const selectedIds = Array.from(maintenanceCheckboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.value);

            if (selectedIds.length === 0) {
                alert('Please select at least one maintenance record to delete');
                return;
            }

            if (confirm(`Are you sure you want to delete ${selectedIds.length} maintenance record/s? This action cannot be undone.`)) {
                if (!window.downloadSelectedRowsBeforeDelete('.maintenance-checkbox:checked', 'maintenance-before-delete')) return;

                const formData = new FormData();
                selectedIds.forEach(id => formData.append('maintenance_ids[]', id));

                fetch(deleteMaintenanceUrl, {
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
                        alert(data.message || 'Failed to delete maintenance');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while deleting maintenance');
                });
            }
        });
    }
})();
