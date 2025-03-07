import os
import logging
from flask import Flask, request, send_file, render_template, redirect, url_for, flash
from werkzeug.utils import safe_join
import tempfile
from pdf_finder import process_pdf_signatures
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
    input_path = safe_join(UPLOAD_FOLDER, filename)
    stats = process_pdf_signatures(input_path)

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
        if 'file' not in request.files:
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(url_for('index'))

        file = request.files['file']
        signer_name = request.form.get('signer_name', '').strip()

        if not file or file.filename == '':
            flash('Nenhum arquivo selecionado', 'error')
            return redirect(url_for('index'))

        if not allowed_file(file.filename):
            flash('Tipo de arquivo inválido. Por favor, envie um arquivo PDF.', 'error')
            return redirect(url_for('index'))

        if not signer_name:
            flash('Por favor, forneça o nome do signatário.', 'error')
            return redirect(url_for('index'))

        # Save uploaded file
        input_filename = f"input_{os.path.basename(file.filename)}"
        input_path = safe_join(UPLOAD_FOLDER, input_filename)
        file.save(input_path)

        if not os.path.exists(input_path):
            flash('Arquivo PDF não encontrado', 'error')
            return redirect(url_for('index'))

        # Process PDF to find signature lines and add signer's name
        stats = process_pdf_signatures(input_path, signer_name)

        if stats["total_signature_lines"] > 0:
            msg = f'Documento assinado por {signer_name} em {stats["total_signature_lines"]} locais'
            flash(msg, 'success')
        else:
            flash('Nenhuma linha de assinatura encontrada no documento', 'warning')

        # Use the processed file if available, otherwise use the input file
        view_filename = os.path.basename(stats.get("output_path", input_path))
        return redirect(url_for('view_pdf', filename=view_filename))

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        flash(f'Erro ao processar PDF: {str(e)}', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)