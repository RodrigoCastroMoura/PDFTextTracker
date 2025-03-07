// Predefined SVG signature paths for different styles
const signatureStyles = {
  cursive: {
    path: `M10 50 C 20 20, 40 20, 50 50 C 60 70, 80 70, 90 50`,
    style: "stroke:#000; fill:none; stroke-width:2;",
    viewBox: "0 0 100 100"
  },
  handwritten: {
    path: `M10 50 Q 25 25, 40 50 T 70 50 Q 85 75, 100 50`,
    style: "stroke:#000; fill:none; stroke-width:3;",
    viewBox: "0 0 110 100"
  },
  artistic: {
    path: `M10 50 S 30 20, 50 50 S 70 80, 90 50`,
    style: "stroke:#000; fill:none; stroke-width:2.5;",
    viewBox: "0 0 100 100"
  }
};

function generateSignatureSVG(name, style) {
  const signatureStyle = signatureStyles[style] || signatureStyles.cursive;
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", signatureStyle.viewBox);
  svg.setAttribute("width", "100%");
  svg.setAttribute("height", "100%");
  
  // Create path for signature style
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", signatureStyle.path);
  path.setAttribute("style", signatureStyle.style);
  svg.appendChild(path);
  
  // Add text with name
  const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
  text.setAttribute("x", "50");
  text.setAttribute("y", "80");
  text.setAttribute("text-anchor", "middle");
  text.setAttribute("style", "font-family: cursive; font-size: 14px;");
  text.textContent = name;
  svg.appendChild(text);
  
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
