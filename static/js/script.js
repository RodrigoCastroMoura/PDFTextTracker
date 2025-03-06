document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('pdfForm');
    const submitBtn = document.getElementById('submitBtn');
    const spinner = submitBtn.querySelector('.spinner-border');
    
    form.addEventListener('submit', function(e) {
        // Show loading state
        submitBtn.disabled = true;
        spinner.classList.remove('d-none');
        
        // Remove any existing alerts
        const existingAlerts = document.querySelectorAll('.alert');
        existingAlerts.forEach(alert => alert.remove());
    });

    // File input validation
    const fileInput = document.getElementById('file');
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

    // Text input validation
    const textInput = document.getElementById('text');
    textInput.addEventListener('input', function(e) {
        const text = e.target.value.trim();
        submitBtn.disabled = text.length === 0;
    });
});
