// Handle password field visibility for registration form
function setupPasswordFieldVisibility() {
    const passwordField = document.querySelector('input[name="password1"]');
    const confirmPasswordContainer = document.getElementById('confirmPasswordContainer');
    const confirmPasswordField = document.querySelector('input[name="password2"]');

    if (passwordField && confirmPasswordContainer && confirmPasswordField) {
        // Show confirm password field on initial load if password already has value
        if (passwordField.value.length > 0) {
            confirmPasswordContainer.style.display = 'block';
            confirmPasswordField.required = true;
        }

        // Listen for input changes to show/hide confirm password
        passwordField.addEventListener('input', function() {
            if (this.value.length > 0) {
                confirmPasswordContainer.style.display = 'block';
                confirmPasswordField.required = true;
            } else {
                confirmPasswordContainer.style.display = 'none';
                confirmPasswordField.required = false;
            }
        });
    }
}

// Attach form submission handler
function attachFormSubmissionHandler() {
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            fetch(this.action || window.location.pathname, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = data.redirect_url || '/accounts/login/';
                } else {
                    // Replace form with the new form HTML that includes errors
                    const formContainer = document.getElementById('formContainer');
                    if (formContainer) {
                        formContainer.innerHTML = data.form_html;
                        // Re-setup password field visibility for the new form
                        setupPasswordFieldVisibility();
                        // Re-attach form submission handler for the new form
                        attachFormSubmissionHandler();
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    setupPasswordFieldVisibility();
    attachFormSubmissionHandler();
});


document.querySelector('form').addEventListener('submit', function(e) {
    e.preventDefault(); // Stop the page from reloading
    
    let formData = new FormData(this);
    
    fetch(window.location.href, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest', // Tells Django it's AJAX
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = data.redirect_url;
        } else {
            // Clear existing errors
            document.querySelectorAll('.text-danger').forEach(el => el.remove());
            
            // Loop through errors and inject them next to the fields
            for (let field in data.errors) {
                let inputElement = document.querySelector(`[name="${field}"]`);
                let errorMsg = document.createElement('small');
                errorMsg.classList.add('text-danger', 'd-block', 'mt-1');
                errorMsg.innerText = data.errors[field];
                inputElement.after(errorMsg);
                
                // Add a red border to the failing field
                inputElement.classList.add('is-invalid');
            }
        }
    });
});

    const form = document.querySelector('form');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault(); // Stop the browser from doing a full page reload

        const formData = new FormData(this);
        
        // Clear previous errors and styling
        document.querySelectorAll('.error-msg').forEach(el => el.remove());
        document.querySelectorAll('.form-control').forEach(el => el.classList.remove('is-invalid'));

        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest', // Tells Django this is an AJAX request
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // If successful, go to the login page
                window.location.href = data.redirect_url;
            } else {
                // If there are errors, loop through the JSON you saw
                for (const field in data.errors) {
                    const input = document.querySelector(`[name="${field}"]`);
                    if (input) {
                        input.classList.add('is-invalid'); // Add red border
                        
                        // Create and insert the error message
                        const errorDiv = document.createElement('div');
                        errorDiv.className = 'error-msg text-danger mt-1 small fw-bold';
                        errorDiv.innerText = data.errors[field][0];
                        input.after(errorDiv);
                    }
                }
            }
        })
        .catch(error => console.error('Error:', error));
    });