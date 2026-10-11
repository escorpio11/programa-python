// QA de vehiculos.js: renderiza vistas de control a 1600x900.
//   cd animacion_3d && node pruebas/qa_vehiculos.mjs [salida] [filtro]
import fs from 'fs';
import path from 'path';
import { servir, abrir } from '../servidor.mjs';

const SALIDA = process.argv[2] || '/tmp/claude-0/-home-user-programa-python/b5cb2a09-0ee8-5313-ae87-f54f223ebf5f/scratchpad/qa_vehiculos';
const FILTRO = process.argv[3] || '';
const PUERTO = 8771;
fs.mkdirSync(SALIDA, { recursive: true });

// Vehículos en z = (i-3)*3 : sedan -9, hatch -6, suv -3, pickup 0, van 3, moto 6, mototaxi 9
const VISTAS = [
  { nombre: '01_tres_cuartos_frontal', escena: 'todos', pos: [14, 5.5, -16], obj: [0, 0.8, -1.0], fov: 42 },
  { nombre: '02_lateral', escena: 'perfil', pos: [3.0, 1.3, -24], obj: [3.0, 1.0, 0], fov: 46 },
  { nombre: '02b_lateral_autos', escena: 'perfil', pos: [-5.5, 1.1, -11], obj: [-5.5, 0.9, 0], fov: 50 },
  { nombre: '02c_lateral_grandes', escena: 'perfil', pos: [5.0, 1.2, -11], obj: [5.0, 1.0, 0], fov: 50 },
  { nombre: '03_tres_cuartos_trasera', escena: 'todos', pos: [-14, 4.5, 15], obj: [0, 0.8, 1.0], fov: 42 },
  { nombre: '04_cenital', escena: 'todos', pos: [0.01, 34, 0.0], obj: [0, 0, 0], fov: 40 },
  { nombre: '05_frontal', escena: 'todos', pos: [24, 1.4, 0], obj: [0, 1.0, 0], fov: 44 },
  { nombre: '06_detalle_sedan_suv', escena: 'todos', pos: [6.5, 2.2, -11.5], obj: [0, 0.8, -6], fov: 40 },
  { nombre: '07_detalle_pickup_van', escena: 'todos', pos: [-6.5, 2.6, 6.5], obj: [0, 1.0, 1.5], fov: 42 },
  { nombre: '08_detalle_motos', escena: 'todos', pos: [4.6, 2.0, 4.6], obj: [0, 0.7, 7.8], fov: 40 },
  { nombre: '12_sedan_trasera', escena: 'todos', pos: [-6.2, 2.3, -12.6], obj: [-1.2, 0.8, -8.6], fov: 38 },
  { nombre: '13_pickup_frontal', escena: 'todos', pos: [6.8, 1.9, 3.4], obj: [0.6, 0.9, -0.3], fov: 40 },
  { nombre: '14_mototaxi_trasera', escena: 'todos', pos: [-4.8, 1.9, 11.8], obj: [0, 0.8, 8.6], fov: 40 },
  { nombre: '15_variantes', escena: 'variantes', pos: [16, 11, -16], obj: [0, 0.5, 0], fov: 42 },
  { nombre: '09_fila_aerea', escena: 'fila', pos: [12, 9, -10], obj: [0.5, 0.5, 0], fov: 40 },
  { nombre: '10_fila_cenital', escena: 'fila', pos: [0.6, 22, 0.01], obj: [0.6, 0, 0], fov: 42 },
  { nombre: '11_fila_frente', escena: 'fila', pos: [11, 1.6, 2.0], obj: [0, 0.9, 0], fov: 50 },
];

const srv = await servir(PUERTO);
const { browser, page, errores } = await abrir({ ancho: 1600, alto: 900, modo: 'still', puerto: PUERTO, pagina: 'pruebas/vehiculos.html' });
let actual = 'todos';
for (const r of await page.evaluate('window.APP.info()')) console.log(JSON.stringify(r));
for (const v of VISTAS) {
  if (FILTRO && !v.nombre.includes(FILTRO)) continue;
  if (v.escena !== actual) {
    await page.evaluate(`window.APP.escena('${v.escena}')`);
    actual = v.escena;
    if (v.escena === 'fila') console.log('fila', JSON.stringify((await page.evaluate('window.APP.info()')).map((r) => [r.tipo, r.ancho, r.minY])));
  }
  const t0 = Date.now();
  await page.evaluate(`window.APP.vista(${JSON.stringify(v.pos)}, ${JSON.stringify(v.obj)}, ${v.fov})`);
  await page.screenshot({ path: path.join(SALIDA, `${v.nombre}.png`) });
  console.log(v.nombre, Date.now() - t0, 'ms');
}
if (errores.length) console.log('ERRORES/AVISOS:\n' + errores.slice(0, 20).join('\n'));
await browser.close();
srv.close();
