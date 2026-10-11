// QA del módulo web/entorno.js: renderiza vistas de control con la página web/pruebas/entorno.html.
//   node pruebas/qa_entorno.mjs [filtro] [ancho] [alto]
// Guarda PNG en $SALIDA (por defecto el scratchpad qa_entorno/).
import fs from 'fs';
import path from 'path';
import { servir, abrir } from '../servidor.mjs';

const SALIDA = process.env.SALIDA ||
  '/tmp/claude-0/-home-user-programa-python/b5cb2a09-0ee8-5313-ae87-f54f223ebf5f/scratchpad/qa_entorno';
const filtro = process.argv[2] && process.argv[2] !== 'todo' ? new RegExp(process.argv[2]) : null;
const ancho = +(process.argv[3] || 1600), alto = +(process.argv[4] || 900);
const PUERTO = 8772;
fs.mkdirSync(SALIDA, { recursive: true });

const srv = await servir(PUERTO);
const extra = process.env.SIN_PROYECTO ? '&proyecto=0' : '';
const { browser, page, errores } = await abrir({ ancho, alto, modo: 'still', puerto: PUERTO, pagina: 'pruebas/entorno.html', extra });
const d = await page.evaluate('({c: window.APP.centroLote, v: window.APP.datos.vertices})');
const [cx, , cz] = d.c;
const A = d.v.A, B = d.v.B, C = d.v.C, D = d.v.D;
// marco de calles: tAB (A->B), nAB (hacia la calle, fuera del lote); tAD (A->D), nDA
const nrm = (x, z) => { const l = Math.hypot(x, z); return [x / l, z / l]; };
const tAB = nrm(B[0] - A[0], B[1] - A[1]);
const tAD = nrm(D[0] - A[0], D[1] - A[1]);
const fueraAB = [-0.8669, -0.4984], fueraDA = [-0.1755, -0.9845];
const P = (base, a, sa, b, sb, y) => [base[0] + a[0] * sa + b[0] * sb, y, base[1] + a[1] * sa + b[1] * sb];

const vistas = [
  { nombre: '01_aerea_34', pos: [cx - 48, 42, cz + 46], obj: [cx, 0, cz], fov: 38 },
  { nombre: '02_aerea_alta_norte', pos: [cx + 75, 70, cz - 85], obj: [cx, 0, cz], fov: 40 },
  { nombre: '03_esquina_A_peaton', pos: P(A, fueraAB, 9.0, tAD, -2.5, 1.65), obj: [cx, 2.0, cz], fov: 55 },
  { nombre: '04_esquina_A_mira_calle', pos: P(A, fueraAB, 0.6, tAD, -0.6, 1.65), obj: P(A, tAD, 40, fueraDA, 5, 2.5), fov: 55 },
  { nombre: '05_jiron_largo', pos: P(B, tAB, 38, fueraAB, 3.0, 2.2), obj: P(A, tAB, -20, fueraAB, 4.5, 2.0), fov: 50 },
  { nombre: '06_jiron_desde_norte', pos: P(A, tAB, -36, fueraAB, 6.5, 2.0), obj: P(B, tAB, 10, fueraAB, 4.0, 1.5), fov: 50 },
  { nombre: '07_cenital', pos: [cx + 0.01, 120, cz + 0.01], obj: [cx, 0, cz], fov: 50 },
  { nombre: '08_cenital_pueblo', pos: [cx + 0.01, 520, cz + 0.01], obj: [cx, 0, cz], fov: 50 },
  { nombre: '09_interior_a_esquina', pos: [cx + 6, 1.65, cz + 4], obj: P(A, fueraAB, 6, fueraDA, 6, 2.5), fov: 60 },
  { nombre: '10_interior_a_fondo', pos: [cx - 6, 1.65, cz - 3], obj: [D[0] + 8, 2.5, D[1] + 6], fov: 60 },
  { nombre: '11_lateral', pos: P(D, tAD, 30, fueraDA, 4.5, 1.7), obj: P(A, fueraDA, 3, tAD, 0, 1.8), fov: 50 },
  { nombre: '12_valle_lejano', pos: [cx - 160, 95, cz + 170], obj: [cx, 10, cz], fov: 45 },
  { nombre: '13_lindero_BC', pos: [cx + 10, 22, cz + 40], obj: [cx, 2, cz], fov: 45 },
];

for (const v of vistas) {
  if (filtro && !filtro.test(v.nombre)) continue;
  const t0 = Date.now();
  await page.evaluate(`window.APP.vista(${JSON.stringify(v.pos)}, ${JSON.stringify(v.obj)}, ${v.fov || 40})`);
  await page.screenshot({ path: path.join(SALIDA, `${v.nombre}.png`) });
  console.log(v.nombre, Date.now() - t0, 'ms', JSON.stringify(await page.evaluate('({t: window.APP.renderer.info.render.triangles, c: window.APP.renderer.info.render.calls})')));
}
// Estadísticas solo del entorno (proyecto oculto)
await page.evaluate('window.APP.soloEntorno(true)');
await page.evaluate(`window.APP.vista([${cx - 48}, 42, ${cz + 46}], [${cx}, 0, ${cz}], 38)`);
console.log('info (solo entorno, vista aerea)', JSON.stringify(await page.evaluate('window.APP.info()')));
if (errores.length) console.log('ERRORES/AVISOS:\n' + errores.slice(0, 30).join('\n'));
await browser.close();
srv.close();
