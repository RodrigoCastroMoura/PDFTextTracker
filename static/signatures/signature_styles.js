// Predefined SVG signature paths for different styles
const signatureStyles = {
  cursive: {
    fontFamily: "Dancing Script, cursive",
    fontSize: "48px",
    color: "#0B5FE3",
    skewAngle: "-10"
  },
  elegant: {
    fontFamily: "Alex Brush, cursive",
    fontSize: "52px",
    color: "#0B5FE3",
    skewAngle: "-8"
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
  },
  formal: {
    fontFamily: "Mr De Haviland, cursive",
    fontSize: "50px",
    color: "#0B5FE3",
    skewAngle: "-12"
  }
};

let isDrawing = false;
let signatureCanvas = null;
let ctx = null;

function initializeDrawingCanvas(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  // Create canvas for drawing
  signatureCanvas = document.createElement('canvas');
  signatureCanvas.width = container.offsetWidth;
  signatureCanvas.height = 200;
  signatureCanvas.style.border = '1px solid var(--bs-gray-400)';
  signatureCanvas.style.backgroundColor = 'white';
  container.appendChild(signatureCanvas);

  ctx = signatureCanvas.getContext('2d');
  ctx.strokeStyle = '#0B5FE3';
  ctx.lineWidth = 2;
  ctx.lineCap = 'round';

  // Add drawing event listeners
  signatureCanvas.addEventListener('mousedown', startDrawing);
  signatureCanvas.addEventListener('mousemove', draw);
  signatureCanvas.addEventListener('mouseup', stopDrawing);
  signatureCanvas.addEventListener('mouseleave', stopDrawing);

  // Add touch support
  signatureCanvas.addEventListener('touchstart', handleTouch);
  signatureCanvas.addEventListener('touchmove', handleTouch);
  signatureCanvas.addEventListener('touchend', stopDrawing);
}

function startDrawing(e) {
  isDrawing = true;
  ctx.beginPath();
  const rect = signatureCanvas.getBoundingClientRect();
  ctx.moveTo(e.clientX - rect.left, e.clientY - rect.top);
}

function draw(e) {
  if (!isDrawing) return;
  const rect = signatureCanvas.getBoundingClientRect();
  ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top);
  ctx.stroke();
}

function stopDrawing() {
  isDrawing = false;
}

function handleTouch(e) {
  e.preventDefault();
  const touch = e.touches[0];
  const mouseEvent = new MouseEvent(e.type === 'touchstart' ? 'mousedown' : 'mousemove', {
    clientX: touch.clientX,
    clientY: touch.clientY
  });
  signatureCanvas.dispatchEvent(mouseEvent);
}

function clearSignature() {
  if (ctx) {
    ctx.clearRect(0, 0, signatureCanvas.width, signatureCanvas.height);
  }
}

function getSignatureImage() {
  if (signatureCanvas) {
    return signatureCanvas.toDataURL('image/png');
  }
  return null;
}

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