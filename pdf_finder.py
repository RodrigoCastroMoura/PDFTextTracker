import fitz  # PyMuPDF
import re
import unicodedata
import os
import tempfile
import requests
import json
import base64
from PIL import Image
import io
import logging
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)

def normalize_text(text):
    """Normalizes text by removing accents and converting to lowercase"""
    normalized = unicodedata.normalize('NFKD', text)
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
    normalized = normalized.lower()
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def perform_ocr_with_api(image_path):
    """Performs OCR using the OCR.space API"""
    api_key = os.environ.get('OCR_API_KEY', 'K81445401788957')  # Default to demo key

    try:
        with open(image_path, 'rb') as f:
            img_data = f.read()

        base64_image = base64.b64encode(img_data).decode('utf-8')

        payload = {
            'apikey': api_key,
            'language': 'por',
            'base64Image': 'data:image/png;base64,' + base64_image,
            'scale': 'true',
            'isTable': 'false'
        }

        response = requests.post('https://api.ocr.space/parse/image', json=payload)
        result = response.json()

        if result.get('OCRExitCode') == 1:
            extracted_text = ' '.join([page['ParsedText'] for page in result['ParsedResults']])
            return extracted_text
        else:
            error_msg = result.get('ErrorMessage', 'Unknown error')
            logger.error(f"OCR API error: {error_msg}")
            return ""

    except Exception as e:
        logger.error(f"OCR processing error: {str(e)}")
        return ""

def find_signature_lines(page):
    """
    Procura por possíveis locais de assinatura no PDF baseado em padrões comuns
    como linhas de underscore, hífen ou a palavra 'assinatura'
    """
    signature_areas = []

    # Obter todo o texto da página com informações de posicionamento
    words = page.get_text("words")

    for word in words:
        # PyMuPDF words format: [x0, y0, x1, y1, word, block_no, line_no]
        if len(word) >= 5:  # Garantir que temos pelo menos as coordenadas e o texto
            x0, y0, x1, y1, text = word[:5]

            # Verificar padrões de assinatura
            is_signature_line = (
                # Linha de underscore
                text.strip('_') == '' and len(text) >= 5 or
                # Linha de hífen
                text.strip('-') == '' and len(text) >= 5 or
                # Palavra "assinatura"
                'assinatura' in text.lower()
            )

            if is_signature_line:
                # Criar uma área retangular para a linha de assinatura
                signature_area = {
                    'rect': fitz.Rect(x0, y0, x1, y1),
                    'type': 'signature_line',
                    'text': text
                }
                signature_areas.append(signature_area)

    return signature_areas

def process_pdf_signatures(input_pdf_path):
    """Processa o PDF e retorna informações sobre linhas de assinatura encontradas"""
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError("Input PDF file not found")

    doc = fitz.open(input_pdf_path)
    stats = {
        "total_signature_lines": 0,
        "pages_with_signatures": 0,
        "pages_processed": 0,
        "signature_locations": []
    }

    try:
        for page_num, page in enumerate(doc):
            stats["pages_processed"] += 1

            # Encontrar linhas de assinatura
            signature_areas = find_signature_lines(page)

            if signature_areas:
                stats["pages_with_signatures"] += 1
                stats["total_signature_lines"] += len(signature_areas)

                # Armazenar localizações
                for area in signature_areas:
                    stats["signature_locations"].append({
                        "page": page_num,
                        "rect": [area['rect'].x0, area['rect'].y0, area['rect'].x1, area['rect'].y1],
                        "type": "signature_line",
                        "text": area['text']
                    })

        return stats

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise
    finally:
        doc.close()