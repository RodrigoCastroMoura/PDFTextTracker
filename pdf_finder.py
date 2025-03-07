import fitz  # PyMuPDF
import re
import unicodedata
import os
import logging
import io
import base64
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

logger = logging.getLogger(__name__)

# Definição dos estilos de assinatura SVG
SIGNATURE_STYLES = {
    'cursive': {
        'path': 'M10 50 C 20 20, 40 20, 50 50 C 60 70, 80 70, 90 50',
        'style': 'stroke:#000066; fill:none; stroke-width:2;',
        'viewBox': '0 0 100 100'
    },
    'handwritten': {
        'path': 'M10 50 Q 25 25, 40 50 T 70 50 Q 85 75, 100 50',
        'style': 'stroke:#000066; fill:none; stroke-width:3;',
        'viewBox': '0 0 110 100'
    },
    'artistic': {
        'path': 'M10 50 S 30 20, 50 50 S 70 80, 90 50',
        'style': 'stroke:#000066; fill:none; stroke-width:2.5;',
        'viewBox': '0 0 100 100'
    }
}

def create_signature_svg(name, style):
    """Cria um SVG de assinatura com o nome e estilo especificados"""
    signature_style = SIGNATURE_STYLES.get(style, SIGNATURE_STYLES['cursive'])

    svg_template = f'''
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="{signature_style['viewBox']}">
        <path d="{signature_style['path']}" style="{signature_style['style']}" />
        <text x="50" y="80" text-anchor="middle" 
              style="font-family: Arial; font-size: 14px; fill: #000066;">
            {name}
        </text>
    </svg>
    '''
    return svg_template

def svg_to_png(svg_content):
    """Converte SVG para PNG"""
    drawing = svg2rlg(io.StringIO(svg_content))
    return renderPM.drawToString(drawing, fmt='PNG')

def find_signature_lines(page):
    """
    Procura por possíveis locais de assinatura no PDF baseado em padrões comuns
    como linhas de underscore, hífen ou a palavra 'assinatura'
    """
    signature_areas = []

    # Obter todo o texto da página com informações de posicionamento
    words = page.get_text("words")

    # Organizar palavras por posição vertical (y)
    words_by_y = {}
    for word in words:
        if len(word) >= 5:  # Garantir que temos pelo menos as coordenadas e o texto
            x0, y0, x1, y1, text = word[:5]
            if y0 not in words_by_y:
                words_by_y[y0] = []
            words_by_y[y0].append((x0, y0, x1, y1, text))

    # Ordenar as coordenadas y
    y_positions = sorted(words_by_y.keys())

    for i, y_pos in enumerate(y_positions):
        for word in words_by_y[y_pos]:
            x0, y0, x1, y1, text = word

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
                # Procurar texto abaixo da linha
                text_below = ""
                if i + 1 < len(y_positions):
                    next_y = y_positions[i + 1]
                    # Verificar se a próxima linha está próxima (dentro de 20 pontos)
                    if next_y - y1 < 20:
                        # Concatenar todo o texto da linha abaixo
                        text_below = " ".join(word[4] for word in words_by_y[next_y])

                # Criar uma área retangular para a linha de assinatura
                signature_area = {
                    'rect': fitz.Rect(x0, y0, x1, y1),
                    'type': 'signature_line',
                    'text': text,
                    'text_below': text_below,
                    'has_description': bool(text_below.strip())
                }
                signature_areas.append(signature_area)

    return signature_areas

def process_pdf_signatures(input_pdf_path, signer_name=None, signature_style='cursive'):
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
        "signer_name": signer_name
    }

    try:
        if signer_name:
            # Criar SVG da assinatura
            svg_content = create_signature_svg(signer_name, signature_style)
            # Converter SVG para PNG
            png_data = svg_to_png(svg_content)

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
                        "text": area['text'],
                        "text_below": area['text_below'],
                        "has_description": area['has_description']
                    })

                    # Adicionar assinatura como imagem
                    if signer_name:
                        # Calcular dimensões e posição da assinatura
                        signature_width = rect.width
                        signature_height = signature_width * 0.5  # Proporção 2:1
                        x0 = rect.x0
                        y0 = rect.y0 - signature_height - 2  # 2 pontos acima da linha

                        # Inserir a imagem da assinatura
                        page.insert_image(
                            fitz.Rect(x0, y0, x0 + signature_width, y0 + signature_height),
                            stream=png_data
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

def normalize_text(text):
    """Normalizes text by removing accents and converting to lowercase"""
    normalized = unicodedata.normalize('NFKD', text)
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
    normalized = normalized.lower()
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized