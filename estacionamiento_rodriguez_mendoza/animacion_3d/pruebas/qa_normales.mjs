// QA de normales de vehiculos.js (puerto 8771): panel lateral sobre los pasos de rueda vs. la puerta.
//   cd animacion_3d && node pruebas/qa_normales.mjs
// Clasifica triángulos: "costado" = todos sus vértices por encima del redondeo inferior de su sección
// (y >= yMinSeccion + rb). Así se mide el panel y no el labio del arco (que legítimamente mira hacia abajo).
// También reporta la métrica del revisor (critica_normales.mjs) para comparar.
import { servir, abrir } from '../servidor.mjs';

const PUERTO = 8771;
const srv = await servir(PUERTO);
const { browser, page, errores } = await abrir({ ancho: 320, alto: 200, modo: 'still', puerto: PUERTO, pagina: 'pruebas/vehiculos.html' });
const r = await page.evaluate(`(async () => {
  const V = await import('../vehiculos.js');
  // [ejes, rb, techo de la zona (bajo el hombro)]
  const CASOS = { sedan: [[1.36, -1.25], 0.06, 0.80], hatchback: [[1.20, -1.30], 0.06, 0.80], suv: [[1.40, -1.29], 0.07, 1.0],
    pickup: [[1.72, -1.365], 0.07, 1.06], van: [[1.70, -1.41], 0.06, 0.98] };
  const out = {};
  for (const [tipo, [ejes, rb, yTop]] of Object.entries(CASOS)) {
    const g = V.crearVehiculo(tipo, { color: '#ebebe7', seed: 1 });
    const m = g.children[0];
    const P = m.geometry.attributes.position, N = m.geometry.attributes.normal;
    // y mínima por sección (x redondeado), solo lado +z
    const ymin = new Map();
    const kx = (x) => Math.round(x * 1e4);
    for (let i = 0; i < P.count; i++) {
      if (P.getZ(i) < 0.3) continue;
      const k = kx(P.getX(i));
      ymin.set(k, Math.min(ymin.get(k) ?? 9, P.getY(i)));
    }
    const zona = (x0, x1, y0, y1) => {
      let ny = 0, c = 0, mn = 1, mx = -1, dmn = null;
      for (let t = 0; t < P.count; t += 3) {
        let ok = true, cy = 0, cx = 0, cz = 0;
        for (let j = 0; j < 3; j++) {
          const i = t + j, y = P.getY(i);
          const ym = ymin.get(kx(P.getX(i)));
          if (ym === undefined || y < ym + rb - 0.002) ok = false;
          cx += P.getX(i) / 3; cy += y / 3; cz += P.getZ(i) / 3;
        }
        if (!ok || cz < 0.6 || cx < x0 || cx > x1 || cy < y0 || cy > y1) continue;
        for (let j = 0; j < 3; j++) {
          if (N.getZ(t + j) < 0.3) continue;
          const v = N.getY(t + j); ny += v; c++; mx = Math.max(mx, v);
          if (v < mn) { mn = v; dmn = [P.getX(t + j), P.getY(t + j), P.getZ(t + j)].map((a) => +a.toFixed(3)); }
        }
      }
      return { n: c, nyMedio: +(ny / Math.max(1, c)).toFixed(3), nyMin: +mn.toFixed(3), nyMax: +mx.toFixed(3), en: dmn };
    };
    // métrica del revisor (incluye el labio del arco)
    const rev = (x0, x1, y0, y1) => {
      let ny = 0, c = 0, mn = 1;
      for (let i = 0; i < P.count; i++) {
        const x = P.getX(i), y = P.getY(i), z = P.getZ(i);
        if (z > 0.6 && x > x0 && x < x1 && y > y0 && y < y1 && N.getZ(i) > 0.3) { ny += N.getY(i); c++; mn = Math.min(mn, N.getY(i)); }
      }
      return { n: c, nyMedio: +(ny / c).toFixed(3), nyMin: +mn.toFixed(3) };
    };
    const ej = ejes[0], et = ejes[1];
    out[tipo] = {
      arcoDel: zona(ej - 0.45, ej + 0.45, 0.45, yTop),
      arcoTras: zona(et - 0.45, et + 0.45, 0.45, yTop),
      puerta: zona(-0.3, 0.6, 0.45, yTop),
      revisorArco: rev(ej - 0.45, ej + 0.45, 0.70, 0.95),
      revisorPuerta: rev(0.0, 0.6, 0.55, 0.85),
    };
  }
  return out;
})()`);
for (const [t, v] of Object.entries(r)) {
  console.log(t);
  for (const [k, z] of Object.entries(v)) console.log('   ', k.padEnd(14), JSON.stringify(z));
}
if (errores.length) console.log('ERRORES/AVISOS:\n' + errores.slice(0, 20).join('\n'));
await browser.close();
srv.close();
