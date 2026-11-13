// Video de recorrido interior (cuadros con Chromium headless + ffmpeg).
//   node render_video.mjs [salida.mp4] [ancho] [alto] [fps] [cuadros_por_tramo]
import http from 'http';
import fs from 'fs';
import path from 'path';
import { execFileSync } from 'child_process';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const AQUI = path.dirname(fileURLToPath(import.meta.url));
const TIPOS = { '.js': 'text/javascript', '.json': 'application/json', '.html': 'text/html' };
const VER = (process.env.GYM_VERSION || 'A').toUpperCase();
const SAL = VER === 'A' ? 'salida' : 'salida_' + VER;
const salida = process.argv[2] || path.join(AQUI, '..', SAL, `Recorrido_Azotea_Gym${VER === 'A' ? '' : '_' + VER}.mp4`);
const ancho = +(process.argv[3] || 1280), alto = +(process.argv[4] || 720), fps = +(process.argv[5] || 20), porTramo = +(process.argv[6] || 40);
const tmp = path.join(AQUI, '..', 'salida', '_tmp', 'cuadros' + VER);
fs.rmSync(tmp, { recursive: true, force: true }); fs.mkdirSync(tmp, { recursive: true });

// Recorrido: [cámara x, altura, y] -> [mira x, altura, y]
const CLAVES_B = [
  [[7.02, 1.60, 2.50], [5.7, 1.25, 3.3]],     // sale de la escalera
  [[7.3, 1.62, 3.9], [5.4, 1.2, 2.9]],        // recepción
  [[5.3, 1.62, 3.95], [3.4, 1.1, 2.6]],       // lockers y baños
  [[3.6, 1.65, 3.5], [1.9, 0.9, 5.6]],        // zona de cardio
  [[5.0, 1.65, 3.97], [8.3, 0.9, 5.4]],       // hip thrust y prensa
  [[7.6, 1.68, 3.6], [12.5, 1.0, 3.3]],       // sala hacia la calle
  [[9.95, 1.65, 3.5], [9.0, 0.9, 0.5]],       // peso libre y espejos
  [[10.2, 1.65, 4.95], [13.4, 0.9, 5.3]],     // crossover y tren inferior
  [[12.58, 1.75, 3.9], [8.0, 0.9, 3.0]],      // vista final hacia la recepción
];
const CLAVES_A = [
  [[7.02, 1.60, 2.50], [5.7, 1.25, 3.3]],     // sale de la escalera
  [[7.3, 1.62, 3.95], [5.4, 1.2, 2.9]],       // recepción
  [[5.6, 1.62, 4.5], [3.5, 1.1, 2.6]],        // lockers y baños
  [[3.7, 1.62, 4.05], [1.4, 0.8, 5.2]],       // press plano y celosía
  [[5.2, 1.65, 4.3], [8.5, 0.9, 5.4]],        // dominadas y prensa
  [[7.6, 1.68, 3.6], [12.5, 1.0, 3.2]],       // sala hacia la calle
  [[10.2, 1.65, 3.4], [9.0, 0.9, 0.5]],       // peso libre y espejos
  [[11.6, 1.65, 3.2], [13.6, 0.9, 5.6]],      // tren inferior
  [[12.9, 1.75, 1.95], [7.5, 0.9, 4.5]],      // vista final hacia la recepción
];
const CLAVES = VER === 'B' ? CLAVES_B : CLAVES_A;
const cr = (p0, p1, p2, p3, t) => p1.map((_, i) => 0.5 * ((2 * p1[i]) + (-p0[i] + p2[i]) * t + (2 * p0[i] - 5 * p1[i] + 4 * p2[i] - p3[i]) * t * t + (-p0[i] + 3 * p1[i] - 3 * p2[i] + p3[i]) * t * t * t));
const suave = (t) => t;          // velocidad constante entre claves
const cuadros = [];
for (let s = 0; s < CLAVES.length - 1; s++) {
  const K = (i) => CLAVES[Math.max(0, Math.min(CLAVES.length - 1, i))];
  for (let f = 0; f < porTramo; f++) {
    const t = suave(f / porTramo);
    cuadros.push([cr(K(s - 1)[0], K(s)[0], K(s + 1)[0], K(s + 2)[0], t), cr(K(s - 1)[1], K(s)[1], K(s + 1)[1], K(s + 2)[1], t)]);
  }
}
for (let i = 0; i < fps; i++) cuadros.push(CLAVES.at(-1));      // 1 s quieto al final

const srv = http.createServer((req, res) => {
  const f = path.join(AQUI, decodeURIComponent(req.url.split('?')[0]));
  if (!f.startsWith(AQUI) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TIPOS[path.extname(f)] || 'application/octet-stream' });
  fs.createReadStream(f).pipe(res);
});
const PUERTO = 8794;
await new Promise((ok) => srv.listen(PUERTO, ok));
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl', '--disable-gpu-sandbox'] });
const page = await browser.newPage({ viewport: { width: ancho, height: alto }, deviceScaleFactor: 1 });
await page.goto(`http://localhost:${PUERTO}/web/index.html?w=${ancho}&h=${alto}&ao=0&ver=${VER}`, { waitUntil: 'commit' });
await page.waitForFunction('window.APP && window.APP.listo === true', null, { timeout: 300000, polling: 500 });
await page.evaluate(() => { const g = window.APP.grupos; g.techo.visible = true; g.techoBano.visible = true; g.gente.visible = false; window.APP.modo(false); });
const t0 = Date.now();
for (let i = 0; i < cuadros.length; i++) {
  await page.evaluate(([c, o]) => window.APP.vista(c, o, 66), cuadros[i]);
  await page.screenshot({ path: path.join(tmp, `c${String(i).padStart(4, '0')}.jpg`), type: 'jpeg', quality: 92 });
  if (i % 20 === 0) console.log('cuadro', i, '/', cuadros.length, Math.round((Date.now() - t0) / 1000), 's');
}
await browser.close(); srv.close();
execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(fps), '-i', path.join(tmp, 'c%04d.jpg'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '21', '-movflags', '+faststart', salida]);
fs.rmSync(tmp, { recursive: true, force: true });
console.log('video:', salida, fs.statSync(salida).size, 'bytes');
