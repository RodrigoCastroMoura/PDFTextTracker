import fitz  # PyMuPDF
import re
import unicodedata
import os
import logging

logger = logging.getLogger(__name__)

def draw_signature(page, rect, text, style='cursive'):
    """
    Desenha uma assinatura estilizada no PDF usando curvas Bezier para simular escrita manual
    """
    # Cor padrão DocuSign-like
    signature_color = (0.13, 0.36, 0.81)  # Azul DocuSign

    # Calcular posição
    x0 = rect.x0
    y0 = rect.y0 - 12  # Ajustado para ficar mais próximo da linha
    width = rect.width
    height = 20  # Altura aproximada da assinatura

    # Desenhar o nome usando uma curva Bezier para simular escrita cursiva
    control_points = []
    x_step = width / (len(text) + 1)
    baseline = y0 + height * 0.6

    # Criar pontos de controle para a curva principal
    for i, char in enumerate(text):
        x = x0 + i * x_step
        # Variar a altura para criar um efeito mais natural
        y_offset = height * 0.3 * (-1 if i % 2 == 0 else 1)
        control_points.append((x, baseline + y_offset))

    # Desenhar a curva principal
    for i in range(len(control_points) - 1):
        x1, y1 = control_points[i]
        x2, y2 = control_points[i + 1]
        cp1 = (x1 + x_step/3, y1)
        cp2 = (x2 - x_step/3, y2)
        page.draw_bezier((x1, y1), cp1, cp2, (x2, y2), color=signature_color, width=1.5)

    # Adicionar o texto em uma fonte base mais fina
    page.insert_text(
        point=(x0, y0),
        text=text,
        fontsize=16,
        color=signature_color,
        fontname="Helv",
    )

    # Adicionar linha decorativa suave abaixo da assinatura
    line_y = baseline + height * 0.3
    # Linha principal
    page.draw_line(
        (x0, line_y),
        (x0 + width, line_y),
        color=signature_color,
        width=0.7
    )

    # Adicionar pequenas ondulações decorativas na linha
    wave_height = 2
    wave_width = width / 10
    for i in range(10):
        x_start = x0 + i * wave_width
        page.draw_bezier(
            (x_start, line_y),
            (x_start + wave_width/3, line_y + wave_height),
            (x_start + 2*wave_width/3, line_y - wave_height),
            (x_start + wave_width, line_y),
            color=signature_color,
            width=0.3
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