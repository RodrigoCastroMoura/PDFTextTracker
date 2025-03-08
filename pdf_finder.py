import fitz  # PyMuPDF
import re
import unicodedata
import os
import logging
import io
import base64
from cairosvg import svg2png

logger = logging.getLogger(__name__)

def calculate_font_size(rect_width, text_length):
    """
    Calcula o tamanho ideal da fonte baseado na largura da linha e comprimento do texto
    """
    # Ajustes para documentos médicos e outros tipos de documentos formais
    min_font_size = 28  # Tamanho mínimo legível
    max_font_size = 96  # Tamanho máximo para não ficar desproporcional

    # Cálculo base: largura disponível dividida por caracteres, com fator de ajuste
    ideal_width_per_char = rect_width / (text_length * 1.2)  # 1.2 é um fator de espaçamento
    base_size = ideal_width_per_char * 2.5  # Multiplicador para ajuste fino

    # Ajuste baseado na largura total disponível
    if rect_width < 200:  # Espaço pequeno
        max_font_size = min(max_font_size, rect_width / 3)
    elif rect_width > 500:  # Espaço grande
        min_font_size = max(min_font_size, rect_width / 20)

    # Retorna o tamanho da fonte dentro dos limites estabelecidos
    return max(min(base_size, max_font_size), min_font_size)

def create_signature_svg(text, rect_width):
    """
    Cria um SVG realístico de uma assinatura manuscrita similar ao DocuSign
    """
    # Cor DocuSign
    stroke_color = "#0B5FE3"

    # Calcular tamanho da fonte baseado na largura do retângulo
    font_size = calculate_font_size(rect_width, len(text))

    # Ajustar largura do SVG proporcionalmente
    width = rect_width
    height = font_size * 2  # Altura proporcional à fonte

    # Criar uma string SVG que simula uma assinatura manuscrita
    svg_template = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
        <text x="{width/2}" y="{height/2}"
              text-anchor="middle"
              fill="{stroke_color}"
              font-family="Dancing Script, cursive"
              font-size="{font_size}px"
              transform="skewX(-10)">
            {text}
        </text>
    </svg>
    '''
    return svg_template

def draw_signature(page, rect, text, style='cursive'):
    """
    Insere uma imagem de assinatura no PDF
    """
    try:
        # Gerar SVG da assinatura com tamanho ajustado
        svg_content = create_signature_svg(text, rect.width)

        # Converter SVG para PNG
        png_data = svg2png(
            bytestring=svg_content.encode('utf-8'),
            output_width=int(rect.width),
            background_color='transparent'
        )

        # Criar um objeto de imagem do PyMuPDF
        img = fitz.Pixmap(png_data)

        # Calcular dimensões e posição
        scale_factor = min(rect.width / img.width, 0.4)  # Reduzir altura para ficar mais proporcional
        signature_width = rect.width
        signature_height = img.height * scale_factor

        # Posicionar a imagem acima da linha
        x0 = rect.x0
        y0 = rect.y0 - signature_height * 1.1  # Ajuste fino do espaçamento

        # Inserir a imagem no PDF
        page.insert_image(
            fitz.Rect(x0, y0, x0 + signature_width, y0 + signature_height),
            pixmap=img
        )

    except Exception as e:
        logger.error(f"Erro ao criar assinatura: {str(e)}")
        # Fallback para texto simples em caso de erro
        page.insert_text(
            point=(rect.x0, rect.y0 - 10),
            text=text,
            color=(0, 0, 0.8),
            fontsize=12,
            fontname="Helv"
        )

def find_signature_lines(page):
    """
    Procura por possíveis locais de assinatura no PDF baseado em padrões comuns
    e texto abaixo das linhas
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

    # Padrões específicos para documentos médicos
    medical_patterns = [
        r'crm',
        r'médico',
        r'doutor',
        r'dr\.',
        r'dra\.',
        r'assinatura\s+do\s+médico'
    ]

    for i, y_pos in enumerate(y_positions):
        for word in words_by_y[y_pos]:
            x0, y0, x1, y1, text = word

            # Verificar padrões de assinatura
            is_signature_line = any([
                # Linha de underscore
                text.strip('_') == '' and len(text) >= 5,
                # Linha de hífen
                text.strip('-') == '' and len(text) >= 5,
                # Palavra "assinatura"
                'assinatura' in text.lower(),
                # Padrões médicos
                any(re.search(pattern, text.lower()) for pattern in medical_patterns)
            ])

            if is_signature_line:
                # Procurar texto abaixo da linha
                text_below = ""
                if i + 1 < len(y_positions):
                    next_y = y_positions[i + 1]
                    # Verificar se a próxima linha está próxima (dentro de 20 pontos)
                    if next_y - y1 < 20:
                        # Concatenar todo o texto da linha abaixo
                        text_below = " ".join(word[4] for word in words_by_y[next_y])

                # Ajustar a largura da área de assinatura baseado no contexto
                signature_width = x1 - x0
                if text_below and any(pattern in text_below.lower() for pattern in medical_patterns):
                    signature_width = max(signature_width, 200)  # Garantir espaço mínimo para assinaturas médicas

                # Criar área retangular para a linha de assinatura
                signature_area = {
                    'rect': fitz.Rect(x0, y0, x0 + signature_width, y1),
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

                    # Adicionar assinatura se fornecido
                    if signer_name:
                        draw_signature(page, rect, signer_name, signature_style)

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