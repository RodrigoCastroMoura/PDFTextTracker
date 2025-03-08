// Predefined SVG signature paths for different styles
const signatureStyles = {
  cursive: {
    path: `M10 50 C 20 20, 40 20, 50 50 C 60 70, 80 70, 90 50 Q 95 40, 100 50`,
    style: "stroke:#0B5FE3; fill:none; stroke-width:2.5;",
    viewBox: "0 0 100 100"
  },
  handwritten: {
    path: `M10 50 Q 25 25, 40 50 T 70 50 Q 85 75, 100 50`,
    style: "stroke:#0B5FE3; fill:none; stroke-width:2.5;",
    viewBox: "0 0 110 100"
  },
  artistic: {
    path: `M10 50 S 30 20, 50 50 S 70 80, 90 50 Q 95 30, 100 50`,
    style: "stroke:#0B5FE3; fill:none; stroke-width:2.5;",
    viewBox: "0 0 100 100"
  }
};

function generateSignatureSVG(name, style) {
  const signatureStyle = signatureStyles[style] || signatureStyles.cursive;
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", signatureStyle.viewBox);
  svg.setAttribute("width", "100%");
  svg.setAttribute("height", "100%");

  // Adicionar um grupo para conter os elementos da assinatura
  const g = document.createElementNS("http://www.w3.org/2000/svg", "g");

  // Criar caminho para a assinatura principal
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", signatureStyle.path);
  path.setAttribute("style", signatureStyle.style);
  g.appendChild(path);

  // Adicionar floreios decorativos
  for (let i = 0; i < 3; i++) {
    const flick = document.createElementNS("http://www.w3.org/2000/svg", "path");
    const x = 20 + i * 30;
    flick.setAttribute("d", `M ${x},50 q 5,-15 10,0`);
    flick.setAttribute("style", signatureStyle.style.replace('2.5', '1.5'));
    g.appendChild(flick);
  }

  svg.appendChild(g);
  return svg;
}

// Function to update signature previews
function updateSignaturePreviews(name) {
  const previews = document.querySelectorAll('.signature-preview');
  previews.forEach(preview => {
    const style = preview.dataset.style;
    preview.innerHTML = '';
    preview.appendChild(generateSignatureSVG(name || 'Nome', style));
  });
}