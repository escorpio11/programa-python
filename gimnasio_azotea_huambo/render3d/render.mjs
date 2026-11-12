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
const salida = process.argv[2] || path.join(AQUI, '..', 'salida', 'vistas_3d');
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
  { nombre: '01_aerea_general', cam: [13.6, 12.6, 16.4], obj: [7.2, 0, 3.6], fov: 38, techo: false, entorno: false },
  { nombre: '02_llegada_y_recepcion', cam: [8.3, 1.62, 4.7], obj: [5.5, 1.2, 2.8], fov: 60, techo: true },
  { nombre: '03_peso_libre_y_espejos', cam: [12.25, 1.6, 4.05], obj: [8.9, 1.0, 0.9], fov: 60, techo: true },
  { nombre: '04_sala_hacia_la_calle', cam: [7.0, 1.66, 3.78], obj: [13.6, 1.1, 3.3], fov: 66, techo: true },
  { nombre: '05_tren_inferior_y_crossover', cam: [9.9, 1.65, 2.0], obj: [13.0, 0.8, 5.6], fov: 64, techo: true },
  { nombre: '06_sala_desde_la_calle', cam: [14.35, 1.7, 1.75], obj: [7.5, 0.95, 4.2], fov: 68, techo: true },
  { nombre: '07_lockers_y_servicios', cam: [2.1, 1.62, 5.5], obj: [4.0, 1.15, 2.4], fov: 66, techo: true },
  { nombre: '08_zona_oeste', cam: [7.0, 1.7, 3.6], obj: [1.6, 0.8, 5.4], fov: 68, techo: true },
  { nombre: '09_noche_recepcion', cam: [8.3, 1.62, 4.7], obj: [5.5, 1.2, 2.8], fov: 60, techo: true, noche: true },
  { nombre: '10_noche_sala', cam: [7.0, 1.66, 3.78], obj: [13.6, 1.1, 3.3], fov: 66, techo: true, noche: true },
  { nombre: '11_aerea_desde_la_calle', cam: [23.5, 9.5, -3.2], obj: [7.6, 0.2, 3.5], fov: 34, techo: false, entorno: false },
  { nombre: '12_planta_3d', cam: [7.485, 21.5, 3.33], obj: [7.485, 0, 3.325], fov: 30, techo: false, entorno: false, cenital: true },
  { nombre: '13_exterior_con_techo', cam: [25.0, 7.5, 15.5], obj: [7.5, 0.6, 3.3], fov: 36, techo: true, entorno: true, gente: false },
];
const page = await browser.newPage({ viewport: { width: ancho, height: alto }, deviceScaleFactor: 1 });
const errores = [];
page.on('pageerror', (e) => errores.push(String(e)));
page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') errores.push(m.text()); });
const t0 = Date.now();
await page.goto(`http://localhost:${PUERTO}/web/index.html?w=${ancho}&h=${alto}${process.env.GYM_Q || ''}`, { waitUntil: 'commit' });
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
    g.entorno.visible = v.entorno !== false; g.gente.visible = v.gente !== false;
    A.modo(!!v.noche);
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
