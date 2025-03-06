import os
import logging
from flask import Flask, request, send_file, render_template, redirect, url_for, flash, jsonify
import tempfile
from pdf_finder import highlight_text_in_pdf

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key-for-development")

# Configure upload folder
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_pdf():
    try:
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('index'))
        
        file = request.files['file']
        text = request.form.get('text', '').strip()
        use_ocr = request.form.get('use_ocr') == 'on'
        
        if not file or file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('index'))
            
        if not text:
            flash('Please enter text to search', 'error')
            return redirect(url_for('index'))
            
        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload a PDF file.', 'error')
            return redirect(url_for('index'))
        
        # Create temporary files for processing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as input_file:
            input_path = input_file.name
            file.save(input_path)
            
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as output_file:
            output_path = output_file.name
        
        try:
            # Process PDF
            stats = highlight_text_in_pdf(input_path, output_path, text, use_ocr=use_ocr)
            
            # Send processed file
            return send_file(
                output_path,
                as_attachment=True,
                download_name='highlighted.pdf',
                mimetype='application/pdf'
            )
        
        finally:
            # Cleanup temporary files
            try:
                os.unlink(input_path)
                os.unlink(output_path)
            except Exception as e:
                logger.error(f"Error cleaning up temporary files: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        flash(f'Error processing PDF: {str(e)}', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
