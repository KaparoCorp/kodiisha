document.addEventListener('DOMContentLoaded', function() {
    const propertiesPage = document.getElementById('propertiesPage');
    const deletePropertiesUrl = propertiesPage ? propertiesPage.dataset.deleteUrl : '/properties/delete/';
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const propertyCheckboxes = document.querySelectorAll('.property-checkbox');
    const deleteSelectedBtn = document.getElementById('deleteSelectedBtn');
    const editButtons = document.querySelectorAll('.editPropertyBtn');
    const editPropertyForm = document.getElementById('editPropertyForm');
    
    // ======================
    // EDIT PROPERTY FUNCTIONALITY
    // ======================
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const propertyId = this.getAttribute('data-property-id');
            
            // Fetch property data
            fetch(`/properties/edit/${propertyId}/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                // Fill form fields
                document.getElementById('editPropertyId').value = data.id;
                document.getElementById('editPropertyName').value = data.name || '';
                document.getElementById('editPropertyAddress').value = data.address || '';
                document.getElementById('editPropertyCounty').value = data.county || '';
                document.getElementById('editPropertyUnits').value = data.total_units || '';
                document.getElementById('editPropertyDescription').value = data.description || '';
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to load property details');
            });
        });
    });
    
    // Handle edit form submission
    if (editPropertyForm) {
        editPropertyForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const propertyId = document.getElementById('editPropertyId').value;
            const formData = new FormData(this);
            
            fetch(`/properties/edit/${propertyId}/`, {
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
                    alert(data.message || 'Failed to update property');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while updating the property');
            });
        });
    }
    
    // ======================
    // DELETE PROPERTIES FUNCTIONALITY
    // ======================
    
    // Select/Deselect all
    selectAllCheckbox.addEventListener('change', function() {
        propertyCheckboxes.forEach(checkbox => {
            checkbox.checked = this.checked;
        });
        updateDeleteButton();
    });
    
    // Update delete button visibility
    propertyCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateDeleteButton);
    });
    
    function updateDeleteButton() {
        const anySelected = Array.from(propertyCheckboxes).some(cb => cb.checked);
        deleteSelectedBtn.style.display = anySelected ? 'inline-block' : 'none';
    }
    
    // Delete selected properties
    deleteSelectedBtn.addEventListener('click', function() {
        const selectedIds = Array.from(propertyCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);
        
        if (selectedIds.length === 0) {
            alert('Please select at least one property to delete');
            return;
        }
        
        if (confirm(`Are you sure you want to delete ${selectedIds.length} property/ies? This action cannot be undone.`)) {
            if (!window.downloadSelectedRowsBeforeDelete('.property-checkbox:checked', 'properties-before-delete')) return;

            const formData = new FormData();
            selectedIds.forEach(id => formData.append('property_ids[]', id));
            
            fetch(deletePropertiesUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value || ''
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);
                    location.reload();
                } else {
                    alert(data.message || 'Failed to delete properties');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while deleting properties');
            });
        }
    });
});
