// Perfil de triángulos del cuerpo por estación del loft (puerto 8771).
//   cd animacion_3d && node pruebas/qa_perfil_tris.mjs [tipo]
import { servir, abrir } from '../servidor.mjs';
const TIPO = process.argv[2] || 'van';
const srv = await servir(8771);
const { browser, page } = await abrir({ ancho: 200, alto: 120, modo: 'still', puerto: 8771, pagina: 'pruebas/vehiculos.html' });
const r = await page.evaluate(`(async () => {
  const V = await import('../vehiculos.js');
  const g = V.crearVehiculo('${TIPO}', { color: '#ebebe7', seed: 1, sombra: false });
  const m = g.children[0], P = m.geometry.attributes.position;
  const xs = new Set();
  for (let i = 0; i < P.count; i++) if (Math.abs(P.getZ(i)) > 0.3) xs.add(+P.getX(i).toFixed(3));
  const est = [...xs].sort((a, b) => a - b);
  // triángulos cuyo x min y x max están entre estaciones consecutivas
  const cnt = new Map();
  let total = P.count / 3;
  for (let t = 0; t < P.count; t += 3) {
    const a = [P.getX(t), P.getX(t + 1), P.getX(t + 2)];
    const k = Math.min(...a).toFixed(3) + '..' + Math.max(...a).toFixed(3);
    cnt.set(k, (cnt.get(k) || 0) + 1);
  }
  const top = [...cnt.entries()].sort((a, b) => b[1] - a[1]).slice(0, 40);
  return { total, nEst: est.length, est, top };
})()`);
console.log('total', r.total, 'estaciones', r.nEst);
console.log(r.est.join(' '));
for (const [k, n] of r.top) console.log(k.padEnd(16), n);
await browser.close(); srv.close();
