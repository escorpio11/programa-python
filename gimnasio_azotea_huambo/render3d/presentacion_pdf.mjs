// Arma la presentación (las mismas diapositivas publicadas) en un PDF 16:9 para compartir.
//   node presentacion_pdf.mjs [salida.pdf]
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const AQUI = path.dirname(fileURLToPath(import.meta.url));
const DECK = path.join(AQUI, '..', 'salida', 'presentacion', 'deck');
const IMG = path.join(AQUI, '..', 'salida', 'presentacion', 'img');
const salida = process.argv[2] || path.join(AQUI, '..', 'salida', 'Presentacion_Azotea_Gym.pdf');
const indice = JSON.parse(fs.readFileSync(path.join(DECK, 'project', 'deck.json'), 'utf8'));
const blobs = JSON.parse(fs.readFileSync(path.join(DECK, 'blobs.json'), 'utf8'));
const b64 = (f) => fs.readFileSync(f).toString('base64');
const fuente = (peso) => `@font-face{font-family:'Oswald';font-weight:${peso};src:url(data:font/woff2;base64,${b64(path.join(AQUI, 'node_modules/@fontsource/oswald/files', `oswald-latin-${peso}-normal.woff2`))}) format('woff2');}`;
let css = fs.readFileSync(path.join(DECK, 'project', 'deck.css'), 'utf8');
let cuerpo = '';
for (const id of indice.order) {
  let h = fs.readFileSync(path.join(DECK, 'project', 'slides', id + '.html'), 'utf8').replace(/<aside>[\s\S]*?<\/aside>/, '');
  h = h.replace(/\/_blob\/([0-9a-f]{32})/g, (_, k) => 'file://' + path.join(IMG, blobs[k]));
  cuerpo += h + '\n';
}
const html = `<!doctype html><html lang="es"><head><meta charset="utf-8"><style>
${fuente(400)}${fuente(600)}
@page{size:1920px 1080px;margin:0} html,body{margin:0;background:#121316}
h1,h2,h3,p{margin:0} h1{font-size:96px} h2{font-size:64px} h3{font-size:44px} p{font-size:32px}
section{width:1920px;height:1080px;box-sizing:border-box;position:relative;overflow:hidden;break-after:page}
section > p, section > h1, section > h2, section > div{position:relative}
.velo,.velo-total{position:absolute !important}
table{border-collapse:collapse;width:100%} th{text-align:left;font-weight:600;border-bottom:3px solid #17181B} td,th{padding:0.42em 0.6em} td{border-bottom:1px solid #C9CBD0}
${css}
*{animation:none !important}
</style></head><body>${cuerpo}</body></html>`;
const tmp = path.join(AQUI, '..', 'salida', 'presentacion', '_presentacion.html');
fs.writeFileSync(tmp, html);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto('file://' + tmp, { waitUntil: 'load' });
await page.evaluate(() => document.fonts.ready);
await page.pdf({ path: salida, width: '1920px', height: '1080px', printBackground: true });
if (process.env.HOJA) {       // hoja de contacto para revisión
  const n = await page.locator('section').count();
  for (let i = 0; i < n; i++) await page.locator('section').nth(i).screenshot({ path: path.join(process.env.HOJA, `p${String(i + 1).padStart(2, '0')}.jpg`), type: 'jpeg', quality: 80 });
}
await browser.close();
fs.rmSync(tmp);
console.log('pdf:', salida, Math.round(fs.statSync(salida).size / 1024), 'KB');
