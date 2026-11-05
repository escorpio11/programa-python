// Renderiza vistas fijas del modelo 3D de la pollería (Chromium headless con WebGL por software).
//   node render.mjs [salida_dir] [ancho] [alto] [solo=nombre1,nombre2]
import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require('playwright')); } catch (e) {
  ({ chromium } = require('../../estacionamiento_rodriguez_mendoza/animacion_3d/node_modules/playwright-core'));
}
const AQUI = path.dirname(fileURLToPath(import.meta.url));
const RAIZ = path.resolve(AQUI, '..', '..');          // raíz del repositorio
const TIPOS = { '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.html': 'text/html',
  '.css': 'text/css', '.png': 'image/png' };
const salida = process.argv[2] || path.join(AQUI, '..', 'salida', 'vistas_3d');
const ancho = +(process.argv[3] || 1600), alto = +(process.argv[4] || 900);
const solo = (process.argv[5] || '').split(',').filter(Boolean);
fs.mkdirSync(salida, { recursive: true });

const srv = http.createServer((req, res) => {
  const f = path.join(RAIZ, decodeURIComponent(req.url.split('?')[0]));
  if (!f.startsWith(RAIZ) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TIPOS[path.extname(f)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
  fs.createReadStream(f).pipe(res);
});
const PUERTO = +(process.env.PUERTO || 8791);
await new Promise((ok) => srv.listen(PUERTO, ok));
const browser = await chromium.launch({ executablePath: process.env.CHROME || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl', '--disable-gpu-sandbox'] });

// Cámaras: posiciones en el marco del edificio (s, d) o del lote (u, v) -> se convierten en la página.
const VISTAS = [
  { nombre: '01_aerea_esquina', q: '', cam: 'C(-1.5, 31, -52)', obj: 'C(22.0, 0, -14.5)', fov: 38 },
  { nombre: '02_ingreso_desde_el_jiron', q: '', cam: 'UV(8.6, 30.2, 1.65)', obj: 'SDp(7.0, 20.5, 2.6)', fov: 50 },
  { nombre: '03_jardin_lateral', q: '', cam: 'SDp(17.6, 33.9, 1.75)', obj: 'SDp(10.5, 21.5, 3.4)', fov: 56 },
  { nombre: '04_terraza_y_escenario', q: '', cam: 'SDp(7.2, 19.2, 5.5)', obj: 'SDp(16.6, 21.5, 4.6)', fov: 62 },
  { nombre: '05_porche_y_sombrillas', q: '', cam: 'UV(8.6, 6.3, 1.65)', obj: 'SDp(12.5, 24.0, 2.6)', fov: 58 },
  { nombre: '06_aerea_modo_evento', q: '&modo=evento', cam: 'C(-1.5, 31, -52)', obj: 'C(22.0, 0, -14.5)', fov: 38 },
  { nombre: '07_aerea_etapa2_piscina', q: '&etapa=2', cam: 'C(20, 44, 22)', obj: 'C(18.0, 0, -6.5)', fov: 42 },
  { nombre: '08_calzada_y_servicio', q: '', cam: 'SDp(-2.5, 8.2, 1.7)', obj: 'SDp(16.0, 10.0, 2.5)', fov: 55 },
];
const grupos = new Map();
for (const v of VISTAS) {
  if (solo.length && !solo.includes(v.nombre)) continue;
  if (!grupos.has(v.q)) grupos.set(v.q, []);
  grupos.get(v.q).push(v);
}
for (const [q, vistas] of grupos) {
  const page = await browser.newPage({ viewport: { width: ancho, height: alto }, deviceScaleFactor: 1 });
  const errores = [];
  page.on('pageerror', (e) => errores.push(String(e)));
  page.on('console', (m) => { if (m.type() === 'error') errores.push(m.text()); });
  const t0 = Date.now();
  await page.goto(`http://localhost:${PUERTO}/polleria_campestre_mendoza/render3d/web/index.html?w=${ancho}&h=${alto}${q}`,
    { waitUntil: 'commit' });
  try {
    await page.waitForFunction('window.APP && window.APP.listo === true', null, { timeout: 300000, polling: 1000 });
  } catch (e) {
    console.error('no cargó', q, errores.join('\n'));
    throw e;
  }
  console.log('escena', q || '(base)', Date.now() - t0, 'ms');
  for (const v of vistas) {
    const t1 = Date.now();
    await page.evaluate(`(() => {
      const A = window.APP;
      const C = (x, y, z) => [x, y, z];
      const UV = (u, v, y) => { const p = A.punto([u, v]); return [p[0], y, p[1]]; };
      const SDp = (s, d, y) => { const p = A.SD(s, d); return [p[0], y, p[1]]; };
      A.vista(${v.cam}, ${v.obj}, ${v.fov});
    })()`);
    await page.screenshot({ path: path.join(salida, `${v.nombre}.png`) });
    console.log(v.nombre, Date.now() - t1, 'ms');
  }
  if (errores.length) console.log('AVISOS:\n' + errores.slice(0, 10).join('\n'));
  await page.close();
}
await browser.close();
srv.close();
