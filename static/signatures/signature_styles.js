// Predefined SVG signature paths for different styles
const signatureStyles = {
  cursive: {
    fontFamily: "Dancing Script, cursive",
    fontSize: "48px",
    color: "#0B5FE3",
    skewAngle: "-10"
  },
  handwritten: {
    fontFamily: "Homemade Apple, cursive",
    fontSize: "42px",
    color: "#0B5FE3",
    skewAngle: "-5"
  },
  artistic: {
    fontFamily: "Pacifico, cursive",
    fontSize: "44px",
    color: "#0B5FE3",
    skewAngle: "-8"
  }
};

function generateSignatureSVG(name, style) {
  const signatureStyle = signatureStyles[style] || signatureStyles.cursive;
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");

  // Calculate width based on text length
  const width = Math.max(300, name.length * 25);
  const height = 100;

  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("width", "100%");
  svg.setAttribute("height", "100%");

  // Create text element for signature
  const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
  text.setAttribute("x", width/2);
  text.setAttribute("y", height/2);
  text.setAttribute("text-anchor", "middle");
  text.setAttribute("fill", signatureStyle.color);
  text.setAttribute("style", `
    font-family: ${signatureStyle.fontFamily};
    font-size: ${signatureStyle.fontSize};
    transform: skewX(${signatureStyle.skewAngle}deg);
  `);
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