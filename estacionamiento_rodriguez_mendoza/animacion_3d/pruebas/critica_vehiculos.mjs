// Revision independiente de vehiculos.js (puerto 8781).
//   cd animacion_3d && node pruebas/critica_vehiculos.mjs [filtro]
import fs from 'fs';
import path from 'path';
import { servir, abrir } from '../servidor.mjs';

const SALIDA = '/tmp/claude-0/-home-user-programa-python/b5cb2a09-0ee8-5313-ae87-f54f223ebf5f/scratchpad/critica_vehiculos';
const FILTRO = process.argv[2] || '';
const PUERTO = 8781;
fs.mkdirSync(SALIDA, { recursive: true });

// escena: [nombre, opts]; pre: js a evaluar antes de la vista
const VISTAS = [
  { n: 'c01_sedan_peaton_34f', e: ['solo', { tipo: 'sedan', color: '#1b3260', seed: 1 }], pos: [4.6, 1.6, 3.4], obj: [0.3, 0.7, 0], fov: 45 },
  { n: 'c02_suv_rueda_baja', e: ['solo', { tipo: 'suv', color: '#9c1a17', seed: 2 }], pos: [2.6, 0.45, 2.3], obj: [1.4, 0.4, 0.8], fov: 40 },
  { n: 'c03_pickup_trasera_der', e: ['solo', { tipo: 'pickup', color: '#ebebe7', seed: 1 }], pos: [-5.2, 1.7, 3.6], obj: [-1.0, 0.9, 0], fov: 45 },
  { n: 'c04_sedan_bajo_suelo', e: ['solo', { tipo: 'sedan', color: '#c3c6c9', seed: 3 }], pos: [0.2, 0.18, 5.0], obj: [0.2, 0.25, 0], fov: 50 },
  { n: 'c05_van_techo_cerca', e: ['solo', { tipo: 'van', color: '#ebebe7', seed: 2 }], pos: [5.2, 4.2, 2.6], obj: [1.2, 1.6, 0], fov: 45 },
  { n: 'c06_hatch_frontal_bajo', e: ['solo', { tipo: 'hatchback', color: '#9c1a17', seed: 2 }], pos: [4.2, 0.9, -0.6], obj: [0, 0.65, 0], fov: 45 },
  { n: 'c07_moto_izq_frente', e: ['motos', {}], pos: [3.4, 1.4, -4.2], obj: [0, 0.6, -1.0], fov: 42 },
  { n: 'c08_mototaxi_frente_der', e: ['motos', {}], pos: [4.2, 1.5, 6.6], obj: [0, 0.8, 4.0], fov: 42 },
  { n: 'c09_colores_aerea', e: ['colores', {}], pos: [-16, 9, 14], obj: [0, 0.6, 0], fov: 40 },
  { n: 'c10_techo_sombra_doble', e: ['todos', { sombraMain: true }], pre: 'window.APP.techo.visible = true', pos: [9, 2.4, -12.5], obj: [0, 0.6, -3], fov: 45 },
  { n: 'c11_ruedas_giradas', e: ['todos', {}], pre: 'window.APP.techo.visible = false; window.APP.girar(0.9)', pos: [3.0, 1.0, -16], obj: [0.5, 0.5, -6], fov: 40 },
  { n: 'c12_sedan_trasera_baja', e: ['solo', { tipo: 'sedan', color: '#45494e', seed: 4 }], pos: [-4.5, 1.2, -2.6], obj: [-1.2, 0.7, 0], fov: 42 },
  { n: 'c13_suv_lado_der_peaton', e: ['solo', { tipo: 'suv', color: '#cfc5ae', seed: 1 }], pos: [0.6, 1.6, 6.0], obj: [0.0, 0.8, 0], fov: 45 },
  { n: 'c14_pickup_cenital_cerca', e: ['solo', { tipo: 'pickup', color: '#34495b', seed: 3 }], pos: [0.01, 9, 0.0], obj: [0, 0, 0], fov: 40 },
  { n: 'c15_fila_techo_toma4', e: ['fila', { sombraMain: true }], pre: 'window.APP.techo.visible = true; window.APP.techo.position.set(-2.6, 3.4, 0); window.APP.techo.scale.set(1.1, 1, 1)', pos: [6.5, 2.1, -12.5], obj: [-2.5, 1.0, -2.0], fov: 54 },
  { n: 'c16_fila_sol_peaton', e: ['fila', { sombraMain: true }], pre: 'window.APP.techo.visible = false', pos: [3.2, 1.65, 4.0], obj: [-2.2, 0.8, -1.5], fov: 50 },
  { n: 'c17_suv_arco_alambre', e: ['solo', { tipo: 'suv', color: '#ebebe7', seed: 1 }], pre: 'window.APP.alambre(true)', pos: [1.4, 0.9, 3.2], obj: [1.4, 0.75, 0.6], fov: 40 },
  { n: 'c18_suv_arco_blanco', e: ['solo', { tipo: 'suv', color: '#ebebe7', seed: 1 }], pre: 'window.APP.alambre(false)', pos: [1.4, 0.9, 3.2], obj: [1.4, 0.75, 0.6], fov: 40 },
  { n: 'c19_heroes_34', e: ['heroes', {}], pre: 'window.APP.alambre(false); window.APP.techo.visible = false', pos: [9.5, 2.2, -6.5], obj: [0, 0.8, 0], fov: 42 },
  { n: 'c20_sedan_cola_cerca', e: ['solo', { tipo: 'sedan', color: '#ebebe7', seed: 2 }], pre: 'window.APP.alambre(false)', pos: [-3.6, 1.05, 1.9], obj: [-2.1, 0.8, 0.5], fov: 40 },
  { n: 'c21_pickup_blanca_lado_toma2', e: ['heroes', {}], pre: 'window.APP.alambre(false)', pos: [2.0, 3.6, -11.5], obj: [0, 0.8, -3.2], fov: 40 },
  { n: 'c22_pickup_blanca_cerca', e: ['heroes', {}], pre: 'window.APP.alambre(false)', pos: [-1.0, 1.9, -8.6], obj: [0.2, 0.8, -3.2], fov: 44 },
  { n: 'c23_mototaxi_lado_franja', e: ['solo', { tipo: 'mototaxi', color: '#1d4f91', seed: 3 }], pre: 'window.APP.alambre(false)', pos: [-0.6, 1.1, 3.0], obj: [-0.7, 0.75, 0], fov: 40 },
];

const srv = await servir(PUERTO);
const { browser, page, errores } = await abrir({ ancho: 1600, alto: 900, modo: 'still', puerto: PUERTO, pagina: 'pruebas/critica_vehiculos.html' });
let actual = '';
for (const v of VISTAS) {
  if (FILTRO && !v.n.includes(FILTRO)) continue;
  const k = JSON.stringify(v.e);
  if (k !== actual) { await page.evaluate(`window.APP.escena(${JSON.stringify(v.e[0])}, ${JSON.stringify(v.e[1])})`); actual = k; }
  if (v.pre) await page.evaluate(v.pre);
  const t0 = Date.now();
  await page.evaluate(`window.APP.vista(${JSON.stringify(v.pos)}, ${JSON.stringify(v.obj)}, ${v.fov})`);
  await page.screenshot({ path: path.join(SALIDA, `${v.n}.png`) });
  console.log(v.n, Date.now() - t0, 'ms');
}
if (!FILTRO || FILTRO === 'medir') {
  await page.evaluate(`window.APP.escena('todos', {})`);
  for (const r of await page.evaluate('window.APP.medir()')) console.log(JSON.stringify(r));
}
if (errores.length) console.log('ERRORES/AVISOS:\n' + errores.slice(0, 20).join('\n'));
await browser.close();
srv.close();
