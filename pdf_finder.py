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

def highlight_text_in_pdf(input_pdf_path, output_pdf_path, text_to_find, highlight_color=(1, 1, 0), use_ocr=False, replacement_text=None):
    """Searches and highlights text in a PDF with optional OCR support and text replacement"""
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError("Input PDF file not found")

    doc = fitz.open(input_pdf_path)
    normalized_text = normalize_text(text_to_find)

    stats = {
        "total_occurrences": 0,
        "pages_with_occurrences": 0,
        "pages_processed": 0,
        "ocr_used": False,
        "locations": []  # Store locations of found text
    }

    try:
        for page_num, page in enumerate(doc):
            stats["pages_processed"] += 1
            page_occurrences = 0

            # Try direct text search first
            page_text = page.get_text()
            normalized_page_text = normalize_text(page_text)
            instances = page.search_for(text_to_find, quads=False)

            # Try normalized text search
            if not instances and normalized_text in normalized_page_text:
                words = page.get_text("words")
                for word in words:
                    x0, y0, x1, y1, text, _, _ = word
                    if normalized_text in normalize_text(text):
                        instances.append(fitz.Rect(x0, y0, x1, y1))

            # Try OCR if enabled and no text found
            if not instances and use_ocr:
                stats["ocr_used"] = True
                with tempfile.NamedTemporaryFile(suffix='.png', delete=True) as temp_img:
                    pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                    pix.save(temp_img.name)

                    ocr_text = perform_ocr_with_api(temp_img.name)
                    if ocr_text and (text_to_find.lower() in ocr_text.lower() or 
                                   normalized_text in normalize_text(ocr_text)):
                        # Create highlight area for OCR match
                        width, height = page.rect.width, page.rect.height
                        rect = fitz.Rect(
                            width * 0.1, height * 0.3,
                            width * 0.9, height * 0.7
                        )
                        instances.append(rect)

            # Apply highlights and replacements
            for inst in instances:
                # Store location information
                stats["locations"].append({
                    "page": page_num,
                    "rect": [inst.x0, inst.y0, inst.x1, inst.y1]
                })

                # Add highlight
                highlight = page.add_highlight_annot(inst)
                highlight.set_colors(stroke=highlight_color)
                highlight.update()

                # Add replacement text if provided
                if replacement_text:
                    # Position replacement text at same height and 1cm to the right
                    replacement_rect = fitz.Rect(
                        inst.x0 + 28.35,    # 1cm to the right
                        inst.y0,            # same height as original
                        inst.x1 + 28.35,    # maintain same width
                        inst.y0 + 28.35     # 1cm height for text
                    )
                    page.insert_text(
                        replacement_rect.tl,  # top-left point
                        replacement_text,
                        color=(0, 0, 1),     # Blue color for replacement
                        fontsize=14,         # Slightly larger font
                        fontname="CoBO",     # Comic Bold - mais parecido com assinatura
                        overlay=True
                    )

                page_occurrences += 1

            stats["total_occurrences"] += page_occurrences
            if page_occurrences > 0:
                stats["pages_with_occurrences"] += 1

        doc.save(output_pdf_path)
        return stats

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise
    finally:
        doc.close()