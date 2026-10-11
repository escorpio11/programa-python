// Render cuadro a cuadro del recorrido y codificación a MP4 (H.264).
//   node render_video.mjs [salida.mp4] [--fps 30] [--w 1920] [--h 1080] [--desde 0] [--hasta <dur>] [--paso 1]
// Reanudable: los cuadros ya generados en cuadros/ no se vuelven a renderizar.
import fs from 'fs';
import path from 'path';
import { execFileSync } from 'child_process';
import { servir, abrir } from './servidor.mjs';

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };
const salida = args[0] && !args[0].startsWith('--') ? args[0] : 'recorrido_estacionamiento.mp4';
const FPS = +opt('fps', 30), W = +opt('w', 1920), H = +opt('h', 1080);
const DIR = opt('cuadros', 'cuadros');
const PUERTO = +(process.env.PUERTO || 8790);
fs.mkdirSync(DIR, { recursive: true });

const srv = await servir(PUERTO);
const { browser, page, errores } = await abrir({ ancho: W, alto: H, modo: 'video', puerto: PUERTO });
const dur = await page.evaluate('window.APP.duracion');
const desde = +opt('desde', 0), hasta = +opt('hasta', dur), paso = +opt('paso', 1);
const n0 = Math.round(desde * FPS), n1 = Math.round(hasta * FPS);
console.log(`Duración ${dur} s, cuadros ${n0}..${n1} a ${FPS} fps, ${W}x${H}`);
const t0 = Date.now();
let hechos = 0;
for (let i = n0; i < n1; i += paso) {
  const f = path.join(DIR, `c${String(i).padStart(5, '0')}.jpg`);
  if (fs.existsSync(f)) continue;
  await page.evaluate(`window.APP.renderEn(${(i / FPS).toFixed(5)})`);
  await page.screenshot({ path: f, type: 'jpeg', quality: 93 });
  hechos++;
  if (hechos % 30 === 0) {
    const s = (Date.now() - t0) / 1000;
    const resta = (n1 - i) / paso * s / hechos;
    console.log(`cuadro ${i}/${n1}  ${(s / hechos).toFixed(2)} s/cuadro  ~${(resta / 60).toFixed(1)} min restantes`);
  }
}
if (errores.length) console.log('Avisos del navegador:\n' + [...new Set(errores)].slice(0, 10).join('\n'));
await browser.close();
srv.close();

if (paso === 1 && desde === 0 && Math.abs(hasta - dur) < 1e-6) {
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(DIR, 'c%05d.jpg'),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
    '-vf', 'format=yuv420p', salida], { stdio: 'inherit' });
  console.log('Video:', salida, (fs.statSync(salida).size / 1e6).toFixed(1), 'MB');
}
