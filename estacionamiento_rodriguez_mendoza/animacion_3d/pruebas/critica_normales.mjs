// Mide normales del cuerpo sobre el paso de rueda delantero (SUV) vs. la puerta (puerto 8781).
import { servir, abrir } from '../servidor.mjs';
const PUERTO = 8781;
const srv = await servir(PUERTO);
const { browser, page } = await abrir({ ancho: 400, alto: 300, modo: 'still', puerto: PUERTO, pagina: 'pruebas/critica_vehiculos.html' });
const r = await page.evaluate(`(() => {
  const out = {};
  for (const [tipo, ej] of [['suv', 1.40], ['sedan', 1.36], ['pickup', 1.72]]) {
    window.APP.escena('solo', { tipo, color: '#ebebe7', seed: 1 });
    const v = window.APP.vehiculos[0].v;
    const m = v.children[0];
    const P = m.geometry.attributes.position, N = m.geometry.attributes.normal;
    const zona = (x0, x1, y0, y1) => {
      let ny = 0, nz = 0, c = 0, minNy = 1;
      for (let i = 0; i < P.count; i++) {
        const x = P.getX(i), y = P.getY(i), z = P.getZ(i);
        if (z > 0.6 && x > x0 && x < x1 && y > y0 && y < y1 && N.getZ(i) > 0.3) { ny += N.getY(i); nz += N.getZ(i); c++; minNy = Math.min(minNy, N.getY(i)); }
      }
      return { n: c, nyMedio: +(ny / c).toFixed(3), nzMedio: +(nz / c).toFixed(3), nyMin: +minNy.toFixed(3) };
    };
    out[tipo] = { sobreArco: zona(ej - 0.45, ej + 0.45, 0.70, 0.95), puerta: zona(0.0, 0.6, 0.55, 0.85) };
  }
  return out;
})()`);
console.log(JSON.stringify(r, null, 1));
await browser.close(); srv.close();
