import fitz  # PyMuPDF
import re
import unicodedata
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def normalize_text(text):
    """Normalizes text by removing accents and converting to lowercase"""
    normalized = unicodedata.normalize('NFKD', text)
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
    normalized = normalized.lower()
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

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

def process_pdf_signatures(input_pdf_path, signer_name=None):
    """Processa o PDF e retorna informações sobre linhas de assinatura encontradas"""
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError("Input PDF file not found")

    # Criar nome do arquivo de saída
    output_path = input_pdf_path.replace('.pdf', '_assinado.pdf')

    doc = fitz.open(input_pdf_path)
    stats = {
        "total_signature_lines": 0,
        "pages_with_signatures": 0,
        "pages_processed": 0,
        "signature_locations": [],
        "output_path": output_path,
        "signer_name": signer_name,
        "signed_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }

    try:
        for page_num, page in enumerate(doc):
            stats["pages_processed"] += 1

            # Encontrar linhas de assinatura
            signature_areas = find_signature_lines(page)

            if signature_areas:
                stats["pages_with_signatures"] += 1
                stats["total_signature_lines"] += len(signature_areas)

                # Armazenar localizações e adicionar assinatura se fornecido
                for area in signature_areas:
                    rect = area['rect']
                    stats["signature_locations"].append({
                        "page": page_num,
                        "rect": [rect.x0, rect.y0, rect.x1, rect.y1],
                        "type": "signature_line",
                        "text": area['text']
                    })

                    # Adicionar assinatura digital acima da linha
                    if signer_name:
                        # Adicionar nome como assinatura
                        page.insert_text(
                            point=(rect.x0, rect.y0 - 1.4175),  # 0.5mm acima da linha
                            text=signer_name,
                            color=(0, 0, 1),     # Cor azul
                            fontsize=16,         # Tamanho da fonte
                            fontname="Helv",     # Fonte padrão
                            render_mode=0        # Modo normal
                        )

                        # Adicionar data e hora da assinatura
                        page.insert_text(
                            point=(rect.x0, rect.y0 + rect.height + 2.835),  # 1mm abaixo da linha
                            text=f"Assinado digitalmente em {stats['signed_at']}",
                            color=(0, 0, 0),     # Cor preta
                            fontsize=8,          # Fonte menor
                            fontname="Helv",     # Fonte padrão
                            render_mode=0        # Modo normal
                        )

        # Salvar em um novo arquivo se houver assinatura
        if signer_name:
            doc.save(output_path)

        return stats

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise
    finally:
        doc.close()