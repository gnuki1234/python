// ConstructCRM JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Global search functionality
    const globalSearch = document.getElementById('globalSearch');
    if (globalSearch) {
        globalSearch.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = this.value.trim();
                if (query) {
                    // Search tickets by default
                    window.location.href = '/tickets?search=' + encodeURIComponent(query);
                }
            }
        });
    }

    // Account-Contact dynamic filtering
    const accountSelect = document.getElementById('accountSelect');
    const contactSelect = document.getElementById('contactSelect');

    if (accountSelect && contactSelect) {
        accountSelect.addEventListener('change', function() {
            const accountId = this.value;
            if (accountId) {
                fetch('/api/contacts/' + accountId)
                    .then(response => response.json())
                    .then(contacts => {
                        // Clear current options except the first one
                        contactSelect.innerHTML = '<option value="">-- Select Contact --</option>';

                        // Add contacts for selected account
                        contacts.forEach(contact => {
                            const option = document.createElement('option');
                            option.value = contact.id;
                            option.textContent = contact.name;
                            contactSelect.appendChild(option);
                        });
                    })
                    .catch(error => console.error('Error fetching contacts:', error));
            }
        });
    }

    // Add hover effects to table rows
    const tableRows = document.querySelectorAll('.data-table tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.cursor = 'pointer';
        });
    });

    // Initialize tooltips (basic implementation)
    const tooltipElements = document.querySelectorAll('[title]');
    tooltipElements.forEach(el => {
        el.addEventListener('mouseenter', function() {
            this.setAttribute('data-original-title', this.getAttribute('title'));
        });
    });

    // Sidebar active state highlighting
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        const href = item.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            item.classList.add('active');
        }
    });

    // Form validation enhancement
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = 'var(--danger)';
                    field.addEventListener('input', function() {
                        this.style.borderColor = '';
                    }, { once: true });
                }
            });

            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields.');
            }
        });
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K to focus global search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            if (globalSearch) {
                globalSearch.focus();
            }
        }

        // Escape to close modals or unfocus
        if (e.key === 'Escape') {
            if (document.activeElement) {
                document.activeElement.blur();
            }
        }
    });

    // Confirmation for destructive actions
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || 'Are you sure?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    console.log('ConstructCRM initialized');
});
