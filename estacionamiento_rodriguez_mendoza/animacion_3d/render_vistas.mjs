// Renderiza vistas de control (PNG) para revisar la escena.
//   node render_vistas.mjs <salida_dir> [ancho] [alto] [vistas.json]
// Sin vistas.json usa un set predefinido de cámaras. Con "t:<seg>" usa el guion del video.
import fs from 'fs';
import path from 'path';
import { servir, abrir } from './servidor.mjs';

const salida = process.argv[2] || 'vistas';
const ancho = +(process.argv[3] || 1600), alto = +(process.argv[4] || 900);
fs.mkdirSync(salida, { recursive: true });

const PUERTO = +(process.env.PUERTO || 8765);
const srv = await servir(PUERTO);
const { browser, page, errores } = await abrir({ ancho, alto, modo: process.env.MODO || 'still', puerto: PUERTO, pagina: process.env.PAGINA || 'index.html' });
const c = await page.evaluate('window.APP.centroLote');
const [cx, , cz] = c;
let vistas = [
  { nombre: '01_aerea', pos: [cx - 48, 42, cz + 46], obj: [cx, 0, cz], fov: 38 },
  { nombre: '02_cenital', pos: [cx + 0.01, 95, cz + 0.01], obj: [cx, 0, cz], fov: 32 },
  { nombre: '03_esquina_calle', pos: [cx - 30, 6, cz - 30], obj: [cx, 2, cz], fov: 45 },
  { nombre: '04_pasillo', pos: [cx + 10, 1.7, cz - 18], obj: [cx + 12, 1.6, cz + 8], fov: 55 },
  { nombre: '05_bajo_techo', pos: [cx + 14, 1.6, cz - 14], obj: [cx + 17, 2.6, cz + 2], fov: 60 },
  { nombre: '06_frente_salida', pos: [cx - 26, 2.0, cz + 10], obj: [cx, 1.5, cz], fov: 50 },
];
if (process.argv[5]) vistas = JSON.parse(fs.readFileSync(process.argv[5], 'utf8'));
for (const v of vistas) {
  const t0 = Date.now();
  if (v.t !== undefined) await page.evaluate(`window.APP.renderEn(${v.t})`);
  else await page.evaluate(`window.APP.vista(${JSON.stringify(v.pos)}, ${JSON.stringify(v.obj)}, ${v.fov || 40}, ${v.tt || 20})`);
  await page.screenshot({ path: path.join(salida, `${v.nombre}.png`) });
  console.log(v.nombre, Date.now() - t0, 'ms');
}
console.log('info', JSON.stringify(await page.evaluate('window.APP.info()')));
if (errores.length) console.log('ERRORES/AVISOS:\n' + errores.slice(0, 20).join('\n'));
await browser.close();
srv.close();
