// Servidor estático mínimo + navegador headless (Chromium con WebGL por software).
import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { chromium } from 'playwright-core';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const RAIZ = path.join(AQUI, 'web');
const TIPOS = { '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.html': 'text/html',
  '.css': 'text/css', '.png': 'image/png', '.jpg': 'image/jpeg' };

export function servir(puerto = 8765) {
  const srv = http.createServer((req, res) => {
    const f = path.join(RAIZ, decodeURIComponent(req.url.split('?')[0]));
    if (!f.startsWith(RAIZ) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': TIPOS[path.extname(f)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    fs.createReadStream(f).pipe(res);
  });
  return new Promise((ok) => srv.listen(puerto, () => ok(srv)));
}

export async function abrir({ ancho = 1920, alto = 1080, modo = 'video', puerto = 8765, extra = '', pagina = 'index.html' } = {}) {
  const chrome = process.env.CHROME || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
  const browser = await chromium.launch({ executablePath: chrome,
    args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl',
      '--disable-gpu-sandbox'] });
  const page = await browser.newPage({ viewport: { width: ancho, height: alto }, deviceScaleFactor: 1 });
  const errores = [];
  page.on('pageerror', (e) => errores.push(String(e)));
  page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') errores.push(m.text()); });
  await page.goto(`http://localhost:${puerto}/${pagina}?modo=${modo}&w=${ancho}&h=${alto}${extra}`);
  try {
    await page.waitForFunction('window.APP && window.APP.listo === true', null, { timeout: 180000 });
  } catch (e) {
    console.error('La escena no cargó:', errores.join('\n'));
    throw e;
  }
  return { browser, page, errores };
}
