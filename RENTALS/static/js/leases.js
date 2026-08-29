document.addEventListener('DOMContentLoaded', function() {
    const propertyFilter = document.getElementById('leasePropertyFilter');
    const unitFilter = document.getElementById('leaseUnitFilter');

    if (!propertyFilter || !unitFilter) {
        return;
    }

    function setUnitOptions(units) {
        unitFilter.innerHTML = '';

        const allUnitsOption = document.createElement('option');
        allUnitsOption.value = '';
        allUnitsOption.textContent = 'All Units';
        unitFilter.appendChild(allUnitsOption);

        units.forEach(function(unit) {
            const option = document.createElement('option');
            option.value = unit.id;
            option.textContent = `${unit.name} (${unit.property})`;
            unitFilter.appendChild(option);
        });
    }

    function loadUnitsForProperty(propertyId) {
        const unitsUrl = unitFilter.dataset.unitsUrl || '/leases/units/';
        const url = propertyId ? `${unitsUrl}?property=${encodeURIComponent(propertyId)}` : unitsUrl;

        unitFilter.disabled = true;
        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('Unable to load units');
                }
                return response.json();
            })
            .then(function(data) {
                setUnitOptions(data.units || []);
            })
            .catch(function() {
                setUnitOptions([]);
            })
            .finally(function() {
                unitFilter.disabled = false;
            });
    }

    propertyFilter.addEventListener('change', function() {
        unitFilter.value = '';
        loadUnitsForProperty(this.value);
    });

    // ======================
    // ADD LEASE MODAL
    // ======================
    const addLeaseModal = document.getElementById('addLeaseModal');
    const addLeaseForm = document.getElementById('addLeaseForm');
    const leasePropertySelect = document.getElementById('leasePropertySelect');
    const leaseUnitSelect = document.getElementById('leaseUnitSelect');
    const leaseTenantSelect = document.getElementById('leaseTenantSelect');

    if (addLeaseModal && addLeaseForm && leasePropertySelect && leaseUnitSelect && leaseTenantSelect) {
        function setLeaseUnitOptions(units) {
            leaseUnitSelect.innerHTML = '<option value="">-- Select Unit --</option>';
            units.forEach(function(unit) {
                const option = document.createElement('option');
                option.value = unit.id;
                option.textContent = `${unit.name} (KES ${unit.rent_amount})`;
                leaseUnitSelect.appendChild(option);
            });
        }

        function setLeaseTenantOptions(tenants) {
            leaseTenantSelect.innerHTML = '<option value="">-- Select Tenant --</option>';
            tenants.forEach(function(tenant) {
                const option = document.createElement('option');
                option.value = tenant.id;
                option.textContent = `${tenant.first_name} ${tenant.last_name}`;
                leaseTenantSelect.appendChild(option);
            });
        }

        leasePropertySelect.addEventListener('change', function() {
            const propertyId = this.value;
            leaseUnitSelect.innerHTML = '<option value="">-- Select Property First --</option>';
            leaseTenantSelect.innerHTML = '<option value="">-- Select Unit First --</option>';
            if (!propertyId) return;

            fetch(`/leases/units/?property=${encodeURIComponent(propertyId)}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                setLeaseUnitOptions(data.units || []);
            })
            .catch(function() {
                setLeaseUnitOptions([]);
            });
        });

        leaseUnitSelect.addEventListener('change', function() {
            const unitId = this.value;
            leaseTenantSelect.innerHTML = '<option value="">-- Select Unit First --</option>';
            if (!unitId) return;

            fetch(`/leases/tenants/?unit=${encodeURIComponent(unitId)}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                setLeaseTenantOptions(data.tenants || []);
            })
            .catch(function() {
                setLeaseTenantOptions([]);
            });
        });

        addLeaseForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const unitId = leaseUnitSelect.value;
            const tenantId = leaseTenantSelect.value;
            const startDate = document.getElementById('leaseStartDate').value;
            const depositHeld = document.getElementById('leaseDepositHeld').value;

            if (!unitId || !tenantId) {
                alert('Please select both a unit and a tenant');
                return;
            }

            const formData = new FormData();
            formData.append('unit_id', unitId);
            formData.append('tenant_id', tenantId);
            formData.append('start_date', startDate);
            formData.append('deposit_held', depositHeld);
            formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

            fetch('/leases/create/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.success) {
                    alert(data.message);
                    location.reload();
                } else {
                    alert(data.message || 'Failed to create lease');
                }
            })
            .catch(function(error) {
                console.error('Error:', error);
                alert('An error occurred while creating the lease');
            });
        });

        addLeaseModal.addEventListener('hidden.bs.modal', function() {
            addLeaseForm.reset();
            leaseUnitSelect.innerHTML = '<option value="">-- Select Property First --</option>';
            leaseTenantSelect.innerHTML = '<option value="">-- Select Unit First --</option>';
        });
    }
});
