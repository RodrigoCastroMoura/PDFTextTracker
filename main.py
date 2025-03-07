import os
import logging
from flask import Flask, request, send_file, render_template, redirect, url_for, flash
from werkzeug.utils import safe_join
import tempfile
from pdf_finder import highlight_text_in_pdf, find_signature_lines
import fitz  # PyMuPDF

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

@app.route('/view/<path:filename>')
def view_pdf(filename):
    if not filename or not os.path.exists(safe_join(UPLOAD_FOLDER, filename)):
        flash('PDF não encontrado', 'error')
        return redirect(url_for('index'))

    # Processar o PDF para encontrar linhas de assinatura
    doc = fitz.open(safe_join(UPLOAD_FOLDER, filename))
    stats = {"signature_lines_found": 0}

    try:
        for page in doc:
            signature_areas = find_signature_lines(page)
            stats["signature_lines_found"] += len(signature_areas)
    finally:
        doc.close()

    return render_template('view_pdf.html', 
                         pdf_path=filename,
                         stats=stats)

@app.route('/pdf/<path:filename>')
def view_pdf_file(filename):
    try:
        file_path = safe_join(UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            flash('PDF não encontrado', 'error')
            return redirect(url_for('index'))
        return send_file(
            file_path,
            mimetype='application/pdf',
            as_attachment=False
        )
    except Exception as e:
        logger.error(f"Error serving PDF file: {str(e)}")
        flash('Erro ao carregar o PDF', 'error')
        return redirect(url_for('index'))

@app.route('/process', methods=['POST'])
def process_pdf():
    try:
        if 'file' not in request.files and 'pdf_path' not in request.form:
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(url_for('index'))

        text = request.form.get('text', '').strip()
        replacement_text = request.form.get('replacement_text', '').strip()
        use_ocr = request.form.get('use_ocr') == 'on'

        if not text:
            flash('Por favor, digite um texto para buscar', 'error')
            return redirect(url_for('index'))

        if not replacement_text:
            flash('Por favor, digite um texto para substituição', 'error')
            return redirect(url_for('index'))

        # Handle file upload or use existing file
        if 'file' in request.files:
            file = request.files['file']
            if not file or file.filename == '':
                flash('Nenhum arquivo selecionado', 'error')
                return redirect(url_for('index'))

            if not allowed_file(file.filename):
                flash('Tipo de arquivo inválido. Por favor, envie um arquivo PDF.', 'error')
                return redirect(url_for('index'))

            # Save uploaded file
            input_filename = f"input_{os.path.basename(file.filename)}"
            input_path = safe_join(UPLOAD_FOLDER, input_filename)
            file.save(input_path)
        else:
            # Use existing file
            input_filename = request.form['pdf_path']
            input_path = safe_join(UPLOAD_FOLDER, input_filename)

        if not os.path.exists(input_path):
            flash('Arquivo PDF não encontrado', 'error')
            return redirect(url_for('index'))

        # Create output filename
        output_filename = f"output_{os.path.basename(input_filename)}"
        output_path = safe_join(UPLOAD_FOLDER, output_filename)

        # Process PDF with replacement text
        stats = highlight_text_in_pdf(
            input_path,
            output_path,
            text,
            use_ocr=use_ocr,
            replacement_text=replacement_text
        )

        # Log processing stats
        logger.info(f"PDF processing stats: {stats}")

        if stats["total_occurrences"] > 0:
            flash(f'Encontradas {stats["total_occurrences"]} ocorrências do texto', 'success')
        else:
            flash('Texto não encontrado no documento', 'warning')

        return redirect(url_for('view_pdf', filename=output_filename))

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        flash(f'Erro ao processar PDF: {str(e)}', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)