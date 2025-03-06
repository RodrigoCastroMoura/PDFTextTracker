
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('pdfForm');
    
    if (form) {
        const submitBtn = document.getElementById('submitBtn');
        if (submitBtn) {
            const spinner = submitBtn.querySelector('.spinner-border');
            
            form.addEventListener('submit', function(e) {
                // Show loading state
                submitBtn.disabled = true;
                if (spinner) {
                    spinner.classList.remove('d-none');
                }
                
                // Remove any existing alerts
                const existingAlerts = document.querySelectorAll('.alert');
                existingAlerts.forEach(alert => alert.remove());
            });
        }

        // File input validation
        const fileInput = document.getElementById('file');
        if (fileInput) {
            fileInput.addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    if (file.type !== 'application/pdf') {
                        alert('Please select a PDF file');
                        fileInput.value = '';
                    } else if (file.size > 10 * 1024 * 1024) { // 10MB limit
                        alert('File size should not exceed 10MB');
                        fileInput.value = '';
                    }
                }
            });
        }

        // Text input validation
        const textInput = document.getElementById('text');
        if (textInput && submitBtn) {
            textInput.addEventListener('input', function(e) {
                const text = e.target.value.trim();
                submitBtn.disabled = text.length === 0;
            });
        }
    }
    
    // Handle form on view_pdf.html page
    const viewPdfForm = document.querySelector('form[action*="process_pdf"]');
    if (viewPdfForm) {
        const searchInput = viewPdfForm.querySelector('input[name="text"]');
        const submitButton = viewPdfForm.querySelector('button[type="submit"]');
        
        if (searchInput && submitButton) {
            // Disable button if search text is empty
            searchInput.addEventListener('input', function() {
                submitButton.disabled = this.value.trim().length === 0;
            });
            
            // Add loading indicator
            viewPdfForm.addEventListener('submit', function() {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span> Processando...';
            });
        }
    }
});
