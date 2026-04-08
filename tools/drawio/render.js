#!/usr/bin/env node
/**
 * render.js — 将 .drawio XML 文件渲染为 PNG。
 *
 * 用法:
 *   node render.js <input.drawio> <output.png> [scale]
 *   node render.js <input.drawio> <output.svg>
 *
 * 依赖: puppeteer-core（已安装于项目 node_modules）
 */

const puppeteer = require('./node_modules/puppeteer-core');
const fs        = require('fs');
const path      = require('path');

const CHROMIUM  = '/usr/bin/chromium-browser';
const MXCLIENT  = path.join(__dirname, 'mxClient.min.js');

async function render(inputFile, outputFile, scale = 1.5) {
  const xmlContent = fs.readFileSync(inputFile, 'utf8');
  const mxClientJs = fs.readFileSync(MXCLIENT, 'utf8');
  const isSVG = outputFile.toLowerCase().endsWith('.svg');

  // Minimal HTML page that uses mxGraph to render the diagram
  const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background: white; }
  #container { display: inline-block; }
</style>
<script>
// mxGraph configuration — must be set BEFORE loading mxClient
window.mxImageBasePath = '';
window.mxBasePath      = '';
window.mxLoadStylesheets = false;
window.mxLoadResources   = false;
</script>
<script>${mxClientJs}</script>
</head>
<body>
<div id="container"></div>
<script>
(function() {
  var xmlStr = ${JSON.stringify(xmlContent)};
  var container = document.getElementById('container');

  // Parse the XML
  var xmlDoc = mxUtils.parseXml(xmlStr);
  var node   = xmlDoc.documentElement;

  // Unwrap <mxfile> → <diagram> → <mxGraphModel> if needed
  if (node.nodeName === 'mxfile') {
    var diagNodes = node.getElementsByTagName('diagram');
    if (diagNodes.length > 0) {
      node = diagNodes[0];
    }
  }
  // If content is text (compressed), try to decompress; if it's a child element, use that
  if (node.nodeName === 'diagram') {
    var children = node.childNodes;
    var modelNode = null;
    for (var i = 0; i < children.length; i++) {
      if (children[i].nodeName === 'mxGraphModel') {
        modelNode = children[i];
        break;
      }
    }
    if (modelNode) {
      node = modelNode;
    } else {
      // Try text content (may be base64+deflate compressed)
      var textContent = node.textContent.trim();
      if (textContent) {
        try {
          var decoded = atob(textContent);
          var bytes   = new Uint8Array(decoded.length);
          for (var j = 0; j < decoded.length; j++) bytes[j] = decoded.charCodeAt(j);
          var decompressed = pako ? pako.inflateRaw(bytes, {to:'string'}) : decoded;
          var inner = mxUtils.parseXml(decodeURIComponent(decompressed));
          node = inner.documentElement;
        } catch(e) { /* ignore, try as-is */ }
      }
    }
  }

  // Create graph in container (hidden sizing div)
  var graph = new mxGraph(container);
  graph.setEnabled(false);
  graph.setHtmlLabels(true);
  graph.setTooltips(false);

  // Decode XML into graph model
  var model   = graph.getModel();
  var codec   = new mxCodec(xmlDoc);
  model.beginUpdate();
  try {
    codec.decode(node, model);
  } finally {
    model.endUpdate();
  }

  // Fit container to content
  graph.fit(10);   // 10px border
  var bounds = graph.getGraphBounds();
  var margin = 20;
  var w = Math.ceil(bounds.x + bounds.width  + margin * 2);
  var h = Math.ceil(bounds.y + bounds.height + margin * 2);
  container.style.width  = w + 'px';
  container.style.height = h + 'px';

  // Signal ready
  window.__renderDone   = true;
  window.__renderWidth  = w;
  window.__renderHeight = h;
})();
</script>
</body>
</html>`;

  const browser = await puppeteer.launch({
    executablePath: CHROMIUM,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--headless=new',
      '--disable-gpu',
    ],
    headless: true,
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 2400, height: 1800, deviceScaleFactor: scale });
    await page.setContent(html, { waitUntil: 'domcontentloaded' });

    // Wait for render to complete
    await page.waitForFunction('window.__renderDone === true', { timeout: 10000 });

    const { w, h } = await page.evaluate(() => ({
      w: window.__renderWidth  || 800,
      h: window.__renderHeight || 600,
    }));

    if (isSVG) {
      // Export as SVG string via mxSvgCanvas2D
      const svg = await page.evaluate(() => {
        var container = document.getElementById('container');
        var svgEl = container.querySelector('svg');
        return svgEl ? svgEl.outerHTML : null;
      });
      if (svg) {
        fs.writeFileSync(outputFile, svg, 'utf8');
        console.log('SVG saved:', outputFile);
      } else {
        throw new Error('No SVG element found in rendered page');
      }
    } else {
      // Screenshot PNG
      const clip = {
        x: 0, y: 0,
        width:  Math.max(w * scale, 100),
        height: Math.max(h * scale, 100),
      };
      await page.screenshot({
        path: outputFile,
        type: 'png',
        clip: { x: 0, y: 0, width: Math.ceil(w * scale + 40), height: Math.ceil(h * scale + 40) },
        omitBackground: false,
      });
      console.log('PNG saved:', outputFile, `(${Math.ceil(w*scale)}x${Math.ceil(h*scale)})`);
    }
  } finally {
    await browser.close();
  }
}

// ── CLI entry point ──────────────────────────────────────────────────────────
const [,, inputFile, outputFile, scaleArg] = process.argv;
if (!inputFile || !outputFile) {
  console.error('Usage: node render.js <input.drawio> <output.png> [scale=1.5]');
  process.exit(1);
}
const scale = parseFloat(scaleArg || '1.5');
render(path.resolve(inputFile), path.resolve(outputFile), scale)
  .catch(err => { console.error('Error:', err.message); process.exit(1); });
