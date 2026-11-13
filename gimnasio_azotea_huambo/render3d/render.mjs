// Vistas 3D del gimnasio con Chromium headless (WebGL por software).
//   node render.mjs [carpeta_salida] [ancho] [alto] [solo=nombre1,nombre2]
import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const AQUI = path.dirname(fileURLToPath(import.meta.url));
const TIPOS = { '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.html': 'text/html', '.css': 'text/css', '.png': 'image/png' };
const VER = (process.env.GYM_VERSION || 'A').toUpperCase();
const salida = process.argv[2] || path.join(AQUI, '..', VER === 'A' ? 'salida' : 'salida_' + VER, 'vistas_3d');
const ancho = +(process.argv[3] || 1920), alto = +(process.argv[4] || 1080);
const solo = (process.argv[5] || '').split(',').filter(Boolean);
fs.mkdirSync(salida, { recursive: true });

const srv = http.createServer((req, res) => {
  const f = path.join(AQUI, decodeURIComponent(req.url.split('?')[0]));
  if (!f.startsWith(AQUI) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TIPOS[path.extname(f)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
  fs.createReadStream(f).pipe(res);
});
const PUERTO = +(process.env.PUERTO || 8793);
await new Promise((ok) => srv.listen(PUERTO, ok));
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl', '--disable-gpu-sandbox'] });

// cam / obj en metros del modelo: [x, altura, y].  techo: se muestra la cubierta.  alto: cerramiento sobre parapeto.
export const VISTAS = [
  { nombre: '01_aerea_general', cam: [13.1, 11.6, 15.4], obj: [7.45, 0, 3.4], fov: 36, techo: false, entorno: false, ocultar: ['B', 'calle'], gente: true },
  { nombre: '02_llegada_y_recepcion', cam: [8.35, 1.62, 4.75], obj: [5.5, 1.2, 2.8], fov: 60, techo: true },
  { nombre: '03_peso_libre_y_espejos', cam: [11.9, 1.62, 3.55], obj: [8.6, 0.95, 0.4], fov: 62, techo: true },
  { nombre: '04_sala_hacia_la_calle', cam: [7.15, 1.7, 3.62], obj: [13.8, 1.0, 3.25], fov: 70, techo: true },
  { nombre: '05_tren_inferior_y_crossover', cam: [9.9, 1.65, 2.0], obj: [13.0, 0.8, 5.6], fov: 64, techo: true },
  { nombre: '06_sala_desde_la_calle', cam: [14.35, 1.7, 1.75], obj: [7.5, 0.95, 4.2], fov: 68, techo: true },
  { nombre: '07_lockers_y_servicios', cam: [3.05, 1.62, 4.4], obj: [4.3, 1.15, 2.2], fov: 72, techo: true },
  { nombre: '08_zona_oeste', cam: [6.85, 1.72, 4.62], obj: [1.5, 0.75, 5.1], fov: 68, techo: true },
  { nombre: '09_noche_recepcion', cam: [8.35, 1.62, 4.75], obj: [5.5, 1.2, 2.8], fov: 60, techo: true, noche: true },
  { nombre: '10_noche_sala', cam: [7.15, 1.7, 3.62], obj: [13.8, 1.0, 3.25], fov: 70, techo: true, noche: true },
  { nombre: '11_aerea_desde_la_calle', cam: [21.2, 8.6, 11.6], obj: [7.9, 0.2, 3.2], fov: 34, techo: false, entorno: false, ocultar: ['B', 'calle'], gente: true },
  { nombre: '12_planta_3d', cam: [7.485, 21.5, 3.33], obj: [7.485, 0, 3.325], fov: 30, techo: false, entorno: false, cenital: true },
  { nombre: '13_vista_general_alta', cam: [14.55, 2.18, 4.08], obj: [5.5, 0.35, 3.1], fov: 76, techo: true },
  { nombre: '14_noche_desde_la_calle', cam: [14.35, 1.7, 1.75], obj: [7.5, 0.95, 4.2], fov: 68, techo: true, noche: true },
];
if (VER === 'B') {            // cámaras propias de la versión B (cardio en la esquina del lado mercado)
  const cambia = {
    '03_peso_libre_y_espejos': { cam: [12.55, 1.65, 4.85], obj: [9.3, 0.85, 0.9], fov: 64 },
    '08_zona_oeste': { nombre: '08_zona_cardio', cam: [5.75, 1.7, 4.15], obj: [1.5, 0.85, 5.35], fov: 68 },
  };
  for (const v of VISTAS) Object.assign(v, cambia[v.nombre] || {});
  VISTAS.push({ nombre: '15_cardio_y_ventanal', cam: [3.0, 1.68, 3.2], obj: [2.75, 0.95, 6.2], fov: 70, techo: true },
    { nombre: '16_noche_cardio', cam: [5.75, 1.7, 4.15], obj: [1.5, 0.85, 5.35], fov: 68, techo: true, noche: true });
}
const page = await browser.newPage({ viewport: { width: ancho, height: alto }, deviceScaleFactor: 1 });
const errores = [];
page.on('pageerror', (e) => errores.push(String(e)));
page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') errores.push(m.text()); });
const t0 = Date.now();
await page.goto(`http://localhost:${PUERTO}/web/index.html?w=${ancho}&h=${alto}&ver=${VER}${process.env.GYM_Q || ''}`, { waitUntil: 'commit' });
try {
  await page.waitForFunction('window.APP && window.APP.listo === true', null, { timeout: 300000, polling: 500 });
} catch (e) { console.error('no cargó:\n' + errores.join('\n')); await browser.close(); srv.close(); process.exit(1); }
console.log('escena lista', Date.now() - t0, 'ms');
for (const v of VISTAS) {
  if (solo.length && !solo.some((s) => v.nombre.includes(s))) continue;
  const t1 = Date.now();
  await page.evaluate((v) => {
    const A = window.APP, g = A.grupos;
    g.techo.visible = v.techo; g.techoBano.visible = v.techo; g.cerramientoAlto.visible = true;
    g.entorno.visible = v.entorno !== false; g.gente.visible = v.gente === true;
    A.modo(!!v.noche);
    A.lados({ A: true, B: true, calle: true, mercado: true });
    if (v.ocultar) A.lados(Object.fromEntries(v.ocultar.map((l) => [l, false])));
    if (v.entorno === false) A.estudio(true);
    if (v.cenital) { A.camera.up.set(0, 0, -1); } else { A.camera.up.set(0, 1, 0); }
    A.vista(v.cam, v.obj, v.fov);
    A.pintar();
  }, v);
  await page.screenshot({ path: path.join(salida, `${v.nombre}.png`) });
  console.log(v.nombre, Date.now() - t1, 'ms');
}
if (errores.length) console.log('AVISOS:\n' + [...new Set(errores)].slice(0, 12).join('\n'));
await browser.close();
srv.close();
